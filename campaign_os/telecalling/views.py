from rest_framework import viewsets, permissions
from .models import TelecallingAssignment, TelecallingFeedback
from .serializers import TelecallingAssignmentSerializer, TelecallingFeedbackSerializer


class TelecallingAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TelecallingAssignment.objects.filter(is_active=True).prefetch_related('voters')
    serializer_class = TelecallingAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['assigned_date', 'telecaller_id']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class TelecallingFeedbackViewSet(viewsets.ModelViewSet):
    queryset = TelecallingFeedback.objects.filter(is_active=True)
    serializer_class = TelecallingFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['action', 'survey']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
