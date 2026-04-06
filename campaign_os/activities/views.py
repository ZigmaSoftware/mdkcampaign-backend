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


def _user_has_screen_flag(user, screen_slug, flag):
    if not user or not getattr(user, 'is_authenticated', False):
        return False

    if getattr(user, 'role', '') == 'admin':
        return True

    roles = resolve_user_permission_roles(user, screen_slug=screen_slug)
    if not roles:
        return False

    from campaign_os.accounts.models import UserScreenPermission

    permissions_qs = UserScreenPermission.objects.filter(
        role__in=roles,
        user_screen__slug=screen_slug,
    )
    return any(getattr(permission, flag, False) for permission in permissions_qs)


def _user_has_any_screen_flag(user, screen_slugs, flag):
    for screen_slug in screen_slugs:
        if _user_has_screen_flag(user, screen_slug, flag):
            return True
    return False


def _activity_log_category_from_request(request, view):
    action = getattr(view, 'action', None)
    if action == 'list':
        return (request.query_params.get('category') or '').strip().lower()

    if action == 'create':
        return (request.data.get('category') or '').strip().lower()

    if action in {'retrieve', 'update', 'partial_update', 'destroy'}:
        pk = getattr(view, 'kwargs', {}).get('pk')
        if not pk:
            return ''
        return (
            ActivityLog.objects
            .filter(is_active=True, pk=pk)
            .values_list('category', flat=True)
            .first()
            or ''
        ).strip().lower()

    return ''


def _activity_log_permission_slugs(category, flag):
    if flag == 'can_view':
        return {
            'agent': ('agent-activity', 'activity-report'),
            'field': ('field-activity', 'feedback-review', 'activity-report'),
            'volunteer': ('volunteer-activity', 'activity-report'),
        }.get(category, ())

    return {
        'agent': {
            'can_add': ('agent-activity',),
            'can_edit': ('agent-activity',),
            'can_delete': ('agent-activity',),
        },
        'field': {
            'can_add': ('field-activity', 'feedback-review'),
            'can_edit': ('field-activity',),
            'can_delete': ('field-activity',),
        },
        'volunteer': {
            'can_add': ('volunteer-activity',),
            'can_edit': ('volunteer-activity',),
            'can_delete': ('volunteer-activity',),
        },
    }.get(category, {}).get(flag, ())


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


class ActivityLogPermission(ScreenPermission):
    """
    Activity Log data is shared by agent, field, volunteer, and feedback-review
    screens. Keep each screen independent by resolving permission from the
    requested activity category instead of forcing everything through
    `agent-activity`.
    """

    def has_permission(self, request, view):
        if super().has_permission(request, view):
            return True

        action = getattr(view, 'action', None)
        flag = ACTION_TO_FLAG.get(action, 'can_view')
        category = _activity_log_category_from_request(request, view)
        if not category:
            return False

        screen_slugs = _activity_log_permission_slugs(category, flag)
        if not screen_slugs:
            return False

        return _user_has_any_screen_flag(request.user, screen_slugs, flag)


class ActivityLogViewSet(viewsets.ModelViewSet):
    screen_slug = 'agent-activity'
    view_permission_screen_slugs = ('activity-report',)
    queryset = ActivityLog.objects.filter(is_active=True)
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated, ActivityLogPermission]
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
    view_permission_screen_slugs = ('activity-report', 'field-activity', 'feedback-review')
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
