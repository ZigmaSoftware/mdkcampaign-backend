import re

from django.db.models import Prefetch, Q, Count
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from campaign_os.activities.models import ActivityLog, FieldSurvey
from campaign_os.core.permissions import ScreenPermission
from campaign_os.masters.models import Booth

from .models import TelecallingAssignment, TelecallingAssignmentVoter, TelecallingFeedback
from .serializers import TelecallingAssignmentSerializer, TelecallingFeedbackSerializer
from .workflow import WORKFLOW_LABELS, build_voter_status_map


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

    survey_qs = FieldSurvey.objects.filter(is_active=True).order_by('-survey_date', '-created_at', '-id')
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
    voter_names = {survey.voter_name.strip().lower() for survey in surveys if survey.voter_name}

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
        scoped_assignments = list(self.get_queryset())
        assignment_time = (request.query_params.get('assignment_time') or '').strip()

        assignment_time_counts = {}
        for assignment in scoped_assignments:
            time_value = _assignment_time_value(assignment)
            if time_value:
                bucket = assignment_time_counts.setdefault(time_value, {
                    'count': 0,
                    'label': _assignment_time_label(assignment),
                })
                bucket['count'] += len(assignment.voters.all())

        assignments = scoped_assignments
        if assignment_time:
            assignments = [
                assignment for assignment in scoped_assignments
                if assignment.created_at and _assignment_time_value(assignment) == assignment_time
            ]

        flat_rows = []
        for assignment in assignments:
            for voter in assignment.voters.all():
                flat_rows.append({
                    'assignment_id': assignment.id,
                    'id': voter.id,
                    'voter': voter.voter_id,
                    'voter_name': voter.voter_name or '',
                    'voter_id_no': voter.voter_id_no or '',
                    'phone': voter.phone or '',
                    'address': voter.address or '',
                    'booth_name': voter.booth_name or '',
                    'booth_no': getattr(getattr(voter, 'voter', None), 'booth', None).number if getattr(getattr(voter, 'voter', None), 'booth', None) else '',
                    'age': voter.age,
                    'gender': voter.gender or '',
                    'telecaller_id': assignment.telecaller_id,
                    'telecaller_name': assignment.telecaller_name or '',
                    'telecaller_phone': assignment.telecaller_phone or '',
                    'assigned_date': str(assignment.assigned_date),
                    'assignment_time': time_value,
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
        global_surveys = list(FieldSurvey.objects.filter(is_active=True).order_by('-survey_date', '-created_at', '-id'))
        global_feedbacks = list(
            TelecallingFeedback.objects
            .filter(is_active=True, survey__isnull=False)
            .select_related('survey')
            .order_by('-date', '-created_at', '-id')
        )
        latest_feedback_by_survey = _latest_feedback_map(global_feedbacks)

        global_counts = {
            'all': len(global_surveys),
            'pending': sum(1 for survey in global_surveys if survey.id not in latest_feedback_by_survey),
            'followup_required': sum(1 for feedback in latest_feedback_by_survey.values() if feedback.action == 'followup_required'),
            'field_survey': sum(1 for feedback in latest_feedback_by_survey.values() if feedback.action == 'followup_required' and feedback.followup_type == 'field_survey'),
            'telephonic': sum(1 for feedback in latest_feedback_by_survey.values() if feedback.action == 'followup_required' and feedback.followup_type == 'telephonic'),
            'followup_not_required': sum(1 for feedback in latest_feedback_by_survey.values() if feedback.action == 'followup_not_required'),
        }

        surveys = list(global_surveys)

        search = (request.query_params.get('search') or '').strip().lower()
        if search:
            surveys = [
                survey for survey in surveys
                if search in (survey.voter_name or '').lower()
                or search in (survey.surveyed_by or '').lower()
                or search in (survey.booth_no or '').lower()
            ]

        support_level = (request.query_params.get('support_level') or '').strip()
        if support_level:
            surveys = [survey for survey in surveys if (survey.support_level or '') == support_level]

        response_status = (request.query_params.get('response_status') or '').strip()
        if response_status:
            surveys = [survey for survey in surveys if (survey.response_status or '') == response_status]

        aware_of_candidate = (request.query_params.get('aware_of_candidate') or '').strip()
        if aware_of_candidate:
            surveys = [survey for survey in surveys if (survey.aware_of_candidate or '') == aware_of_candidate]

        likely_to_vote = (request.query_params.get('likely_to_vote') or '').strip()
        if likely_to_vote:
            surveys = [survey for survey in surveys if (survey.likely_to_vote or '') == likely_to_vote]

        party = (request.query_params.get('party') or '').strip()
        if party:
            surveys = [survey for survey in surveys if (survey.party_preference or '') == party]

        block = (request.query_params.get('block') or '').strip()
        if block:
            surveys = [survey for survey in surveys if (survey.block or '') == block]

        booth = (request.query_params.get('booth') or '').strip()
        if booth:
            surveys = [survey for survey in surveys if (survey.booth_no or '') == booth]

        date_from = (request.query_params.get('date_from') or '').strip()
        if date_from:
            surveys = [survey for survey in surveys if str(survey.survey_date) >= date_from]

        date_to = (request.query_params.get('date_to') or '').strip()
        if date_to:
            surveys = [survey for survey in surveys if str(survey.survey_date) <= date_to]

        booth_map = _survey_location_maps(surveys)
        panchayat = (request.query_params.get('panchayat') or '').strip()
        if panchayat:
            surveys = [survey for survey in surveys if (booth_map.get(survey.booth_no or '', {}).get('panchayat') or '') == panchayat]

        union = (request.query_params.get('union') or '').strip()
        if union:
            surveys = [survey for survey in surveys if (booth_map.get(survey.booth_no or '', {}).get('union') or '') == union]

        telecaller_by_voter, telecaller_by_name = _build_telecaller_lookup_for_surveys(surveys)

        telecaller_filter = (request.query_params.get('telecaller') or '').strip()
        if telecaller_filter:
            surveys = [
                survey for survey in surveys
                if (
                    (telecaller_by_voter.get(survey.voter_id) if survey.voter_id else None) or
                    telecaller_by_name.get((survey.voter_name or '').strip().lower())
                ) and (
                    ((telecaller_by_voter.get(survey.voter_id) if survey.voter_id else None) or telecaller_by_name.get((survey.voter_name or '').strip().lower()) or {}).get('name', '')
                ) == telecaller_filter
            ]

        filter_tab = (request.query_params.get('tab') or 'all').strip().lower()
        if filter_tab != 'all':
            filtered = []
            for survey in surveys:
                decision = latest_feedback_by_survey.get(survey.id)
                if filter_tab == 'pending' and not decision:
                    filtered.append(survey)
                elif filter_tab == 'followup_required' and decision and decision.action == 'followup_required':
                    filtered.append(survey)
                elif filter_tab == 'field_survey' and decision and decision.action == 'followup_required' and decision.followup_type == 'field_survey':
                    filtered.append(survey)
                elif filter_tab == 'telephonic' and decision and decision.action == 'followup_required' and decision.followup_type == 'telephonic':
                    filtered.append(survey)
                elif filter_tab == 'followup_not_required' and decision and decision.action == 'followup_not_required':
                    filtered.append(survey)
            surveys = filtered

        filtered_counts = {
            'all': len(surveys),
            'pending': sum(1 for survey in surveys if survey.id not in latest_feedback_by_survey),
            'followup_required': sum(
                1 for survey in surveys
                if latest_feedback_by_survey.get(survey.id)
                and latest_feedback_by_survey[survey.id].action == 'followup_required'
            ),
            'field_survey': sum(
                1 for survey in surveys
                if latest_feedback_by_survey.get(survey.id)
                and latest_feedback_by_survey[survey.id].action == 'followup_required'
                and latest_feedback_by_survey[survey.id].followup_type == 'field_survey'
            ),
            'telephonic': sum(
                1 for survey in surveys
                if latest_feedback_by_survey.get(survey.id)
                and latest_feedback_by_survey[survey.id].action == 'followup_required'
                and latest_feedback_by_survey[survey.id].followup_type == 'telephonic'
            ),
            'followup_required_other': sum(
                1 for survey in surveys
                if latest_feedback_by_survey.get(survey.id)
                and latest_feedback_by_survey[survey.id].action == 'followup_required'
                and not latest_feedback_by_survey[survey.id].followup_type
            ),
            'followup_not_required': sum(
                1 for survey in surveys
                if latest_feedback_by_survey.get(survey.id)
                and latest_feedback_by_survey[survey.id].action == 'followup_not_required'
            ),
        }

        results = []
        for survey in surveys:
            telecaller = (telecaller_by_voter.get(survey.voter_id) if survey.voter_id else None) or telecaller_by_name.get((survey.voter_name or '').strip().lower()) or {}
            decision = latest_feedback_by_survey.get(survey.id)
            results.append({
                'id': survey.id,
                'voter_name': survey.voter_name or '',
                'phone': survey.phone or '',
                'booth_no': survey.booth_no or '',
                'block': survey.block or '',
                'village': survey.village or '',
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
                    'date': str(decision.date),
                    'telecaller_name': decision.telecaller_name or '',
                } if decision else None,
            })

        page = self.paginate_queryset(results)
        payload = page if page is not None else results
        response = self.get_paginated_response(payload) if page is not None else Response({'results': payload, 'count': len(payload)})
        response.data['counts'] = global_counts
        response.data['filtered_counts'] = filtered_counts
        response.data['telecallers'] = sorted(
            [name for name in TelecallingAssignment.objects.filter(is_active=True).values_list('telecaller_name', flat=True).distinct() if name],
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
