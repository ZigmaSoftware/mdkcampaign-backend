"""
Serializers for opinion polls
"""
from django.conf import settings
from rest_framework import serializers
from .models import Poll, PollOption, PollVote


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
        is_admin = (
            request and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'admin'
        )
        if not is_admin:
            return None
        counts = self.context.get('vote_counts', {})
        q_key = 'q1' if obj.question_no == 1 else 'q2'
        return counts.get(q_key, {}).get(obj.id, 0)

    def get_is_winner(self, obj):
        """Only admin users can see who is winning"""
        request = self.context.get('request')
        if request and request.user.is_authenticated and getattr(request.user, 'role', None) == 'admin':
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
        counts = obj.vote_counts()
        serializer = PollOptionSerializer(
            obj.options.all(), many=True,
            context={**self.context, 'vote_counts': counts},
        )
        return serializer.data

    def get_total_votes(self, obj):
        return obj.vote_counts()['total']

    def _get_vote(self, obj):
        """Return the user's vote. When device_id is present, only check device — don't fall back to IP."""
        device_id = (self.context.get('device_id') or '').strip()
        if device_id:
            # device_id is the source of truth — if this device hasn't voted, return None
            return PollVote.objects.filter(poll=obj, voter_device_id=device_id).first()
        request = self.context.get('request')
        if not request:
            return None
        if request.user.is_authenticated:
            return PollVote.objects.filter(poll=obj, voter_user=request.user).first()
        ip = self._voter_ip()
        if not ip:
            return None
        return PollVote.objects.filter(poll=obj, voter_ip=ip).first()

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
