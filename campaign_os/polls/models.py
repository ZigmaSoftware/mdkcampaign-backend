"""
Opinion poll models
"""
import secrets
from django.db import models
from django.db.models import Count
from django.utils import timezone
from campaign_os.core.models import BaseModel


def _make_token():
    """16-char URL-safe token (96 bits entropy — not guessable)."""
    return secrets.token_urlsafe(12)


class Poll(BaseModel):
    """An opinion poll for a constituency"""
    # Override BaseModel FK related_names to avoid clash with elections.Poll
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.PROTECT,
        related_name='opinionpoll_created', null=True, blank=True,
        db_constraint=False
    )
    updated_by = models.ForeignKey(
        'accounts.User', on_delete=models.PROTECT,
        related_name='opinionpoll_updated', null=True, blank=True,
        db_constraint=False
    )

    title        = models.CharField(max_length=200)
    title_ta     = models.CharField(max_length=200, blank=True)
    constituency_name = models.CharField(max_length=200, blank=True)
    constituency_no   = models.IntegerField(null=True, blank=True)
    is_active    = models.BooleanField(default=True, db_index=True)
    starts_at    = models.DateTimeField(null=True, blank=True)
    ends_at      = models.DateTimeField(null=True, blank=True)
    short_token  = models.CharField(max_length=32, unique=True, default=_make_token, db_index=True)
    share_url    = models.CharField(max_length=300, blank=True)   # populated by is.gd auto-shortener

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def resolve_reset_window(self, reset_id=None, now=None):
        """
        Resolve a vote counting window for this poll.

        - If reset_id is provided, use that reset's window.
        - Otherwise use the latest reset with starts_at <= now (current window).
        - If no reset matches, return all-time window (None, None, None).
        """
        now = now or timezone.now()
        resets = self.resets.filter(is_active=True).order_by('starts_at', 'id')

        selected = None
        if reset_id is not None and str(reset_id).strip() != '':
            try:
                reset_pk = int(reset_id)
            except (TypeError, ValueError):
                reset_pk = None
            if reset_pk:
                selected = resets.filter(id=reset_pk).first()
                if not selected:
                    return None, None, None

        if selected is None:
            selected = resets.filter(starts_at__lte=now).order_by('-starts_at', '-id').first()
            if not selected:
                return None, None, None

        next_reset = resets.filter(starts_at__gt=selected.starts_at).order_by('starts_at', 'id').first()
        return selected, selected.starts_at, (next_reset.starts_at if next_reset else None)

    def resolve_session_window(self, session_key=None, now=None):
        """
        Resolve a named poll session window.

        Session model:
        - Poll 1  => "base" window (before first reset, or all-time if no resets)
        - Poll N>1 => window that starts at reset id <session_key>
        - Latest/current window is used when session_key is empty/'latest'/'current'
        """
        now = now or timezone.now()
        resets = self.resets.filter(is_active=True).order_by('starts_at', 'id')
        key = str(session_key or '').strip().lower()

        # Default: latest/current session
        if key in {'', 'latest', 'current'}:
            current_reset = resets.filter(starts_at__lte=now).order_by('-starts_at', '-id').first()
            if not current_reset:
                return 'base', None, None
            return str(current_reset.id), current_reset.starts_at, None

        # Base session (before first reset)
        if key == 'base':
            first_reset = resets.first()
            return 'base', None, (first_reset.starts_at if first_reset else None)

        # Session keyed by reset id
        try:
            reset_pk = int(key)
        except (TypeError, ValueError):
            return None, None, None

        selected = resets.filter(id=reset_pk).first()
        if not selected:
            return None, None, None
        next_reset = resets.filter(starts_at__gt=selected.starts_at).order_by('starts_at', 'id').first()
        return str(selected.id), selected.starts_at, (next_reset.starts_at if next_reset else None)

    def vote_counts(self, start_at=None, end_at=None):
        """Return Q1/Q2/total counts for a given vote window."""
        votes = PollVote.objects.filter(poll=self)
        if start_at:
            votes = votes.filter(voted_at__gte=start_at)
        if end_at:
            votes = votes.filter(voted_at__lt=end_at)

        q1 = votes.filter(q1_option__isnull=False).values('q1_option').annotate(cnt=Count('id'))
        q2 = votes.filter(q2_option__isnull=False).values('q2_option').annotate(cnt=Count('id'))
        return {
            'q1': {row['q1_option']: row['cnt'] for row in q1},
            'q2': {row['q2_option']: row['cnt'] for row in q2},
            'total': votes.count(),
        }


class PollReset(BaseModel):
    """
    Date-wise reset marker.
    Votes are never deleted; each reset defines a new counting window.
    """
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='resets', db_constraint=False)
    starts_at = models.DateTimeField(db_index=True)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-starts_at', '-created_at']
        indexes = [
            models.Index(fields=['poll', 'starts_at']),
        ]

    def __str__(self):
        return f"{self.poll.title} reset @ {self.starts_at}"


class PollOption(BaseModel):
    """An option within a poll question (Q1=alliance, Q2=candidate)"""
    QUESTION_CHOICES = [(1, 'Question 1 - Alliance'), (2, 'Question 2 - Candidate')]

    poll          = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options', db_constraint=False)
    question_no   = models.IntegerField(choices=QUESTION_CHOICES, default=1)
    key           = models.CharField(max_length=50)   # 'bjp', 'inc', 'kirthika'
    name          = models.CharField(max_length=200)
    name_ta       = models.CharField(max_length=200, blank=True)
    sub_label     = models.CharField(max_length=200, blank=True)  # party/candidate info
    icon_bg       = models.CharField(max_length=200, blank=True)  # CSS gradient
    bar_color     = models.CharField(max_length=20, blank=True)   # hex color
    is_winner     = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['question_no', 'display_order']
        unique_together = ['poll', 'question_no', 'key']

    def __str__(self):
        return f"{self.poll.title} — Q{self.question_no}: {self.name}"


class PollVote(models.Model):
    """One vote cast by a voter (deduplicated by user when authenticated, by IP when anonymous)"""
    poll        = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes', db_constraint=False)
    voter_ip        = models.GenericIPAddressField(null=True, blank=True)
    voter_device_id = models.CharField(max_length=64, blank=True, db_index=True)
    voter_user  = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='poll_votes',
        db_constraint=False
    )
    voter_name  = models.CharField(max_length=200, blank=True)
    voter_phone = models.CharField(max_length=20, blank=True)
    voter_city  = models.CharField(max_length=100, blank=True)
    q1_option   = models.ForeignKey(PollOption, on_delete=models.SET_NULL, null=True, blank=True, related_name='q1_votes', db_constraint=False)
    q2_option   = models.ForeignKey(PollOption, on_delete=models.SET_NULL, null=True, blank=True, related_name='q2_votes', db_constraint=False)
    voted_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        pass  # deduplication enforced in the view (device_id → user → IP)

    def __str__(self):
        identifier = self.voter_user.username if self.voter_user else self.voter_ip
        return f"Vote by {identifier} on {self.poll.title}"
