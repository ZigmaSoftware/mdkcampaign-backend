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
from campaign_os.core.permissions import ScreenPermission


class VolunteerViewSet(viewsets.ModelViewSet):
    """Volunteer management"""
    screen_slug = 'volunteer'
    queryset = Volunteer.objects.filter(is_active=True).select_related('user')
    serializer_class = VolunteerSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['booth', 'status', 'ward']
    search_fields = ['name', 'user__username', 'user__first_name', 'user__last_name']

    @action(detail=False, methods=['GET'], url_path='names')
    def names(self, request):
        """Return minimal volunteer list for agent/booth dropdown"""
        data = []
        for v in self.get_queryset():
            if v.name:
                vol_name = v.name
                phone    = v.phone or ''
            elif v.user_id:
                vol_name = v.user.get_full_name() or v.user.username
                phone    = getattr(v.user, 'phone', '') or v.phone or ''
            else:
                vol_name = f'Volunteer #{v.id}'
                phone    = v.phone or ''
            data.append({'id': v.id, 'user_name': vol_name, 'phone': phone})
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
          name (required), phone, alt_phone,
          booth_code, ward_code, volunteer_type, role, skills,
          block, gender, age, notes, status
        """
        from campaign_os.masters.models import Booth, Ward

        rows, err = parse_upload(request)
        if err:
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)

        result = BulkResult()
        for i, row in enumerate(rows, start=2):
            name = to_str(row.get('name'))
            if not name:
                result.fail(i, 'name is required')
                continue
            try:
                ward_id = resolve_by_code(Ward, row.get('ward_code', ''))

                # Parse comma-separated booth codes e.g. "1, 2, 3" or "B001,B002"
                raw_codes = to_str(row.get('booth_code', '')) or ''
                booth_codes = [bc.strip() for bc in raw_codes.split(',') if bc.strip()]
                booth_ids = [bid for bc in booth_codes if (bid := resolve_by_code(Booth, bc))]
                primary_booth_id = booth_ids[0] if booth_ids else None

                vol, created = Volunteer.objects.get_or_create(
                    name=name,
                    defaults={
                        'voter_id':       to_str(row.get('voter_id'))        or None,
                        'phone':          to_str(row.get('phone'))           or None,
                        'phone2':         to_str(row.get('alt_phone'))       or None,
                        'booth_id':       primary_booth_id,
                        'ward_id':        ward_id,
                        'volunteer_type': to_str(row.get('volunteer_type')) or None,
                        'role':           to_str(row.get('role'))           or None,
                        'skills':         to_str(row.get('skills'))         or None,
                        'block':          to_str(row.get('block'))          or None,
                        'gender':         to_str(row.get('gender'))         or None,
                        'age':            to_int(row.get('age')),
                        'notes':          to_str(row.get('notes'))          or None,
                        'status':         to_str(row.get('status'))         or 'active',
                    }
                )
                if booth_ids:
                    vol.booths.set(booth_ids)
                result.ok(created)
            except Exception as exc:
                result.fail(i, str(exc))

        return Response(result.summary(), status=status.HTTP_200_OK)


class VolunteerTaskViewSet(viewsets.ModelViewSet):
    screen_slug = 'event'
    queryset = VolunteerTask.objects.filter(is_active=True)
    serializer_class = VolunteerTaskSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
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
    screen_slug = 'attendance'
    queryset = VolunteerAttendance.objects.all()
    serializer_class = VolunteerAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['volunteer', 'date']
    ordering = ['-date']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
