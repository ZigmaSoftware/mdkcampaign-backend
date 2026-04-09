import logging
import re

from django.db.models import (
    Q,
    Count,
    Sum,
    Case,
    When,
    IntegerField,
    OuterRef,
    Subquery,
    DateField,
)
from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ActivityLog, FieldSurvey
from .serializers import ActivityLogSerializer, FieldSurveySerializer
from campaign_os.core.permissions import (
    ScreenPermission,
    ACTION_TO_FLAG,
    resolve_user_permission_roles,
)
from campaign_os.masters.models import Booth
from campaign_os.telecalling.models import TelecallingFeedback
from campaign_os.telecalling.models import TelecallingAssignmentVoter


logger = logging.getLogger(__name__)
SURVEY_ID_PATTERN = re.compile(r'\[survey_id:(\d+)\]')


def _build_telecaller_lookup_for_surveys(surveys):
    voter_ids = {survey.voter_id for survey in surveys if getattr(survey, 'voter_id', None)}
    voter_names = {
        (survey.voter_name or '').strip()
        for survey in surveys
        if getattr(survey, 'voter_name', None)
    }

    if not voter_ids and not voter_names:
        return {}, {}

    assignment_rows = (
        TelecallingAssignmentVoter.objects
        .filter(
            Q(voter_id__in=voter_ids) |
            Q(voter_name__in=[name for name in voter_names if name])
        )
        .select_related('assignment')
        .order_by('-assignment__assigned_date', '-assignment__created_at', '-assignment_id', '-id')
    )

    by_voter = {}
    by_name = {}
    for row in assignment_rows:
        info = {
            'name': row.assignment.telecaller_name or '',
            'phone': row.assignment.telecaller_phone or '',
        }
        if row.voter_id and row.voter_id not in by_voter:
            by_voter[row.voter_id] = info
        if row.voter_name:
            key = row.voter_name.strip().lower()
            if key and key not in by_name:
                by_name[key] = info

    return by_voter, by_name


def _survey_location_maps(surveys):
    booth_numbers = {survey.booth_no.strip() for survey in surveys if getattr(survey, 'booth_no', None)}
    booth_map = {}
    if booth_numbers:
        booths = (
            Booth.objects
            .filter(is_active=True, number__in=booth_numbers)
            .select_related('panchayat__union__block')
        )
        for booth in booths:
            booth_map[booth.number] = {
                'panchayat': getattr(booth.panchayat, 'name', '') if booth.panchayat_id else '',
                'union': getattr(getattr(booth.panchayat, 'union', None), 'name', '') if booth.panchayat_id else '',
                'block': getattr(getattr(getattr(booth.panchayat, 'union', None), 'block', None), 'name', '') if booth.panchayat_id else '',
            }
    return booth_map


def _annotate_latest_field_followup_feedback(queryset):
    latest_feedback = (
        TelecallingFeedback.objects
        .filter(
            is_active=True,
            followup_type='field_survey',
            survey_id=OuterRef('pk'),
        )
        .order_by('-date', '-created_at', '-id')
    )
    return queryset.annotate(
        latest_decision_id=Subquery(latest_feedback.values('id')[:1]),
        latest_decision_action=Subquery(latest_feedback.values('action')[:1]),
        latest_decision_followup_type=Subquery(latest_feedback.values('followup_type')[:1]),
        latest_decision_date=Subquery(latest_feedback.values('date')[:1], output_field=DateField()),
    )


def _followup_count_payload(queryset):
    agg = queryset.order_by().aggregate(
        all=Count('id'),
        done=Sum(
            Case(
                When(latest_decision_action='followup_not_required', then=1),
                default=0,
                output_field=IntegerField(),
            )
        ),
    )
    total = int(agg.get('all') or 0)
    done = int(agg.get('done') or 0)
    return {
        'all': total,
        'pending': max(0, total - done),
        'done': done,
    }


def _apply_location_filters(queryset, *, block='', panchayat='', union=''):
    if not block and not panchayat and not union:
        return queryset

    rows = list(queryset.order_by().values('id', 'booth_no', 'block'))
    if not rows:
        return queryset.none()

    booth_numbers = {(row.get('booth_no') or '').strip() for row in rows if (row.get('booth_no') or '').strip()}
    booth_map = {}
    if booth_numbers:
        booths = (
            Booth.objects
            .filter(is_active=True, number__in=booth_numbers)
            .select_related('panchayat__union__block')
        )
        for booth in booths:
            booth_map[booth.number] = {
                'panchayat': getattr(booth.panchayat, 'name', '') if booth.panchayat_id else '',
                'union': getattr(getattr(booth.panchayat, 'union', None), 'name', '') if booth.panchayat_id else '',
                'block': getattr(getattr(getattr(booth.panchayat, 'union', None), 'block', None), 'name', '') if booth.panchayat_id else '',
            }

    matched_ids = []
    for row in rows:
        location = booth_map.get((row.get('booth_no') or '').strip(), {})
        row_block = (row.get('block') or location.get('block') or '')
        if block and row_block != block:
            continue
        if panchayat and (location.get('panchayat') or '') != panchayat:
            continue
        if union and (location.get('union') or '') != union:
            continue
        matched_ids.append(row['id'])

    if not matched_ids:
        return queryset.none()
    return queryset.filter(id__in=matched_ids)


