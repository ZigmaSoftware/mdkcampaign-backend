import logging

from django.utils import timezone
from rest_framework import viewsets, permissions

from .models import ActivityLog, FieldSurvey
from .serializers import ActivityLogSerializer, FieldSurveySerializer
from campaign_os.core.permissions import (
    ScreenPermission,
    ACTION_TO_FLAG,
    resolve_user_permission_roles,
)
from campaign_os.telecalling.models import TelecallingFeedback


logger = logging.getLogger(__name__)


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


def _has_field_followup_marker(instance):
    return ActivityLog.objects.filter(
        is_active=True,
        category='field',
        notes__icontains=f"[survey_id:{instance.id}]",
    ).exists()


def _sync_field_followup_status(instance, user):
    """
    When a survey already belongs to the field-followup flow, closing the survey
    should also close the related feedback-review decision.
    """
    field_feedback = (
        TelecallingFeedback.objects
        .filter(is_active=True, survey=instance, followup_type='field_survey')
        .order_by('-date', '-created_at', '-id')
        .first()
    )
    latest_feedback = field_feedback or (
        TelecallingFeedback.objects
        .filter(is_active=True, survey=instance)
        .order_by('-date', '-created_at', '-id')
        .first()
    )

    if not field_feedback and not _has_field_followup_marker(instance):
        return

    today = timezone.localdate()

    if latest_feedback:
        latest_feedback.voter_name = instance.voter_name
        latest_feedback.action = 'followup_not_required'
        latest_feedback.followup_type = 'field_survey'
        latest_feedback.date = today
        latest_feedback.updated_by = user
        latest_feedback.save()
        return

    TelecallingFeedback.objects.create(
        survey=instance,
        voter_name=instance.voter_name,
        telecaller_name='',
        action='followup_not_required',
        followup_type='field_survey',
        date=today,
        created_by=user,
    )


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


class FieldSurveyPermission(ScreenPermission):
    """
    Field Survey records are reused by both Voter Survey and Field Survey screens.
    Allow edits from the field-activity screen as well, while keeping the existing
    voter-survey permission path intact.
    """

    def has_permission(self, request, view):
        if super().has_permission(request, view):
            return True

        action = getattr(view, 'action', None)
        if action not in {'update', 'partial_update'}:
            return False

        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.role == 'admin':
            return True

        roles = resolve_user_permission_roles(request.user, screen_slug='field-activity')
        if not roles:
            return False

        from campaign_os.accounts.models import UserScreenPermission

        flag = ACTION_TO_FLAG.get(action, 'can_view')
        permissions_qs = UserScreenPermission.objects.filter(
            role__in=roles,
            user_screen__slug='field-activity',
        )
        return any(getattr(permission, flag, False) for permission in permissions_qs)


class FieldSurveyViewSet(viewsets.ModelViewSet):
    screen_slug = 'voter-survey'
    queryset = FieldSurvey.objects.filter(is_active=True)
    serializer_class = FieldSurveySerializer
    permission_classes = [permissions.IsAuthenticated, FieldSurveyPermission]
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
        try:
            _sync_field_followup_status(instance, self.request.user)
        except Exception:
            logger.exception("Failed to sync field follow-up status for survey %s", instance.pk)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
