"""
Views for campaigns and events
"""
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
        'delivery_incharge', 'coordinator'
    )
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'category']
    search_fields = ['title', 'venue']
    ordering_fields = ['expected_datetime', 'created_at']
    ordering = ['expected_datetime']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


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