def _telecaller_lookup_for_survey_rows(survey_rows):
    voter_ids = {row.get('voter_id') for row in survey_rows if row.get('voter_id')}
    voter_names = {(row.get('voter_name') or '').strip() for row in survey_rows if (row.get('voter_name') or '').strip()}
    if not voter_ids and not voter_names:
        return {}, {}

    assignment_rows = (
        TelecallingAssignmentVoter.objects
        .filter(
            Q(voter_id__in=voter_ids) |
            Q(voter_name__in=list(voter_names))
        )
        .select_related('assignment')
        .order_by('-assignment__assigned_date', '-assignment__created_at', '-assignment_id', '-id')
    )

    by_voter = {}
    by_name = {}
    for row in assignment_rows:
        info = {
            'name': row.assignment.telecaller_name or '',
            'phone': row.assignment.telecaller_phone or '',
        }
        if row.voter_id and row.voter_id not in by_voter:
            by_voter[row.voter_id] = info
        if row.voter_name:
            normalized = row.voter_name.strip().lower()
            if normalized and normalized not in by_name:
                by_name[normalized] = info
    return by_voter, by_name


def _apply_telecaller_filter(queryset, telecaller_name):
    if not telecaller_name:
        return queryset

    survey_rows = list(queryset.order_by().values('id', 'voter_id', 'voter_name'))
    if not survey_rows:
        return queryset.none()

    by_voter, by_name = _telecaller_lookup_for_survey_rows(survey_rows)
    matched_ids = []
    for row in survey_rows:
        normalized = (row.get('voter_name') or '').strip().lower()
        resolved = by_voter.get(row.get('voter_id')) or by_name.get(normalized) or {}
        if resolved.get('name', '') == telecaller_name:
            matched_ids.append(row['id'])

    if not matched_ids:
        return queryset.none()
    return queryset.filter(id__in=matched_ids)


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

    @action(detail=False, methods=['get'], url_path='followup-list')
    def followup_list(self, request):
        field_survey_ids = set(
            TelecallingFeedback.objects
            .filter(is_active=True, followup_type='field_survey', survey__isnull=False)
            .values_list('survey_id', flat=True)
        )

        log_notes = ActivityLog.objects.filter(
            is_active=True,
            category='field',
            notes__contains='[survey_id:',
        ).values_list('notes', flat=True)
        for note in log_notes:
            match = SURVEY_ID_PATTERN.search(note or '')
            if match:
                field_survey_ids.add(int(match.group(1)))

        if not field_survey_ids:
            response = Response({'results': [], 'count': 0})
            response.data['counts'] = {'all': 0, 'pending': 0, 'done': 0}
            response.data['filtered_counts'] = {'all': 0, 'pending': 0, 'done': 0}
            response.data['volunteers'] = []
            response.data['telecallers'] = []
            return response

        base_surveys = _annotate_latest_field_followup_feedback(
            FieldSurvey.objects
            .filter(is_active=True, id__in=field_survey_ids)
            .select_related('voter')
            .order_by('-survey_date', '-created_at', '-id')
        )

        base_counts = _followup_count_payload(base_surveys)
        volunteer_names = sorted(
            [
                name
                for name in base_surveys.order_by().values_list('assigned_volunteer', flat=True).distinct()
                if name
            ]
        )
        telecaller_row_lookup = list(base_surveys.order_by().values('voter_id', 'voter_name'))
        telecaller_lookup_by_voter, telecaller_lookup_by_name = _telecaller_lookup_for_survey_rows(telecaller_row_lookup)
        telecaller_names = sorted(
            {
                (
                    telecaller_lookup_by_voter.get(row.get('voter_id')) or
                    telecaller_lookup_by_name.get((row.get('voter_name') or '').strip().lower()) or {}
                ).get('name', '')
                for row in telecaller_row_lookup
            } - {''},
            key=str.lower,
        )

        scoped_surveys = base_surveys

        search = (request.query_params.get('search') or '').strip()
        if search:
            scoped_surveys = scoped_surveys.filter(
                Q(voter_name__icontains=search) |
                Q(booth_no__icontains=search) |
                Q(block__icontains=search)
            )

        booth = (request.query_params.get('booth') or '').strip()
        if booth:
            scoped_surveys = scoped_surveys.filter(booth_no=booth)

        volunteer = (request.query_params.get('volunteer') or '').strip()
        if volunteer:
            scoped_surveys = scoped_surveys.filter(assigned_volunteer=volunteer)

        support_level = (request.query_params.get('support_level') or '').strip()
        if support_level:
            scoped_surveys = scoped_surveys.filter(support_level=support_level)

        response_status = (request.query_params.get('response_status') or '').strip()
        if response_status:
            scoped_surveys = scoped_surveys.filter(response_status=response_status)

        aware_of_candidate = (request.query_params.get('aware_of_candidate') or '').strip()
        if aware_of_candidate:
            scoped_surveys = scoped_surveys.filter(aware_of_candidate=aware_of_candidate)

        likely_to_vote = (request.query_params.get('likely_to_vote') or '').strip()
        if likely_to_vote:
            scoped_surveys = scoped_surveys.filter(likely_to_vote=likely_to_vote)

        party = (request.query_params.get('party') or '').strip()
        if party:
            scoped_surveys = scoped_surveys.filter(party_preference=party)

        scoped_surveys = _apply_location_filters(
            scoped_surveys,
            block=(request.query_params.get('block') or '').strip(),
            panchayat=(request.query_params.get('panchayat') or '').strip(),
            union=(request.query_params.get('union') or '').strip(),
        )

        telecaller = (request.query_params.get('telecaller') or '').strip()
        scoped_surveys = _apply_telecaller_filter(scoped_surveys, telecaller)

        date_from = (request.query_params.get('date_from') or '').strip()
        if date_from:
            scoped_surveys = scoped_surveys.filter(survey_date__gte=date_from)

        date_to = (request.query_params.get('date_to') or '').strip()
        if date_to:
            scoped_surveys = scoped_surveys.filter(survey_date__lte=date_to)

        filtered_counts = _followup_count_payload(scoped_surveys)

        status_filter = (request.query_params.get('status') or 'all').strip().lower()
        if status_filter == 'pending':
            scoped_surveys = scoped_surveys.exclude(latest_decision_action='followup_not_required')
        elif status_filter == 'done':
            scoped_surveys = scoped_surveys.filter(latest_decision_action='followup_not_required')

        page = self.paginate_queryset(scoped_surveys)
        surveys = list(page) if page is not None else list(scoped_surveys)
        telecaller_by_voter, telecaller_by_name = _build_telecaller_lookup_for_surveys(surveys)

        payload = []
        for survey in surveys:
            decision_date = getattr(survey, 'latest_decision_date', None)
            normalized_name = (survey.voter_name or '').strip().lower()
            telecaller_info = (
                (telecaller_by_voter.get(survey.voter_id) if survey.voter_id else None) or
                telecaller_by_name.get(normalized_name) or
                {}
            )
            voter = survey.voter if survey.voter_id and survey.voter else None
            payload.append({
                'id': survey.id,
                'survey_date': str(survey.survey_date) if survey.survey_date else '',
                'block': survey.block or '',
                'village': survey.village or '',
                'booth_no': survey.booth_no or '',
                'voter_name': survey.voter_name or '',
                'age': survey.age,
                'gender': survey.gender or '',
                'phone': survey.phone or (voter.phone if voter else '') or '',
                'phone2': (voter.phone2 if voter else '') or '',
                'alt_phoneno2': (voter.alt_phoneno2 if voter else '') or '',
                'alt_phoneno3': (voter.alt_phoneno3 if voter else '') or '',
                'address': survey.address or '',
                'aware_of_candidate': survey.aware_of_candidate or '',
                'likely_to_vote': survey.likely_to_vote or '',
                'support_level': survey.support_level or '',
                'party_preference': survey.party_preference or '',
                'remarks': survey.remarks or '',
                'response_status': survey.response_status or '',
                'surveyed_by': survey.surveyed_by or '',
                'assigned_volunteer': survey.assigned_volunteer or '',
                'telecaller_name': telecaller_info.get('name', ''),
                'telecaller_phone': telecaller_info.get('phone', ''),
                'decision': {
                    'action': survey.latest_decision_action,
                    'followup_type': survey.latest_decision_followup_type or '',
                    'date': str(decision_date) if decision_date else '',
                } if survey.latest_decision_id else None,
            })

        response = (
            self.get_paginated_response(payload)
            if page is not None
            else Response({'results': payload, 'count': len(payload)})
        )
        response.data['counts'] = base_counts
        response.data['filtered_counts'] = filtered_counts
        response.data['volunteers'] = volunteer_names
        response.data['telecallers'] = telecaller_names
        return response
