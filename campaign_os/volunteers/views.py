"""
Views for volunteer management
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django.db.models import Q
from django.db.models.functions import Trim
from campaign_os.masters.models import VolunteerRole
from campaign_os.volunteers.models import Volunteer, VolunteerTask, VolunteerAttendance
from campaign_os.volunteers.serializers import (
    VolunteerSerializer, VolunteerTaskSerializer, VolunteerAttendanceSerializer
)
from campaign_os.core.utils.bulk_upload import parse_upload, BulkResult, resolve_by_code, to_int, to_str
from campaign_os.core.permissions import ScreenPermission


class VolunteerViewSet(viewsets.ModelViewSet):
    """Volunteer management"""
    screen_slug = 'volunteer'
    view_permission_screen_slugs = ('volunteer-report',)
    queryset = Volunteer.objects.filter(is_active=True).select_related(
        'user', 'booth__panchayat__union__block', 'volunteer_role'
    ).prefetch_related('booths__panchayat__union')
    serializer_class = VolunteerSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['booth', 'status', 'ward']

    def get_permissions(self):
        # Allow the 'names' action for any authenticated user (used by task form)
        if self.action in {'names', 'lookup'}:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def _filter_by_role(self, qs, role):
        role = (role or '').strip()
        if not role:
            return qs

        normalized_role = ''.join(ch for ch in role.lower() if ch.isalnum())
        if normalized_role in {'telecalling', 'telecaller'}:
            return qs.filter(
                Q(role__icontains='telecall') |
                Q(role__icontains='tele call') |
                Q(volunteer_role__name__icontains='telecall') |
                Q(volunteer_role__name__icontains='tele call') |
                Q(volunteer_type__icontains='telecall') |
                Q(volunteer_type__icontains='tele call')
            )

        return qs.filter(
            Q(role__iexact=role) |
            Q(volunteer_role__name__iexact=role)
        )

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        search    = params.get('search',    '').strip()
        block     = params.get('block',     '').strip()
        panchayat = params.get('panchayat', '').strip()
        union     = params.get('union',     '').strip()
        if search:
            q = (
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(phone2__icontains=search) |
                Q(voter_id__icontains=search) |
                Q(role__icontains=search) |
                Q(block__icontains=search) |
                Q(skills__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__username__icontains=search) |
                Q(booth__panchayat__name__icontains=search) |
                Q(booth__panchayat__union__name__icontains=search) |
                Q(booth__panchayat__union__block__name__icontains=search)
            )
            if search.isdigit():
                q |= Q(age=int(search))
            qs = qs.filter(q)
        if block:
            qs = qs.filter(block__iexact=block)
        if panchayat:
            qs = qs.filter(booth__panchayat__name__iexact=panchayat)
        if union:
            qs = qs.filter(booth__panchayat__union__name__iexact=union)

        # Age group filter: ?age_group=18-25 or ?age_group=18-25,26-35
        age_group_param = params.get('age_group', '').strip()
        if age_group_param:
            from campaign_os.core.utils.age_utils import build_age_filter
            age_q = build_age_filter(age_group_param)
            if age_q:
                qs = qs.filter(age_q)

        # Voter ID filter: ?voter_id_status=with|without
        voter_id_status = params.get('voter_id_status', '').strip().lower()
        if voter_id_status:
            qs = qs.annotate(trimmed_voter_id=Trim('voter_id'))
            has_voter_id_q = Q(trimmed_voter_id__isnull=False) & ~Q(trimmed_voter_id='')
            if voter_id_status in {'with', 'yes', 'true', '1'}:
                qs = qs.filter(has_voter_id_q)
            elif voter_id_status in {'without', 'no', 'false', '0'}:
                qs = qs.exclude(has_voter_id_q)

        role = params.get('role', '').strip()
        if role and self.action != 'names':
            qs = self._filter_by_role(qs, role)

        status_param = params.get('status', '').strip().lower()
        if status_param:
            qs = qs.filter(status=status_param)

        volunteer_type = params.get('volunteer_type', '').strip()
        if volunteer_type:
            qs = qs.filter(volunteer_type__iexact=volunteer_type)

        gender = params.get('gender', '').strip()
        if gender:
            qs = qs.filter(gender__iexact=gender)

        source = params.get('source', '').strip()
        if source:
            qs = qs.filter(source__iexact=source)

        return qs

    @action(detail=False, methods=['GET'], url_path='names')
    def names(self, request):
        """
        Return minimal volunteer list for dropdowns.
        Filters:
          ?role=<role_name>      — match Volunteer.role (legacy CharField)
          ?role_id=<id>          — match Volunteer.volunteer_role FK id
          ?volunteer_role=<name> — match VolunteerRole.name (iexact)
        """
        qs = self.get_queryset()
        role = request.query_params.get('role', '').strip()
        role_id = request.query_params.get('role_id', '').strip()
        vol_role = request.query_params.get('volunteer_role', '').strip()
        if role_id:
            filtered = qs.filter(volunteer_role_id=role_id)
            if filtered.exists():
                qs = filtered
            # else: fallback to all volunteers (role not yet tagged)
        elif vol_role:
            filtered = self._filter_by_role(qs, vol_role)
            if filtered.exists():
                qs = filtered
        elif role:
            filtered = self._filter_by_role(qs, role)
            if filtered.exists():
                qs = filtered
        data = []
        for v in qs:
            if v.name:
                vol_name = v.name
                phone    = v.phone or ''
            elif v.user_id:
                vol_name = v.user.get_full_name() or v.user.username
                phone    = getattr(v.user, 'phone', '') or v.phone or ''
            else:
                vol_name = f'Volunteer #{v.id}'
                phone    = v.phone or ''
            data.append({
                'id':      v.id,
                'user_id': v.user_id,
                'user_name': vol_name,
                'phone':   phone,
                'role':    v.role or '',
            })
        return Response(data)

    @action(detail=False, methods=['GET'], url_path='lookup')
    def lookup(self, request):
        search = request.query_params.get('search', '').strip()
        role_id = request.query_params.get('role_id', '').strip()
        role = request.query_params.get('role', '').strip()
        status_param = request.query_params.get('status', '').strip().lower()

        try:
            limit = int(request.query_params.get('limit', 20))
        except (TypeError, ValueError):
            limit = 20
        limit = max(1, min(limit, 50))

        qs = Volunteer.objects.filter(is_active=True).select_related('user', 'volunteer_role')

        if status_param:
            qs = qs.filter(status=status_param)
        if role_id:
            filtered = qs.filter(volunteer_role_id=role_id)
            role_obj = VolunteerRole.objects.filter(id=role_id, is_active=True).only('name').first()
            if role_obj and role_obj.name:
                legacy_or_named = self._filter_by_role(qs, role_obj.name)
                qs = (filtered | legacy_or_named).distinct()
            else:
                qs = filtered
        elif role:
            qs = self._filter_by_role(qs, role)

        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(phone2__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__username__icontains=search)
            )

        qs = qs.order_by('name', 'user__first_name', 'user__last_name', 'id')
        total = qs.count()
        rows = qs[:limit]
        data = []
        for v in rows:
            if v.name:
                vol_name = v.name
            elif v.user_id:
                vol_name = v.user.get_full_name() or v.user.username
            else:
                vol_name = f'Volunteer #{v.id}'

            phone = v.phone or getattr(v.user, 'phone', '') or ''
            role_name = getattr(v.volunteer_role, 'name', '') or v.role or ''
            label = f'{vol_name} ({phone})' if phone else vol_name
            data.append({
                'id': v.id,
                'user_name': vol_name,
                'phone': phone,
                'label': label,
                'role': role_name,
                'volunteer_role': v.volunteer_role_id,
                'volunteer_role_name': getattr(v.volunteer_role, 'name', ''),
            })

        return Response({'count': total, 'results': data})

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
    view_permission_screen_slugs = ('campaign-report',)
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
    view_permission_screen_slugs = ('activity-report',)
    queryset = VolunteerAttendance.objects.all()
    serializer_class = VolunteerAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['volunteer', 'date']
    ordering = ['-date']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
