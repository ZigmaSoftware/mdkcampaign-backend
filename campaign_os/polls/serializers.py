"""
Serializers for opinion polls
"""
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from .models import Poll, PollOption, PollVote, PollReset


def _can_view_poll_management(request):
    if not request or not request.user.is_authenticated:
        return False
    username = (getattr(request.user, 'username', '') or '').strip().lower()
    return getattr(request.user, 'role', None) == 'admin' or username == 'poll'


class PollOptionSerializer(serializers.ModelSerializer):
    vote_count = serializers.SerializerMethodField()
    is_winner  = serializers.SerializerMethodField()

    class Meta:
        model = PollOption
        fields = [
            'id', 'question_no', 'key', 'name', 'name_ta', 'sub_label',
            'icon_bg', 'bar_color', 'is_winner', 'display_order', 'vote_count',
        ]

    def get_vote_count(self, obj):
        request = self.context.get('request')
        if not _can_view_poll_management(request):
            return None
        counts = self.context.get('vote_counts', {})
        q_key = 'q1' if obj.question_no == 1 else 'q2'
        return counts.get(q_key, {}).get(obj.id, 0)

    def get_is_winner(self, obj):
        """Only admin users can see who is winning"""
        request = self.context.get('request')
        if _can_view_poll_management(request):
            return obj.is_winner
        return None


class PollDetailSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()
    total_votes = serializers.SerializerMethodField()
    user_has_voted = serializers.SerializerMethodField()
    user_q1_option = serializers.SerializerMethodField()
    user_q2_option = serializers.SerializerMethodField()
    short_url = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = [
            'id', 'title', 'title_ta', 'constituency_name', 'constituency_no',
            'is_active', 'starts_at', 'ends_at',
            'options', 'total_votes', 'user_has_voted', 'user_q1_option', 'user_q2_option',
            'short_url',
        ]

    def get_short_url(self, obj):
        # Prefer pre-generated is.gd URL; fall back to local short URL
        if obj.share_url:
            return obj.share_url
        base = getattr(settings, 'BACKEND_BASE_URL', None)
        if not base:
            request = self.context.get('request')
            base = request.build_absolute_uri('/').rstrip('/') if request else 'http://localhost:7904'
        return f'{base}/p/{obj.short_token}/'

    def _voter_ip(self):
        request = self.context.get('request')
        if not request:
            return None
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def get_options(self, obj):
        start_at = self.context.get('poll_reset_start')
        end_at = self.context.get('poll_reset_end')
        counts = obj.vote_counts(start_at=start_at, end_at=end_at)
        serializer = PollOptionSerializer(
            obj.options.all(), many=True,
            context={**self.context, 'vote_counts': counts},
        )
        return serializer.data

    def get_total_votes(self, obj):
        start_at = self.context.get('poll_reset_start')
        end_at = self.context.get('poll_reset_end')
        return obj.vote_counts(start_at=start_at, end_at=end_at)['total']

    def _get_vote(self, obj):
        """Return the user's vote. When device_id is present, only check device — don't fall back to IP."""
        start_at = self.context.get('poll_reset_start')
        end_at = self.context.get('poll_reset_end')
        votes = PollVote.objects.filter(poll=obj)
        if start_at:
            votes = votes.filter(voted_at__gte=start_at)
        if end_at:
            votes = votes.filter(voted_at__lt=end_at)

        device_id = (self.context.get('device_id') or '').strip()
        if device_id:
            # device_id is the source of truth — if this device hasn't voted, return None
            return votes.filter(voter_device_id=device_id).first()
        request = self.context.get('request')
        if not request:
            return None
        if request.user.is_authenticated:
            return votes.filter(voter_user=request.user).first()
        ip = self._voter_ip()
        if not ip:
            return None
        return votes.filter(voter_ip=ip).first()

    def get_user_has_voted(self, obj):
        return self._get_vote(obj) is not None

    def get_user_q1_option(self, obj):
        vote = self._get_vote(obj)
        return vote.q1_option_id if vote else None

    def get_user_q2_option(self, obj):
        vote = self._get_vote(obj)
        return vote.q2_option_id if vote else None


class CastVoteSerializer(serializers.Serializer):
    q1_option   = serializers.IntegerField()
    q2_option   = serializers.IntegerField(required=False, allow_null=True)
    voter_name  = serializers.CharField(max_length=200, required=False, allow_blank=True)
    voter_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    voter_city  = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate(self, attrs):
        poll = self.context['poll']
        q1 = attrs['q1_option']
        if not poll.options.filter(id=q1, question_no=1).exists():
            raise serializers.ValidationError({'q1_option': 'Invalid Q1 option for this poll'})
        q2 = attrs.get('q2_option')
        if q2 is not None and not poll.options.filter(id=q2, question_no=2).exists():
            raise serializers.ValidationError({'q2_option': 'Invalid Q2 option for this poll'})
        return attrs


class PollResetSerializer(serializers.ModelSerializer):
    ends_at = serializers.SerializerMethodField()
    is_current = serializers.SerializerMethodField()
    total_votes = serializers.SerializerMethodField()

    class Meta:
        model = PollReset
        fields = ['id', 'starts_at', 'ends_at', 'is_current', 'total_votes', 'note']

    def get_ends_at(self, obj):
        poll = self.context.get('poll') or obj.poll
        next_reset = poll.resets.filter(
            is_active=True, starts_at__gt=obj.starts_at
        ).order_by('starts_at', 'id').first()
        return next_reset.starts_at if next_reset else None

    def get_is_current(self, obj):
        now = timezone.now()
        poll = self.context.get('poll') or obj.poll
        current = poll.resets.filter(
            is_active=True, starts_at__lte=now
        ).order_by('-starts_at', '-id').first()
        return bool(current and current.id == obj.id)

    def get_total_votes(self, obj):
        poll = self.context.get('poll') or obj.poll
        next_reset = poll.resets.filter(
            is_active=True, starts_at__gt=obj.starts_at
        ).order_by('starts_at', 'id').first()
        counts = poll.vote_counts(
            start_at=obj.starts_at,
            end_at=(next_reset.starts_at if next_reset else None),
        )
        return counts['total']


class CreatePollResetSerializer(serializers.Serializer):
    starts_at = serializers.DateTimeField(required=False)
    note = serializers.CharField(required=False, allow_blank=True, max_length=200)
