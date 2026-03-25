"""
Views for elections and polls
"""
from rest_framework import viewsets, permissions
from campaign_os.elections.models import Election, Poll, PollQuestion, PollResponse
from rest_framework.decorators import action
from rest_framework.response import Response


class ElectionViewSet(viewsets.ReadOnlyModelViewSet):
    """Election management"""
    queryset = Election.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['state', 'election_type', 'status']
    search_fields = ['name']
    
    @action(detail=True, methods=['GET'])
    def polls(self, request, pk=None):
        """Get all polls for this election"""
        election = self.get_object()
        polls = election.polls.all()
        from campaign_os.volunteers.serializers import PollSerializer
        serializer = PollSerializer(polls, many=True)
        return Response(serializer.data)


class PollViewSet(viewsets.ModelViewSet):
    """Opinion poll management"""
    queryset = Poll.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['election', 'constituency']
    search_fields = ['name']
    
    @action(detail=True, methods=['GET'])
    def questions(self, request, pk=None):
        """Get all questions in this poll"""
        poll = self.get_object()
        questions = poll.questions.all()
        from campaign_os.volunteers.serializers import PollSerializer
        serializer = PollSerializer(questions, many=True)
        return Response(serializer.data)


class PollQuestionViewSet(viewsets.ModelViewSet):
    """Poll question management"""
    queryset = PollQuestion.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['poll']


class PollResponseViewSet(viewsets.ModelViewSet):
    """Poll response tracking"""
    queryset = PollResponse.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['poll', 'voter']
