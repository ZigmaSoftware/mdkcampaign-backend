"""
Views for campaigns and events
"""
from django.http import HttpResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from campaign_os.campaigns.models import CampaignEvent, EventAttendee, Task
from campaign_os.campaigns.serializers import CampaignEventSerializer, EventAttendeeSerializer, TaskSerializer
from campaign_os.core.utils.bulk_upload import parse_upload, BulkResult, resolve_by_code, to_str, to_int


class CampaignEventViewSet(viewsets.ModelViewSet):
    queryset = CampaignEvent.objects.filter(is_active=True)
    serializer_class = CampaignEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['constituency', 'event_type', 'status', 'scheduled_date']
    search_fields = ['title', 'location']
    ordering_fields = ['scheduled_date', 'created_at']
    ordering = ['scheduled_date']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    # ── bulk upload ──────────────────────────────────────────────────────────
    @action(detail=False, methods=['POST'], url_path='bulk-upload',
            parser_classes=[MultiPartParser])
    def bulk_upload(self, request):
        """
        POST /api/v1/campaigns/events/bulk-upload/
        Multipart field: file (.csv or .xlsx)

        CSV columns:
          title (required), event_type, constituency_code, ward_code,
          scheduled_date (YYYY-MM-DD), scheduled_time (HH:MM), location,
          expected_attendees, status, description
        """
        from campaign_os.masters.models import Constituency, Ward

        rows, err = parse_upload(request)
        if err:
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)

        result = BulkResult()
        for i, row in enumerate(rows, start=2):
            title = to_str(row.get('title'))
            if not title:
                result.fail(i, 'title is required')
                continue
            try:
                const_id = resolve_by_code(Constituency, row.get('constituency_code', ''))
                ward_id  = resolve_by_code(Ward,         row.get('ward_code', ''))

                obj, created = CampaignEvent.objects.get_or_create(
                    title=title,
                    scheduled_date=to_str(row.get('scheduled_date')) or None,
                    defaults={
                        'event_type':          to_str(row.get('event_type'))       or None,
                        'constituency_id':     const_id,
                        'ward_id':             ward_id,
                        'scheduled_time':      to_str(row.get('scheduled_time'))   or None,
                        'location':            to_str(row.get('location'))         or None,
                        'expected_attendees':  to_int(row.get('expected_attendees')),
                        'status':              to_str(row.get('status'))           or 'planned',
                        'description':         to_str(row.get('description'))      or None,
                        'created_by':          request.user,
                    }
                )
                result.ok(created)
            except Exception as exc:
                result.fail(i, str(exc))

        return Response(result.summary(), status=status.HTTP_200_OK)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.filter(is_active=True).select_related(
        'delivery_incharge', 'coordinator', 'task_category'
    )
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'category', 'task_category']
    search_fields = ['title', 'venue']
    ordering_fields = ['expected_datetime', 'created_at']
    ordering = ['expected_datetime']

    def get_queryset(self):
        qs = super().get_queryset()
        date_from = self.request.query_params.get('date_from')
        date_to   = self.request.query_params.get('date_to')
        if date_from:
            qs = qs.filter(expected_datetime__date__gte=date_from)
        if date_to:
            qs = qs.filter(expected_datetime__date__lte=date_to)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    @action(detail=False, methods=['GET'], url_path='export')
    def export(self, request):
        """
        GET /api/v1/campaigns/tasks/export/
        Returns tasks as a printable HTML table.
        Supports the same filters: ?status=pending&category=logistics
        Add ?download=1 to force file download instead of browser render.
        """
        qs = self.filter_queryset(self.get_queryset())

        def user_name(u):
            return (u.get_full_name() or u.username) if u else '—'

        def fmt_dt(dt):
            return dt.strftime('%Y-%m-%d %H:%M') if dt else '—'

        headers = [
            'S.No',
            'Task Title',
            'Task Category',
            'Details',
            'Expected Delivery Date & Time',
            'Venue',
            'Delivery Incharge',
            'Coordinator',
            'Qty',
            'Status',
            'Completed Date & Time',
            'Notes',
        ]

        rows = []
        for idx, task in enumerate(qs, start=1):
            rows.append([
                idx,
                task.title or '—',
                task.task_category.name if task.task_category_id else (task.get_category_display() if task.category else '—'),
                task.details or '—',
                fmt_dt(task.expected_datetime),
                task.venue or '—',
                user_name(task.delivery_incharge),
                user_name(task.coordinator),
                task.qty if task.qty is not None else '—',
                task.get_status_display() if task.status else '—',
                fmt_dt(task.completed_datetime),
                task.notes or '—',
            ])

        th_cells = ''.join(f'<th>{h}</th>' for h in headers)

        td_rows = ''
        for row in rows:
            cells = ''.join(f'<td>{cell}</td>' for cell in row)
            td_rows += f'<tr>{cells}</tr>\n'

        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Task Management Export</title>
  <style>
    body {{ font-family: Arial, sans-serif; font-size: 13px; margin: 20px; }}
    h2   {{ margin-bottom: 12px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 8px 10px; text-align: left; white-space: nowrap; }}
    th {{ background: #4a6fa5; color: #fff; }}
    tr:nth-child(even) {{ background: #f5f7fa; }}
  </style>
</head>
<body>
  <h2>Task Management</h2>
  <table>
    <thead><tr>{th_cells}</tr></thead>
    <tbody>{td_rows}</tbody>
  </table>
</body>
</html>"""

        response = HttpResponse(html, content_type='text/html; charset=utf-8')
        if request.query_params.get('download'):
            response['Content-Disposition'] = 'attachment; filename="tasks.html"'
        return response


class EventAttendeeViewSet(viewsets.ModelViewSet):
    queryset = EventAttendee.objects.filter(is_active=True)
    serializer_class = EventAttendeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['event', 'attendee_type', 'sentiment']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
