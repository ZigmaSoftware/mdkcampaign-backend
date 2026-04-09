"""
Views for opinion polls
"""
import urllib.request
import urllib.parse
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Poll, PollVote, PollReset
from .serializers import (
    PollDetailSerializer,
    CastVoteSerializer,
    PollResetSerializer,
    CreatePollResetSerializer,
)


def _make_short_url(long_url: str) -> str | None:
    """Shorten a URL via TinyURL. Returns short URL or None on failure."""
    try:
        api = 'https://tinyurl.com/api-create.php?url=' + urllib.parse.quote(long_url, safe='')
        with urllib.request.urlopen(api, timeout=6) as resp:
            result = resp.read().decode().strip()
        if result.startswith('https://tinyurl.com/') or result.startswith('http://tinyurl.com/'):
            return result
    except Exception:
        pass
    return None


def poll_short_redirect(request, token):
    """Public short URL: /p/<token>/ → frontend poll page (no auth required)."""
    poll = Poll.objects.filter(short_token=token, is_active=True).first()
    if not poll:
        return HttpResponseNotFound('Poll not found or no longer active.')
    # Derive frontend URL from request host — same host, port 8973
    host = request.get_host().split(':')[0]   # strip port if present
    frontend_url = getattr(settings, 'FRONTEND_URL', f'http://{host}:8973')
    return HttpResponseRedirect(f'{frontend_url}/#poll')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class PollViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Poll.objects.filter(is_active=True)
    serializer_class = PollDetailSerializer
    permission_classes = [AllowAny]

    def _can_view_poll_management(self, request):
        if not request.user.is_authenticated:
            return False
        username = (getattr(request.user, 'username', '') or '').strip().lower()
        return getattr(request.user, 'role', None) == 'admin' or username == 'poll'

    def _can_create_poll_session(self, request):
        if not request.user.is_authenticated:
            return False
        username = (getattr(request.user, 'username', '') or '').strip().lower()
        return username == 'poll'

    def _windowed_votes(self, poll, start_at=None, end_at=None):
        votes = PollVote.objects.filter(poll=poll)
        if start_at:
            votes = votes.filter(voted_at__gte=start_at)
        if end_at:
            votes = votes.filter(voted_at__lt=end_at)
        return votes

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    @action(detail=False, methods=['GET'], url_path='active')
    def active(self, request):
        """Get the current active poll"""
        poll = Poll.objects.filter(is_active=True).first()
        if not poll:
            return Response({'detail': 'No active poll found'}, status=status.HTTP_404_NOT_FOUND)

        # Auto-shorten via TinyURL on first access — use the request's actual host
        if not poll.share_url:
            base = request.build_absolute_uri('/').rstrip('/')
            local_url = f'{base}/p/{poll.short_token}/'
            shortened = _make_short_url(local_url)
            if shortened:
                poll.share_url = shortened
                poll.save(update_fields=['share_url'])

        session_key = request.query_params.get('session') or request.query_params.get('reset_id')
        selected_session_key = None
        start_at = None
        end_at = None
        if session_key and self._can_view_poll_management(request):
            selected_session_key, start_at, end_at = poll.resolve_session_window(session_key=session_key)
            if selected_session_key is None:
                return Response({'detail': 'Invalid session'}, status=status.HTTP_404_NOT_FOUND)
        else:
            selected_session_key, start_at, end_at = poll.resolve_session_window()

        ctx = self.get_serializer_context()
        ctx['device_id'] = request.query_params.get('device_id', '')
        ctx['poll_reset_start'] = start_at
        ctx['poll_reset_end'] = end_at
        ctx['poll_session_key'] = selected_session_key
        serializer = PollDetailSerializer(poll, context=ctx)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'], url_path='vote', permission_classes=[AllowAny])
    def vote(self, request, pk=None):
        """Cast a vote on a poll"""
        poll = self.get_object()
        if not poll.is_active:
            return Response({'detail': 'This poll is no longer active'}, status=status.HTTP_400_BAD_REQUEST)

        voter_ip    = get_client_ip(request)
        device_id   = (request.data.get('device_id') or '').strip()[:64]
        _, start_at, end_at = poll.resolve_session_window()
        window_votes = self._windowed_votes(poll, start_at=start_at, end_at=end_at)

        # Deduplicate: device_id (highest priority) → user → IP
        if device_id and window_votes.filter(voter_device_id=device_id).exists():
            return Response({'detail': 'already_voted', 'message': 'Already voted from this device'}, status=status.HTTP_400_BAD_REQUEST)
        if request.user.is_authenticated and window_votes.filter(voter_user=request.user).exists():
            return Response({'detail': 'already_voted', 'message': 'You have already voted on this poll'}, status=status.HTTP_400_BAD_REQUEST)
        if not device_id and window_votes.filter(voter_ip=voter_ip).exists():
            return Response({'detail': 'already_voted', 'message': 'You have already voted on this poll'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CastVoteSerializer(data=request.data, context={'poll': poll, 'request': request})
        serializer.is_valid(raise_exception=True)

        PollVote.objects.create(
            poll=poll,
            voter_ip=voter_ip,
            voter_device_id=device_id,
            voter_user=request.user if request.user.is_authenticated else None,
            voter_name=serializer.validated_data.get('voter_name', ''),
            voter_phone=serializer.validated_data.get('voter_phone', ''),
            voter_city=serializer.validated_data.get('voter_city', ''),
            q1_option_id=serializer.validated_data['q1_option'],
            q2_option_id=serializer.validated_data.get('q2_option'),
        )

        ctx = self.get_serializer_context()
        ctx['device_id'] = device_id
        ctx['poll_reset_start'] = start_at
        ctx['poll_reset_end'] = end_at
        updated = PollDetailSerializer(poll, context=ctx).data
        return Response(updated, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['GET'], url_path='votes', permission_classes=[IsAuthenticated])
    def votes_list(self, request, pk=None):
        """Admin-only: list all individual votes for this poll"""
        if not self._can_view_poll_management(request):
            return Response({'detail': 'Poll management access required'}, status=status.HTTP_403_FORBIDDEN)
        poll = self.get_object()
        session_key = request.query_params.get('session') or request.query_params.get('reset_id')
        selected_session_key = None
        start_at = None
        end_at = None
        if session_key and session_key == 'all':
            start_at = None
            end_at = None
        elif session_key:
            selected_session_key, start_at, end_at = poll.resolve_session_window(session_key=session_key)
            if selected_session_key is None:
                return Response({'detail': 'Invalid session'}, status=status.HTTP_404_NOT_FOUND)
        else:
            selected_session_key, start_at, end_at = poll.resolve_session_window()

        votes = self._windowed_votes(poll, start_at=start_at, end_at=end_at).select_related(
            'voter_user', 'q1_option', 'q2_option'
        ).order_by('-voted_at')
        data = [{
            'id':          v.id,
            'username':    v.voter_user.username if v.voter_user else (v.voter_name or '—'),
            'voter_ip':    v.voter_ip or '—',
            'voter_name':  v.voter_name or '—',
            'voter_phone': v.voter_phone or '—',
            'voter_city':  v.voter_city or '—',
            'q1_option':   v.q1_option.name if v.q1_option else '—',
            'q1_key':      v.q1_option.key  if v.q1_option else '',
            'q2_option':   v.q2_option.name if v.q2_option else '—',
            'q2_key':      v.q2_option.key  if v.q2_option else '',
            'timestamp':   v.voted_at,
        } for v in votes]
        return Response(data)

    @action(detail=True, methods=['PATCH'], url_path='update_vote', permission_classes=[AllowAny])
    def update_vote(self, request, pk=None):
        """Update q2_option on an existing vote (after Q1 already submitted)"""
        poll = self.get_object()
        voter_ip = get_client_ip(request)
        _, start_at, end_at = poll.resolve_session_window()
        window_votes = self._windowed_votes(poll, start_at=start_at, end_at=end_at)

        device_id = (request.data.get('device_id') or '').strip()[:64]
        if device_id:
            vote = window_votes.filter(voter_device_id=device_id).first()
        elif request.user.is_authenticated:
            vote = window_votes.filter(voter_user=request.user).first()
        else:
            vote = window_votes.filter(voter_ip=voter_ip).first()

        if not vote:
            return Response({'detail': 'No vote found to update'}, status=status.HTTP_404_NOT_FOUND)

        q2_id = request.data.get('q2_option')
        if q2_id and poll.options.filter(id=q2_id, question_no=2).exists():
            vote.q2_option_id = q2_id
            vote.save(update_fields=['q2_option'])

        ctx = self.get_serializer_context()
        ctx['device_id'] = device_id
        ctx['poll_reset_start'] = start_at
        ctx['poll_reset_end'] = end_at
        updated = PollDetailSerializer(poll, context=ctx).data
        return Response(updated)

    @action(detail=True, methods=['GET', 'POST'], url_path='resets', permission_classes=[IsAuthenticated])
    def resets(self, request, pk=None):
        """Admin-only: manage reset windows for poll counting."""
        if request.method == 'POST':
            if not self._can_create_poll_session(request):
                return Response({'detail': 'Only poll session manager can create sessions'}, status=status.HTTP_403_FORBIDDEN)
        else:
            if not self._can_view_poll_management(request):
                return Response({'detail': 'Poll management access required'}, status=status.HTTP_403_FORBIDDEN)

        poll = self.get_object()

        if request.method == 'POST':
            serializer = CreatePollResetSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            starts_at = timezone.now()
            note = serializer.validated_data.get('note', '')
            reset = PollReset.objects.create(
                poll=poll,
                starts_at=starts_at,
                note=note,
                created_by=request.user,
                updated_by=request.user,
            )
            data = PollResetSerializer(reset, context={'poll': poll}).data
            return Response(data, status=status.HTTP_201_CREATED)

        resets = poll.resets.filter(is_active=True).order_by('-starts_at', '-id')
        data = PollResetSerializer(resets, many=True, context={'poll': poll}).data
        return Response(data)
