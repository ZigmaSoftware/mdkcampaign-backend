import re

from django.db.models import (
    Prefetch,
    Q,
    Count,
    Sum,
    Case,
    When,
    F,
    Window,
    IntegerField,
    Subquery,
)
from django.db.models.functions import RowNumber
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from campaign_os.activities.models import ActivityLog, FieldSurvey
from campaign_os.beneficiaries.models import Beneficiary
from campaign_os.core.permissions import ScreenPermission
from campaign_os.masters.models import Booth
from campaign_os.volunteers.models import Volunteer

from .models import TelecallingAssignment, TelecallingAssignmentVoter, TelecallingFeedback
from .serializers import TelecallingAssignmentSerializer, TelecallingFeedbackSerializer
from .workflow import WORKFLOW_LABELS, build_nonvoter_status_map, build_voter_status_map


SURVEY_ID_PATTERN = re.compile(r'\[survey_id:(\d+)\]')


def _assignment_time_value(assignment):
    if not assignment.created_at:
        return ''
    return timezone.localtime(assignment.created_at).strftime('%H:%M:%S')


def _assignment_time_label(assignment):
    if not assignment.created_at:
        return ''
    return timezone.localtime(assignment.created_at).strftime('%Y-%m-%d %H:%M:%S')


def _serialize_field_survey_record(survey):
    if not survey:
        return None

    voter = getattr(survey, 'voter', None)

    return {
        'id': survey.id,
        'voter': survey.voter_id,
        'survey_date': str(survey.survey_date) if survey.survey_date else '',
        'block': survey.block or '',
        'village': survey.village or '',
        'booth_no': survey.booth_no or '',
        'voter_name': survey.voter_name or '',
        'age': survey.age,
        'gender': survey.gender or '',
        'phone': survey.phone or '',
        'phone2': getattr(voter, 'phone2', '') or '',
        'alt_phoneno2': getattr(voter, 'alt_phoneno2', '') or '',
        'alt_phoneno3': getattr(voter, 'alt_phoneno3', '') or '',
        'address': survey.address or '',
        'is_registered': survey.is_registered or '',
        'aware_of_candidate': survey.aware_of_candidate or '',
        'likely_to_vote': survey.likely_to_vote or '',
        'support_level': survey.support_level or '',
        'party_preference': survey.party_preference or '',
        'key_issues': survey.key_issues or '',
        'remarks': survey.remarks or '',
        'response_status': survey.response_status or '',
        'surveyed_by': survey.surveyed_by or '',
        'assigned_volunteer': survey.assigned_volunteer or '',
        'created_at': survey.created_at.isoformat() if survey.created_at else '',
    }


def _build_assignment_survey_lookup(flat_rows):
    voter_ids = {row['voter'] for row in flat_rows if row.get('voter')}
    loose_names = {row['voter_name'].strip() for row in flat_rows if row.get('voter_name')}

    survey_qs = FieldSurvey.objects.filter(is_active=True).select_related('voter').order_by('-survey_date', '-created_at', '-id')
    if voter_ids or loose_names:
        survey_qs = survey_qs.filter(
            Q(voter_id__in=voter_ids) |
            Q(voter__isnull=True, voter_name__in=loose_names)
        )
    else:
        survey_qs = survey_qs.none()

    by_voter = {}
    by_name_phone = {}
    by_name = {}

    for survey in survey_qs:
        if survey.voter_id and survey.voter_id not in by_voter:
            by_voter[survey.voter_id] = survey

        if not survey.voter_id and survey.voter_name:
            normalized_name = survey.voter_name.strip().lower()
            if survey.phone:
                by_name_phone.setdefault(f'{normalized_name}::{survey.phone}', survey)
            by_name.setdefault(normalized_name, survey)

    return by_voter, by_name_phone, by_name


def _match_assignment_survey(row, by_voter, by_name_phone, by_name):
    if row.get('voter'):
        return by_voter.get(row['voter'])

    normalized_name = (row.get('voter_name') or '').strip().lower()
    phone = row.get('phone') or ''
    if phone:
        matched = by_name_phone.get(f'{normalized_name}::{phone}')
        if matched:
            return matched
    return by_name.get(normalized_name)


def _latest_feedback_map(feedbacks):
    latest = {}
    for feedback in feedbacks:
        survey_id = feedback.survey_id
        if survey_id and survey_id not in latest:
            latest[survey_id] = feedback
    return latest


def _build_telecaller_lookup_for_surveys(surveys):
    voter_ids = {survey.voter_id for survey in surveys if survey.voter_id}
    voter_names = {survey.voter_name.strip() for survey in surveys if survey.voter_name}

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
        if row.voter_id:
            by_voter[row.voter_id] = info
        if row.voter_name:
            by_name[row.voter_name.strip().lower()] = info

    return by_voter, by_name


