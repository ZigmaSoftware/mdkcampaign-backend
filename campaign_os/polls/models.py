"""
Opinion poll models
"""
import secrets
from django.db import models
from django.db.models import Count
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

    def vote_counts(self):
        """Returns dict: {option_id: count} for Q1 and Q2 separately"""
        q1 = (PollVote.objects.filter(poll=self, q1_option__isnull=False)
              .values('q1_option').annotate(cnt=Count('id')))
        q2 = (PollVote.objects.filter(poll=self, q2_option__isnull=False)
              .values('q2_option').annotate(cnt=Count('id')))
        return {
            'q1': {row['q1_option']: row['cnt'] for row in q1},
            'q2': {row['q2_option']: row['cnt'] for row in q2},
            'total': PollVote.objects.filter(poll=self).count(),
        }


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
