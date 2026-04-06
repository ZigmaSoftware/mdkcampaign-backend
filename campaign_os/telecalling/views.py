from django.db.models import Prefetch, Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from campaign_os.activities.models import ActivityLog, FieldSurvey
from campaign_os.core.permissions import ScreenPermission

from .models import TelecallingAssignment, TelecallingAssignmentVoter, TelecallingFeedback
from .serializers import TelecallingAssignmentSerializer, TelecallingFeedbackSerializer
from .workflow import WORKFLOW_LABELS, build_voter_status_map


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
            return self.get_paginated_response(serializer.data)
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