def _build_assignment_detail_lookup_for_surveys(surveys):
    voter_ids = {survey.voter_id for survey in surveys if survey.voter_id}
    voter_names = {survey.voter_name.strip() for survey in surveys if survey.voter_name}

    if not voter_ids and not voter_names:
        return {}, {}

    assignment_rows = (
        TelecallingAssignmentVoter.objects
        .filter(
            Q(voter_id__in=voter_ids) |
            Q(voter_name__in=[name for name in voter_names if name])
        )
        .select_related('assignment', 'voter')
        .order_by('-assignment__assigned_date', '-assignment__created_at', '-assignment_id', '-id')
    )

    by_voter = {}
    by_name = {}
    for row in assignment_rows:
        info = {
            'voter_id_no': row.voter_id_no or '',
            'booth_name': row.booth_name or '',
            'phone': row.phone or '',
            'phone2': getattr(getattr(row, 'voter', None), 'phone2', '') or '',
            'alt_phoneno2': getattr(getattr(row, 'voter', None), 'alt_phoneno2', '') or '',
            'alt_phoneno3': getattr(getattr(row, 'voter', None), 'alt_phoneno3', '') or '',
            'address': row.address or '',
            'age': row.age,
            'gender': row.gender or '',
        }
        if row.voter_id and row.voter_id not in by_voter:
            by_voter[row.voter_id] = info
        if row.voter_name:
            normalized_name = row.voter_name.strip().lower()
            if normalized_name and normalized_name not in by_name:
                by_name[normalized_name] = info

    return by_voter, by_name


def _survey_location_maps(surveys):
    booth_numbers = {survey.booth_no.strip() for survey in surveys if survey.booth_no}
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


def _booth_location_map_for_numbers(booth_numbers):
    cleaned = {str(number).strip() for number in booth_numbers if str(number or '').strip()}
    booth_map = {}
    if not cleaned:
        return booth_map

    booths = (
        Booth.objects
        .filter(is_active=True, number__in=cleaned)
        .select_related('panchayat__union__block')
    )
    for booth in booths:
        booth_map[booth.number] = {
            'panchayat': getattr(booth.panchayat, 'name', '') if booth.panchayat_id else '',
            'union': getattr(getattr(booth.panchayat, 'union', None), 'name', '') if booth.panchayat_id else '',
            'block': getattr(getattr(getattr(booth.panchayat, 'union', None), 'block', None), 'name', '') if booth.panchayat_id else '',
        }
    return booth_map


def _latest_feedback_for_surveys(surveys_queryset):
    survey_ids = surveys_queryset.order_by().values('id')
    return (
        TelecallingFeedback.objects
        .filter(is_active=True, survey__isnull=False, survey_id__in=Subquery(survey_ids))
        .annotate(
            _rn=Window(
                expression=RowNumber(),
                partition_by=[F('survey_id')],
                order_by=[F('date').desc(), F('created_at').desc(), F('id').desc()],
            )
        )
        .filter(_rn=1)
    )


def _review_count_payload_from_surveys(surveys_queryset, include_followup_required_other=False):
    total = surveys_queryset.order_by().count()
    latest_feedbacks = _latest_feedback_for_surveys(surveys_queryset)
    agg = latest_feedbacks.aggregate(
        resolved=Count('id'),
        followup_required=Sum(
            Case(
                When(action='followup_required', then=1),
                default=0,
                output_field=IntegerField(),
            )
        ),
        field_survey=Sum(
            Case(
                When(action='followup_required', followup_type='field_survey', then=1),
                default=0,
                output_field=IntegerField(),
            )
        ),
        telephonic=Sum(
            Case(
                When(action='followup_required', followup_type='telephonic', then=1),
                default=0,
                output_field=IntegerField(),
            )
        ),
        followup_not_required=Sum(
            Case(
                When(action='followup_not_required', then=1),
                default=0,
                output_field=IntegerField(),
            )
        ),
    )
    resolved = int(agg.get('resolved') or 0)
    payload = {
        'all': int(total),
        'pending': max(0, int(total) - resolved),
        'followup_required': int(agg.get('followup_required') or 0),
        'field_survey': int(agg.get('field_survey') or 0),
        'telephonic': int(agg.get('telephonic') or 0),
        'followup_not_required': int(agg.get('followup_not_required') or 0),
    }
    if include_followup_required_other:
        payload['followup_required_other'] = max(
            0,
            payload['followup_required'] - payload['field_survey'] - payload['telephonic'],
        )
    return payload


def _apply_location_filters(queryset, *, block='', panchayat='', union=''):
    if not block and not panchayat and not union:
        return queryset

    scoped = queryset
    if panchayat or union:
        booth_qs = Booth.objects.filter(is_active=True)
        if panchayat:
            booth_qs = booth_qs.filter(panchayat__name=panchayat)
        if union:
            booth_qs = booth_qs.filter(panchayat__union__name=union)
        scoped = scoped.filter(booth_no__in=Subquery(booth_qs.values('number')))

    if block:
        block_booths = (
            Booth.objects
            .filter(is_active=True, panchayat__union__block__name=block)
            .values('number')
        )
        scoped = scoped.filter(Q(block=block) | Q(booth_no__in=Subquery(block_booths)))

    return scoped


