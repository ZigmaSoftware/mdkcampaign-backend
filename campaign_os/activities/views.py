from rest_framework import viewsets, permissions
from .models import ActivityLog, FieldSurvey
from .serializers import ActivityLogSerializer, FieldSurveySerializer
from campaign_os.core.permissions import ScreenPermission


def _sync_voter_from_survey(instance):
    """Push support_level → voter.sentiment and party_preference → voter.preferred_party."""
    voter = instance.voter
    if not voter:
        return

    changed = False

    if instance.support_level:
        voter.sentiment = instance.support_level   # values match: positive/negative/neutral
        changed = True

    if instance.party_preference:
        from campaign_os.masters.models import Party
        party = Party.objects.filter(
            is_active=True
        ).filter(
            name__iexact=instance.party_preference
        ).first()
        if party:
            voter.preferred_party = party
            changed = True

    if changed:
        fields_to_save = []
        if instance.support_level:
            fields_to_save.append('sentiment')
        if instance.party_preference:
            fields_to_save.append('preferred_party_id')
        voter.save(update_fields=fields_to_save)


class ActivityLogViewSet(viewsets.ModelViewSet):
    screen_slug = 'agent-activity'
    queryset = ActivityLog.objects.filter(is_active=True)
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['category', 'date', 'username']

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            username=serializer.validated_data.get('username') or self.request.user.username,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class FieldSurveyViewSet(viewsets.ModelViewSet):
    screen_slug = 'voter-survey'
    queryset = FieldSurvey.objects.filter(is_active=True)
    serializer_class = FieldSurveySerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['survey_date', 'block', 'support_level', 'surveyed_by']

    def perform_create(self, serializer):
        instance = serializer.save(
            created_by=self.request.user,
            surveyed_by=serializer.validated_data.get('surveyed_by') or self.request.user.username,
        )
        _sync_voter_from_survey(instance)

    def perform_update(self, serializer):
        instance = serializer.save(updated_by=self.request.user)
        _sync_voter_from_survey(instance)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
