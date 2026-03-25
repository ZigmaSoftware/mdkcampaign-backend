"""
Views for opinion polls
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from .models import Poll, PollOption, PollVote
from .serializers import PollDetailSerializer, CastVoteSerializer, PollOptionSerializer


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class PollViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Poll.objects.filter(is_active=True)
    serializer_class = PollDetailSerializer
    permission_classes = [AllowAny]

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
        serializer = self.get_serializer(poll)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'], url_path='vote', permission_classes=[AllowAny])
    def vote(self, request, pk=None):
        """Cast a vote on a poll"""
        poll = self.get_object()
        if not poll.is_active:
            return Response({'detail': 'This poll is no longer active'}, status=status.HTTP_400_BAD_REQUEST)

        voter_ip = get_client_ip(request)

        # Deduplicate by user when authenticated, by IP when anonymous
        if request.user.is_authenticated:
            if PollVote.objects.filter(poll=poll, voter_user=request.user).exists():
                return Response({'detail': 'already_voted', 'message': 'You have already voted on this poll'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if PollVote.objects.filter(poll=poll, voter_ip=voter_ip).exists():
                return Response({'detail': 'already_voted', 'message': 'You have already voted on this poll'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CastVoteSerializer(data=request.data, context={'poll': poll, 'request': request})
        serializer.is_valid(raise_exception=True)

        PollVote.objects.create(
            poll=poll,
            voter_ip=voter_ip,
            voter_user=request.user if request.user.is_authenticated else None,
            voter_name=serializer.validated_data.get('voter_name', ''),
            voter_phone=serializer.validated_data.get('voter_phone', ''),
            voter_city=serializer.validated_data.get('voter_city', ''),
            q1_option_id=serializer.validated_data['q1_option'],
            q2_option_id=serializer.validated_data.get('q2_option'),
        )

        updated = PollDetailSerializer(poll, context={'request': request}).data
        return Response(updated, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['GET'], url_path='votes', permission_classes=[IsAuthenticated])
    def votes_list(self, request, pk=None):
        """Admin-only: list all individual votes for this poll"""
        if getattr(request.user, 'role', None) != 'admin':
            return Response({'detail': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        poll = self.get_object()
        votes = PollVote.objects.filter(poll=poll).select_related(
            'voter_user', 'q1_option', 'q2_option'
        ).order_by('-created_at')
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

        if request.user.is_authenticated:
            vote = PollVote.objects.filter(poll=poll, voter_user=request.user).first()
        else:
            vote = PollVote.objects.filter(poll=poll, voter_ip=voter_ip).first()

        if not vote:
            return Response({'detail': 'No vote found to update'}, status=status.HTTP_404_NOT_FOUND)

        q2_id = request.data.get('q2_option')
        if q2_id and poll.options.filter(id=q2_id, question_no=2).exists():
            vote.q2_option_id = q2_id
            vote.save(update_fields=['q2_option'])

        updated = PollDetailSerializer(poll, context={'request': request}).data
        return Response(updated)