def _apply_telecaller_filter(queryset, telecaller_name):
    if not telecaller_name:
        return queryset

    assignment_rows = list(
        TelecallingAssignmentVoter.objects
        .filter(
            assignment__is_active=True,
            assignment__telecaller_name=telecaller_name,
        )
        .order_by()
        .values('voter_id', 'voter_name')
    )
    if not assignment_rows:
        return queryset.none()

    voter_ids = {row['voter_id'] for row in assignment_rows if row.get('voter_id')}
    voter_names = {(row.get('voter_name') or '').strip() for row in assignment_rows if (row.get('voter_name') or '').strip()}
    return queryset.filter(
        Q(voter_id__in=voter_ids) |
        Q(voter__isnull=True, voter_name__in=list(voter_names))
    )


class TelecallingAssignmentViewSet(viewsets.ModelViewSet):
    screen_slug = 'assign-telecalling'
    view_permission_screen_slugs = ('telecalling-assigned', 'voter-survey', 'feedback-review', 'activity-report')
    queryset = TelecallingAssignment.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            'voters',
            queryset=TelecallingAssignmentVoter.objects.select_related('voter__booth'),
        )
    )
    serializer_class = TelecallingAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['assigned_date', 'telecaller_id']

    def get_queryset(self):
        queryset = super().get_queryset()

        date_value = (self.request.query_params.get('date') or '').strip()
        if date_value:
            queryset = queryset.filter(assigned_date=date_value)

        telecaller_value = (self.request.query_params.get('telecaller') or '').strip()
        if telecaller_value:
            if telecaller_value.isdigit():
                queryset = queryset.filter(telecaller_id=int(telecaller_value))
            else:
                queryset = queryset.filter(telecaller_name__iexact=telecaller_value)

        return queryset

    def _include_workflow(self):
        value = (self.request.query_params.get('include_workflow') or '').strip().lower()
        return value in {'1', 'true', 'yes'}

    def _with_workflow_context(self, objects):
        ctx = self.get_serializer_context()
        if not self._include_workflow():
            return ctx

        voter_ids = set()
        for assignment in objects:
            voters_rel = getattr(assignment, 'voters', None)
            if not voters_rel:
                continue
            for voter in voters_rel.all():
                if voter.voter_id:
                    voter_ids.add(voter.voter_id)
        ctx['voter_status_map'] = build_voter_status_map(voter_ids)
        return ctx

    @action(detail=False, methods=['get'], url_path='assignable-people')
    def assignable_people(self, request):
        category = (request.query_params.get('category') or '').strip().lower()
        search = (request.query_params.get('search') or '').strip()
        workflow_status = (request.query_params.get('workflow_status') or '').strip().lower()
        contact_status = (request.query_params.get('contact_status') or '').strip().lower()

        if category not in {'volunteer', 'beneficiary'}:
            return Response(
                {'detail': 'category must be volunteer or beneficiary'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if category == 'volunteer':
            role_value = (request.query_params.get('role') or '').strip()
            queryset = Volunteer.objects.filter(is_active=True).select_related('user', 'booth', 'volunteer_role')

            if role_value:
                queryset = queryset.filter(
                    Q(role__iexact=role_value) |
                    Q(volunteer_role__name__iexact=role_value)
                )

            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(phone__icontains=search) |
                    Q(phone2__icontains=search) |
                    Q(voter_id__icontains=search) |
                    Q(role__icontains=search) |
                    Q(volunteer_role__name__icontains=search) |
                    Q(booth__name__icontains=search) |
                    Q(booth__number__icontains=search)
                )

            if contact_status == 'with':
                queryset = queryset.exclude(
                    (Q(phone__isnull=True) | Q(phone__exact='')) &
                    (Q(phone2__isnull=True) | Q(phone2__exact=''))
                )
            elif contact_status == 'without':
                queryset = queryset.filter(
                    Q(phone__isnull=True) | Q(phone__exact='')
                ).filter(
                    Q(phone2__isnull=True) | Q(phone2__exact='')
                )

            raw_rows = []
            for volunteer in queryset.order_by('name', 'id'):
                role_label = getattr(getattr(volunteer, 'volunteer_role', None), 'name', '') or volunteer.role or ''
                raw_rows.append({
                    'id': volunteer.id,
                    'source_id': volunteer.id,
                    'name': volunteer.name or (volunteer.user.get_full_name() if volunteer.user_id else f'Volunteer #{volunteer.id}'),
                    'voter_id': volunteer.voter_id or '',
                    'phone': volunteer.phone or '',
                    'phone2': volunteer.phone2 or '',
                    'alt_phoneno2': '',
                    'alt_phoneno3': '',
                    'address': '',
                    'booth': volunteer.booth_id or 0,
                    'booth_no': getattr(getattr(volunteer, 'booth', None), 'number', '') or '',
                    'booth_name': getattr(getattr(volunteer, 'booth', None), 'name', '') or '',
                    'age': volunteer.age,
                    'gender': volunteer.gender or '',
                    'relation_label': role_label,
                    'entity_type': 'volunteer',
                    'phones': [volunteer.phone or '', volunteer.phone2 or ''],
                })
        else:
            scheme_value = (request.query_params.get('scheme') or '').strip()
            queryset = Beneficiary.objects.filter(is_active=True).select_related('booth', 'scheme')

            if scheme_value:
                queryset = queryset.filter(
                    Q(scheme__name__iexact=scheme_value) |
                    Q(scheme_name__iexact=scheme_value)
                )

            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(voter_id__icontains=search) |
                    Q(phone__icontains=search) |
                    Q(phone2__icontains=search) |
                    Q(address__icontains=search) |
                    Q(booth__name__icontains=search) |
                    Q(booth__number__icontains=search) |
                    Q(scheme__name__icontains=search) |
                    Q(scheme_name__icontains=search)
                )

            if contact_status == 'with':
                queryset = queryset.exclude(
                    (Q(phone__isnull=True) | Q(phone__exact='')) &
                    (Q(phone2__isnull=True) | Q(phone2__exact=''))
                )
            elif contact_status == 'without':
                queryset = queryset.filter(
                    Q(phone__isnull=True) | Q(phone__exact='')
                ).filter(
                    Q(phone2__isnull=True) | Q(phone2__exact='')
                )

            raw_rows = []
            for beneficiary in queryset.order_by('name', 'id'):
                scheme_label = getattr(getattr(beneficiary, 'scheme', None), 'name', '') or beneficiary.scheme_name or ''
                raw_rows.append({
                    'id': beneficiary.id,
                    'source_id': beneficiary.id,
                    'name': beneficiary.name or f'Beneficiary #{beneficiary.id}',
                    'voter_id': beneficiary.voter_id or '',
                    'phone': beneficiary.phone or '',
                    'phone2': beneficiary.phone2 or '',
                    'alt_phoneno2': '',
                    'alt_phoneno3': '',
                    'address': beneficiary.address or '',
                    'booth': beneficiary.booth_id or 0,
                    'booth_no': getattr(getattr(beneficiary, 'booth', None), 'number', '') or '',
                    'booth_name': getattr(getattr(beneficiary, 'booth', None), 'name', '') or '',
                    'age': beneficiary.age,
                    'gender': beneficiary.gender or '',
                    'relation_label': scheme_label,
                    'entity_type': 'beneficiary',
                    'phones': [beneficiary.phone or '', beneficiary.phone2 or ''],
                })

        status_map = build_nonvoter_status_map(category, raw_rows)
        workflow_summary = {}
        for row in raw_rows:
            status_info = status_map.get(row['source_id'], {
                'status': 'unassigned',
                'label': WORKFLOW_LABELS['unassigned'],
                'is_locked': False,
                'telecaller_name': '',
                'telecaller_phone': '',
            })
            row['workflow_status'] = status_info['status']
            row['workflow_label'] = status_info['label']
            row['is_locked'] = status_info['is_locked']
            row['assigned_telecaller_name'] = status_info.get('telecaller_name', '')
            row['assigned_telecaller_phone'] = status_info.get('telecaller_phone', '')
            workflow_summary[row['workflow_status']] = workflow_summary.get(row['workflow_status'], 0) + 1

        raw_count = len(raw_rows)
        filtered_rows = raw_rows
        if workflow_status:
            filtered_rows = [row for row in raw_rows if row.get('workflow_status') == workflow_status]

        page = self.paginate_queryset(filtered_rows)
        payload = list(page) if page is not None else filtered_rows
        response = (
            self.get_paginated_response(payload)
            if page is not None
            else Response({'count': len(payload), 'next': None, 'previous': None, 'results': payload})
        )
        response.data['raw_count'] = raw_count
        response.data['workflow_summary'] = workflow_summary
        return response

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        assignment_time = (request.query_params.get('assignment_time') or '').strip()
        include_summary = (request.query_params.get('include_summary') or '').strip().lower() in {'1', 'true', 'yes'}

        if assignment_time:
            objects = [
                assignment for assignment in queryset
                if assignment.created_at
                and timezone.localtime(assignment.created_at).strftime('%H:%M:%S') == assignment_time
            ]
            page = self.paginate_queryset(objects)
        else:
            page = self.paginate_queryset(queryset)
            objects = list(page) if page is not None else list(queryset)

        if assignment_time and page is not None:
            objects = list(page)

        serializer = self.get_serializer(
            objects,
            many=True,
            context=self._with_workflow_context(objects),
        )
        if page is not None:
            response = self.get_paginated_response(serializer.data)
            if include_summary:
                summary_queryset = queryset
                if assignment_time:
                    summary_queryset = [assignment for assignment in queryset if assignment.created_at and timezone.localtime(assignment.created_at).strftime('%H:%M:%S') == assignment_time]
                    total_voters = sum(len(getattr(assignment, 'voters', []).all() if hasattr(getattr(assignment, 'voters', None), 'all') else getattr(assignment, 'voters', [])) for assignment in summary_queryset)
                else:
                    total_voters = (
                        summary_queryset
                        .annotate(voter_count=Count('voters'))
                        .aggregate(total=Count('id'), total_voters=Count('voters'))
                    )
                    total_voters = total_voters.get('total_voters', 0)
                response.data['total_voters'] = total_voters
            return response
        if include_summary:
            total_voters = sum(len(assignment.voters.all()) for assignment in objects)
            return Response({'results': serializer.data, 'total_voters': total_voters})
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            context=self._with_workflow_context([instance]),
        )
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    @action(detail=False, methods=['get'], url_path='filters')
    def filters(self, request):
        queryset = self.get_queryset()
        telecallers = (
            queryset
            .exclude(telecaller_id__isnull=True)
            .values('telecaller_id', 'telecaller_name')
            .distinct()
        )
        return Response({
            'telecallers': sorted(
                [
                    {'id': row['telecaller_id'], 'name': row['telecaller_name']}
                    for row in telecallers
                    if row['telecaller_id'] is not None and row['telecaller_name']
                ],
                key=lambda row: row['name'].lower(),
            ),
        })

    @action(detail=False, methods=['get'], url_path='survey-voters')
    def survey_voters(self, request):
        date_value = (request.query_params.get('date') or '').strip()
        telecaller_value = (request.query_params.get('telecaller') or '').strip()
        scoped_assignments_qs = TelecallingAssignment.objects.filter(is_active=True)
        if date_value:
            scoped_assignments_qs = scoped_assignments_qs.filter(assigned_date=date_value)
        if telecaller_value:
            if telecaller_value.isdigit():
                scoped_assignments_qs = scoped_assignments_qs.filter(telecaller_id=int(telecaller_value))
            else:
                scoped_assignments_qs = scoped_assignments_qs.filter(telecaller_name__iexact=telecaller_value)
        scoped_assignments_qs = scoped_assignments_qs.order_by('-assigned_date', '-created_at', '-id')

        assignment_rows = list(
            scoped_assignments_qs
            .annotate(voter_count=Count('voters'))
            .values(
                'id',
                'created_at',
                'assigned_date',
                'telecaller_id',
                'telecaller_name',
                'telecaller_phone',
                'voter_count',
            )
        )
        assignment_time = (request.query_params.get('assignment_time') or '').strip()

        assignment_time_counts = {}
        selected_assignment_ids = []
        assignment_lookup = {}
        for assignment in assignment_rows:
            created_at = assignment.get('created_at')
            if not created_at:
                continue
            time_value = timezone.localtime(created_at).strftime('%H:%M:%S')
            if time_value:
                bucket = assignment_time_counts.setdefault(time_value, {
                    'count': 0,
                    'label': timezone.localtime(created_at).strftime('%Y-%m-%d %H:%M:%S'),
                })
                bucket['count'] += int(assignment.get('voter_count') or 0)
            if assignment_time and time_value != assignment_time:
                continue
            selected_assignment_ids.append(assignment['id'])
            assignment_lookup[assignment['id']] = {
                'telecaller_id': assignment.get('telecaller_id'),
                'telecaller_name': assignment.get('telecaller_name') or '',
                'telecaller_phone': assignment.get('telecaller_phone') or '',
                'assigned_date': str(assignment.get('assigned_date') or ''),
                'assignment_time': time_value,
            }

        voter_rows = []
        if selected_assignment_ids:
            voter_rows = list(
                TelecallingAssignmentVoter.objects
                .filter(assignment_id__in=selected_assignment_ids)
                .select_related('voter__booth')
                .order_by('id')
            )

        flat_rows = []
        for voter in voter_rows:
            assignment = assignment_lookup.get(voter.assignment_id, {})
            flat_rows.append({
                'assignment_id': voter.assignment_id,
                'id': voter.id,
                'voter': voter.voter_id,
                'source_id': voter.source_id or voter.voter_id,
                'entity_type': voter.entity_type or 'voter',
                'relation_label': voter.relation_label or '',
                'voter_name': voter.voter_name or '',
                'voter_id_no': voter.voter_id_no or '',
                'phone': voter.phone or '',
                'phone2': getattr(getattr(voter, 'voter', None), 'phone2', '') or '',
                'alt_phoneno2': getattr(getattr(voter, 'voter', None), 'alt_phoneno2', '') or '',
                'alt_phoneno3': getattr(getattr(voter, 'voter', None), 'alt_phoneno3', '') or '',
                'address': voter.address or '',
                'booth_name': voter.booth_name or '',
                'booth_no': voter.booth_no or (getattr(getattr(voter, 'voter', None), 'booth', None).number if getattr(getattr(voter, 'voter', None), 'booth', None) else ''),
                'age': voter.age,
                'gender': voter.gender or '',
                'telecaller_id': assignment.get('telecaller_id'),
                'telecaller_name': assignment.get('telecaller_name', ''),
                'telecaller_phone': assignment.get('telecaller_phone', ''),
                'assigned_date': assignment.get('assigned_date', ''),
                'assignment_time': assignment.get('assignment_time', ''),
            })

        by_voter, by_name_phone, by_name = _build_assignment_survey_lookup(flat_rows)

        base_rows = []
        for row in flat_rows:
            survey_record = _match_assignment_survey(row, by_voter, by_name_phone, by_name)
            base_rows.append({
                **row,
                'survey_record': _serialize_field_survey_record(survey_record),
            })

        base_counts = {
            'all': len(base_rows),
            'pending': sum(1 for row in base_rows if not row['survey_record']),
            'done': sum(1 for row in base_rows if row['survey_record']),
        }
        booth_location_map = _booth_location_map_for_numbers(
            [
                (row.get('survey_record') or {}).get('booth_no') or row.get('booth_no') or ''
                for row in base_rows
            ]
        )

        def survey_record_for(row):
            return row.get('survey_record') or {}

        def row_booth_no(row):
            return (survey_record_for(row).get('booth_no') or row.get('booth_no') or '').strip()

        def row_location(row):
            return booth_location_map.get(row_booth_no(row), {})

        base_rows.sort(
            key=lambda row: (
                1 if not (row.get('address') or '').strip() else 0,
                (row.get('address') or '').strip().lower(),
                row.get('id', 0),
            )
        )

        search = (request.query_params.get('search') or '').strip().lower()
        filtered_rows = base_rows
        if search:
            filtered_rows = [
                row for row in base_rows
                if search in (row['voter_name'] or '').lower()
                or search in (row['voter_id_no'] or '').lower()
                or search in (row['phone'] or '')
                or search in (row['address'] or '').lower()
            ]

        support_level = (request.query_params.get('support_level') or '').strip()
        if support_level:
            filtered_rows = [
                row for row in filtered_rows
                if (survey_record_for(row).get('support_level') or '') == support_level
            ]

        response_status = (request.query_params.get('response_status') or '').strip()
        if response_status:
            filtered_rows = [
                row for row in filtered_rows
                if (survey_record_for(row).get('response_status') or '') == response_status
            ]

        aware_of_candidate = (request.query_params.get('aware_of_candidate') or '').strip()
        if aware_of_candidate:
            filtered_rows = [
                row for row in filtered_rows
                if (survey_record_for(row).get('aware_of_candidate') or '') == aware_of_candidate
            ]

        likely_to_vote = (request.query_params.get('likely_to_vote') or '').strip()
        if likely_to_vote:
            filtered_rows = [
                row for row in filtered_rows
                if (survey_record_for(row).get('likely_to_vote') or '') == likely_to_vote
            ]

        party = (request.query_params.get('party') or '').strip()
        if party:
            filtered_rows = [
                row for row in filtered_rows
                if (survey_record_for(row).get('party_preference') or '') == party
            ]

        block = (request.query_params.get('block') or '').strip()
        if block:
            filtered_rows = [
                row for row in filtered_rows
                if ((survey_record_for(row).get('block') or row_location(row).get('block') or '') == block)
            ]

        booth = (request.query_params.get('booth') or '').strip()
        if booth:
            filtered_rows = [row for row in filtered_rows if row_booth_no(row) == booth]

        date_from = (request.query_params.get('date_from') or '').strip()
        if date_from:
            filtered_rows = [
                row for row in filtered_rows
                if (survey_record_for(row).get('survey_date') or '')
                and str(survey_record_for(row).get('survey_date') or '') >= date_from
            ]

        date_to = (request.query_params.get('date_to') or '').strip()
        if date_to:
            filtered_rows = [
                row for row in filtered_rows
                if (survey_record_for(row).get('survey_date') or '')
                and str(survey_record_for(row).get('survey_date') or '') <= date_to
            ]

        panchayat = (request.query_params.get('panchayat') or '').strip()
        if panchayat:
            filtered_rows = [
                row for row in filtered_rows
                if (row_location(row).get('panchayat') or '') == panchayat
            ]

        union = (request.query_params.get('union') or '').strip()
        if union:
            filtered_rows = [
                row for row in filtered_rows
                if (row_location(row).get('union') or '') == union
            ]

        filtered_counts = {
            'all': len(filtered_rows),
            'pending': sum(1 for row in filtered_rows if not row['survey_record']),
            'done': sum(1 for row in filtered_rows if row['survey_record']),
        }

        status_filter = (request.query_params.get('status') or 'all').strip().lower()
        enriched_rows = filtered_rows
        if status_filter == 'pending':
            enriched_rows = [row for row in filtered_rows if not row['survey_record']]
        elif status_filter == 'done':
            enriched_rows = [row for row in filtered_rows if row['survey_record']]

        page = self.paginate_queryset(enriched_rows)
        payload = page if page is not None else enriched_rows
        response = self.get_paginated_response(payload) if page is not None else Response({'results': payload, 'count': len(payload)})
        response.data['counts'] = base_counts
        response.data['filtered_counts'] = filtered_counts
        response.data['assignment_times'] = [
            {
                'value': value,
                'label': f"{meta['label'] or value} / {meta['count']} {'voter' if meta['count'] == 1 else 'voters'}",
                'count': meta['count'],
            }
            for value, meta in sorted(assignment_time_counts.items(), key=lambda item: item[0])
        ]
        return response


