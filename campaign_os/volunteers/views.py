"""
Views for volunteer management
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from campaign_os.volunteers.models import Volunteer, VolunteerTask, VolunteerAttendance
from campaign_os.volunteers.serializers import (
    VolunteerSerializer, VolunteerTaskSerializer, VolunteerAttendanceSerializer
)
from campaign_os.core.utils.bulk_upload import parse_upload, BulkResult, resolve_by_code, to_int, to_str


class VolunteerViewSet(viewsets.ModelViewSet):
    """Volunteer management"""
    queryset = Volunteer.objects.filter(is_active=True).select_related('user')
    serializer_class = VolunteerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['booth', 'status', 'ward']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

    @action(detail=False, methods=['GET'], url_path='names')
    def names(self, request):
        """Return minimal volunteer list for agent multiselect"""
        data = [
            {
                'id':        v.user_id,
                'user_name': v.user.get_full_name() or v.user.username,
                'phone':     getattr(v.user, 'phone', '') or '',
            }
            for v in self.get_queryset()
        ]
        return Response(data)

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
        POST /api/v1/volunteers/volunteers/bulk-upload/
        Multipart field: file (.csv or .xlsx)

        CSV columns:
          username (required), first_name, last_name, phone,
          booth_code, ward_code, volunteer_type, role, skills,
          block, gender, age, notes
        """
        from campaign_os.accounts.models import User
        from campaign_os.masters.models import Booth, Ward

        rows, err = parse_upload(request)
        if err:
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)

        result = BulkResult()
        for i, row in enumerate(rows, start=2):
            username = to_str(row.get('username'))
            if not username:
                result.fail(i, 'username is required')
                continue
            try:
                user, _ = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': to_str(row.get('first_name')),
                        'last_name':  to_str(row.get('last_name')),
                        'phone':      to_str(row.get('phone')) or None,
                        'role':       'volunteer',
                    }
                )
                booth_id = resolve_by_code(Booth, row.get('booth_code', ''))
                ward_id  = resolve_by_code(Ward,  row.get('ward_code',  ''))

                _, created = Volunteer.objects.get_or_create(
                    user=user,
                    defaults={
                        'booth_id':       booth_id,
                        'ward_id':        ward_id,
                        'volunteer_type': to_str(row.get('volunteer_type')) or None,
                        'role':           to_str(row.get('role'))           or None,
                        'skills':         to_str(row.get('skills'))         or None,
                        'block':          to_str(row.get('block'))          or None,
                        'gender':         to_str(row.get('gender'))         or None,
                        'age':            to_int(row.get('age')),
                        'notes':          to_str(row.get('notes'))          or None,
                    }
                )
                result.ok(created)
            except Exception as exc:
                result.fail(i, str(exc))

        return Response(result.summary(), status=status.HTTP_200_OK)


class VolunteerTaskViewSet(viewsets.ModelViewSet):
    queryset = VolunteerTask.objects.filter(is_active=True)
    serializer_class = VolunteerTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['volunteer', 'status', 'assignment_type']
    search_fields = ['title']
    ordering = ['-due_date']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class VolunteerAttendanceViewSet(viewsets.ModelViewSet):
    queryset = VolunteerAttendance.objects.all()
    serializer_class = VolunteerAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['volunteer', 'date']
    ordering = ['-date']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