class TelecallingFeedbackViewSet(viewsets.ModelViewSet):
    screen_slug = 'feedback-review'
    view_permission_screen_slugs = ('field-activity', 'activity-report')
    queryset = TelecallingFeedback.objects.filter(is_active=True).select_related('survey')
    serializer_class = TelecallingFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['action', 'survey', 'followup_type']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    @action(detail=False, methods=['get'], url_path='review-list')
    def review_list(self, request):
        all_surveys = FieldSurvey.objects.filter(is_active=True)
        global_counts = _review_count_payload_from_surveys(all_surveys)
        scoped_surveys = (
            all_surveys
            .select_related('voter__booth')
            .order_by('-survey_date', '-created_at', '-id')
        )

        search = (request.query_params.get('search') or '').strip()
        if search:
            scoped_surveys = scoped_surveys.filter(
                Q(voter_name__icontains=search) |
                Q(surveyed_by__icontains=search) |
                Q(booth_no__icontains=search)
            )

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

        remarks_filter = (request.query_params.get('remarks') or '').strip().lower()
        if remarks_filter == 'commented':
            scoped_surveys = scoped_surveys.exclude(Q(remarks__isnull=True) | Q(remarks__exact=''))
        elif remarks_filter == 'uncommented':
            scoped_surveys = scoped_surveys.filter(Q(remarks__isnull=True) | Q(remarks__exact=''))

        booth = (request.query_params.get('booth') or '').strip()
        if booth:
            scoped_surveys = scoped_surveys.filter(booth_no=booth)

        date_from = (request.query_params.get('date_from') or '').strip()
        if date_from:
            scoped_surveys = scoped_surveys.filter(survey_date__gte=date_from)

        date_to = (request.query_params.get('date_to') or '').strip()
        if date_to:
            scoped_surveys = scoped_surveys.filter(survey_date__lte=date_to)

        scoped_surveys = _apply_location_filters(
            scoped_surveys,
            block=(request.query_params.get('block') or '').strip(),
            panchayat=(request.query_params.get('panchayat') or '').strip(),
            union=(request.query_params.get('union') or '').strip(),
        )

        telecaller_filter = (request.query_params.get('telecaller') or '').strip()
        scoped_surveys = _apply_telecaller_filter(scoped_surveys, telecaller_filter)

        filter_tab = (request.query_params.get('tab') or 'all').strip().lower()
        if filter_tab != 'all':
            latest_feedbacks = _latest_feedback_for_surveys(scoped_surveys)
            if filter_tab == 'pending':
                scoped_surveys = scoped_surveys.exclude(id__in=Subquery(latest_feedbacks.values('survey_id')))
            elif filter_tab == 'followup_required':
                scoped_surveys = scoped_surveys.filter(
                    id__in=Subquery(latest_feedbacks.filter(action='followup_required').values('survey_id'))
                )
            elif filter_tab == 'field_survey':
                scoped_surveys = scoped_surveys.filter(
                    id__in=Subquery(
                        latest_feedbacks.filter(
                            action='followup_required',
                            followup_type='field_survey',
                        ).values('survey_id')
                    )
                )
            elif filter_tab == 'telephonic':
                scoped_surveys = scoped_surveys.filter(
                    id__in=Subquery(
                        latest_feedbacks.filter(
                            action='followup_required',
                            followup_type='telephonic',
                        ).values('survey_id')
                    )
                )
            elif filter_tab == 'followup_not_required':
                scoped_surveys = scoped_surveys.filter(
                    id__in=Subquery(latest_feedbacks.filter(action='followup_not_required').values('survey_id'))
                )

        filtered_counts = _review_count_payload_from_surveys(scoped_surveys, include_followup_required_other=True)

        page = self.paginate_queryset(scoped_surveys)
        surveys = list(page) if page is not None else list(scoped_surveys)

        telecaller_by_voter, telecaller_by_name = _build_telecaller_lookup_for_surveys(surveys)
        detail_by_voter, detail_by_name = _build_assignment_detail_lookup_for_surveys(surveys)
        survey_ids = [survey.id for survey in surveys]
        latest_decisions = {}
        if survey_ids:
            page_surveys_qs = FieldSurvey.objects.filter(id__in=survey_ids)
            for decision in _latest_feedback_for_surveys(page_surveys_qs):
                latest_decisions[decision.survey_id] = decision

        results = []
        for survey in surveys:
            voter_obj = getattr(survey, 'voter', None)
            booth_obj = getattr(voter_obj, 'booth', None) if voter_obj else None
            normalized_name = (survey.voter_name or '').strip().lower()
            telecaller = (telecaller_by_voter.get(survey.voter_id) if survey.voter_id else None) or telecaller_by_name.get(normalized_name) or {}
            assignment_details = (detail_by_voter.get(survey.voter_id) if survey.voter_id else None) or detail_by_name.get(normalized_name) or {}
            decision = latest_decisions.get(survey.id)
            results.append({
                'id': survey.id,
                'voter_name': survey.voter_name or '',
                'voter_id_no': getattr(voter_obj, 'voter_id', '') or assignment_details.get('voter_id_no', ''),
                'phone': survey.phone or getattr(voter_obj, 'phone', '') or assignment_details.get('phone', ''),
                'phone2': getattr(voter_obj, 'phone2', '') or assignment_details.get('phone2', ''),
                'alt_phoneno2': getattr(voter_obj, 'alt_phoneno2', '') or assignment_details.get('alt_phoneno2', ''),
                'alt_phoneno3': getattr(voter_obj, 'alt_phoneno3', '') or assignment_details.get('alt_phoneno3', ''),
                'booth_no': survey.booth_no or '',
                'booth_name': getattr(booth_obj, 'name', '') or assignment_details.get('booth_name', ''),
                'block': survey.block or '',
                'village': survey.village or '',
                'age': survey.age if survey.age is not None else getattr(voter_obj, 'age', None) or assignment_details.get('age'),
                'gender': survey.gender or getattr(voter_obj, 'gender', '') or assignment_details.get('gender', ''),
                'address': survey.address or getattr(voter_obj, 'address', '') or assignment_details.get('address', ''),
                'support_level': survey.support_level or '',
                'party_preference': survey.party_preference or '',
                'response_status': survey.response_status or '',
                'aware_of_candidate': survey.aware_of_candidate or '',
                'likely_to_vote': survey.likely_to_vote or '',
                'remarks': survey.remarks or '',
                'surveyed_by': survey.surveyed_by or '',
                'survey_date': str(survey.survey_date) if survey.survey_date else '',
                'telecaller_name': telecaller.get('name', ''),
                'telecaller_phone': telecaller.get('phone', ''),
                'decision': {
                    'id': decision.id,
                    'action': decision.action,
                    'followup_type': decision.followup_type or '',
                    'date': str(decision.date) if decision.date else '',
                    'telecaller_name': decision.telecaller_name or '',
                } if decision else None,
            })

        response = (
            self.get_paginated_response(results)
            if page is not None
            else Response({'results': results, 'count': len(results)})
        )
        response.data['counts'] = global_counts
        response.data['filtered_counts'] = filtered_counts
        response.data['telecallers'] = sorted(
            [
                name
                for name in TelecallingAssignment.objects
                .filter(is_active=True)
                .values_list('telecaller_name', flat=True)
                .distinct()
                if name
            ],
            key=str.lower,
        )
        return response

    @action(detail=False, methods=['get'], url_path='timeline')
    def timeline(self, request):
        survey_id = request.query_params.get('survey')
        if not survey_id:
            return Response(
                {'detail': 'survey query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        survey = FieldSurvey.objects.filter(is_active=True, id=survey_id).first()
        if not survey:
            return Response({'detail': 'Survey not found'}, status=status.HTTP_404_NOT_FOUND)

        if survey.voter_id:
            survey_qs = FieldSurvey.objects.filter(is_active=True, voter_id=survey.voter_id)
            assignment_rows = TelecallingAssignmentVoter.objects.filter(voter_id=survey.voter_id).select_related('assignment')
        else:
            survey_qs = FieldSurvey.objects.filter(is_active=True, voter_name__iexact=survey.voter_name)
            assignment_rows = TelecallingAssignmentVoter.objects.filter(voter_name__iexact=survey.voter_name).select_related('assignment')

        all_surveys = list(survey_qs.order_by('survey_date', 'created_at'))
        survey_ids = [s.id for s in all_surveys]

        feedbacks = list(
            TelecallingFeedback.objects
            .filter(is_active=True, survey_id__in=survey_ids)
            .order_by('date', 'created_at', 'id')
        )

        if survey_ids:
            log_filter = Q()
            for sid in survey_ids:
                log_filter |= Q(notes__icontains=f"[survey_id:{sid}]")
            field_logs = list(
                ActivityLog.objects.filter(is_active=True, category='field').filter(log_filter)
            )
        else:
            field_logs = []

        events = []
        for row in assignment_rows:
            assignment = row.assignment
            events.append({
                'event_type': 'telephonic_assignment',
                'timestamp': assignment.created_at.isoformat() if assignment.created_at else '',
                'date': str(assignment.assigned_date),
                'user': assignment.telecaller_name or '',
                'remarks': f"Assigned for telecalling ({row.voter_name})",
            })

        for record in all_surveys:
            events.append({
                'event_type': 'telephonic_entry',
                'timestamp': record.created_at.isoformat() if record.created_at else '',
                'date': str(record.survey_date),
                'user': record.surveyed_by or '',
                'remarks': record.remarks or '',
            })

        for decision in feedbacks:
            decision_label = 'Follow-up Required' if decision.action == 'followup_required' else 'Follow-up Not Required'
            if decision.action == 'followup_required' and decision.followup_type:
                decision_label = f"{decision_label} ({'Telephonic' if decision.followup_type == 'telephonic' else 'Field Survey'})"
            events.append({
                'event_type': 'followup_event',
                'timestamp': decision.created_at.isoformat() if decision.created_at else '',
                'date': str(decision.date),
                'user': decision.telecaller_name or '',
                'remarks': decision_label,
            })

        for log in field_logs:
            notes = (log.notes or '').strip()
            events.append({
                'event_type': 'field_survey_entry',
                'timestamp': log.created_at.isoformat() if log.created_at else '',
                'date': str(log.date),
                'user': log.username or '',
                'remarks': notes,
            })

        def _sort_key(item):
            return item.get('timestamp') or ''

        events = sorted(events, key=_sort_key)
        final_status = 'Pending'
        if survey.voter_id:
            status_map = build_voter_status_map([survey.voter_id])
            status_info = status_map.get(survey.voter_id)
            if status_info:
                final_status = WORKFLOW_LABELS.get(status_info['status'], status_info['label'])
        elif feedbacks:
            latest = feedbacks[-1]
            final_status = 'Completed' if latest.action == 'followup_not_required' else 'Pending'

        return Response({
            'survey': survey.id,
            'voter_name': survey.voter_name,
            'final_status': final_status,
            'events': events,
        })
