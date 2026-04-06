"""
Attendance views — punch-in / punch-out / report
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q, Avg
from datetime import date, timedelta
from .models import Attendance
from .serializers import AttendanceSerializer, AttendanceReportSerializer
from campaign_os.core.permissions import ScreenPermission


class AttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Attendance management.
    POST /attendance/punch-in/
    POST /attendance/punch-out/
    GET  /attendance/today/
    GET  /attendance/report/
    GET  /attendance/my_history/
    """
    screen_slug = 'attendance'
    view_permission_screen_slugs = ('activity-report',)
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated, ScreenPermission]
    filterset_fields = ['user', 'attendance_date', 'status']
    ordering = ['-attendance_date']

    def get_queryset(self):
        user = self.request.user
        if user.role in ('admin', 'district_head', 'constituency_mgr'):
            return Attendance.objects.all()
        return Attendance.objects.filter(user=user)

    # ── Punch-In ──────────────────────────────────────────────
    @action(detail=False, methods=['POST'], url_path='punch-in')
    def punch_in(self, request):
        user  = request.user
        today = timezone.localtime(timezone.now()).date()
        now   = timezone.now()

        # Prevent future timestamps
        if now > timezone.now() + timedelta(minutes=5):
            return Response(
                {'detail': 'Cannot punch-in with a future timestamp.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent duplicate punch-in on same day
        if Attendance.objects.filter(user=user, attendance_date=today).exists():
            return Response(
                {'detail': 'Already punched in for today. Use punch-out to complete.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record = Attendance.objects.create(
            user=user,
            punch_in=now,
            attendance_date=today,
            status='INCOMPLETE',
            notes=request.data.get('notes', ''),
        )
        return Response(AttendanceSerializer(record).data, status=status.HTTP_201_CREATED)

    # ── Punch-Out ─────────────────────────────────────────────
    @action(detail=False, methods=['POST'], url_path='punch-out')
    def punch_out(self, request):
        user  = request.user
        today = timezone.localtime(timezone.now()).date()
        now   = timezone.now()

        try:
            record = Attendance.objects.get(user=user, attendance_date=today)
        except Attendance.DoesNotExist:
            return Response(
                {'detail': 'No punch-in found for today. Please punch in first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if record.punch_out is not None:
            return Response(
                {'detail': 'Already punched out for today.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if now < record.punch_in:
            return Response(
                {'detail': 'Punch-out time cannot be before punch-in time.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record.punch_out = now
        if request.data.get('notes'):
            record.notes = request.data['notes']
        record.save()  # triggers status=PRESENT + work hours calc

        return Response(AttendanceSerializer(record).data)

    # ── Today Status ──────────────────────────────────────────
    @action(detail=False, methods=['GET'], url_path='today')
    def today(self, request):
        today = timezone.localtime(timezone.now()).date()
        try:
            record = Attendance.objects.get(user=request.user, attendance_date=today)
            return Response(AttendanceSerializer(record).data)
        except Attendance.DoesNotExist:
            return Response({
                'status': 'ABSENT',
                'attendance_date': str(today),
                'punch_in': None,
                'punch_out': None,
                'total_work_hours': '0.00',
                'message': 'No attendance record for today.',
            })

    # ── My History ────────────────────────────────────────────
    @action(detail=False, methods=['GET'], url_path='my-history')
    def my_history(self, request):
        records = Attendance.objects.filter(user=request.user).order_by('-attendance_date')[:30]
        return Response(AttendanceSerializer(records, many=True).data)

    # ── Report ────────────────────────────────────────────────
    @action(detail=False, methods=['GET'], url_path='report')
    def report(self, request):
        """
        Attendance report with filters.
        Query params:
          - date_from  (YYYY-MM-DD)
          - date_to    (YYYY-MM-DD)
          - user_id
          - status     (PRESENT / INCOMPLETE / ABSENT)
        Admin/manager sees all; others see only their own.
        """
        user = request.user
        qs   = self.get_queryset()

        date_from = request.query_params.get('date_from')
        date_to   = request.query_params.get('date_to')
        user_id   = request.query_params.get('user_id')
        stat      = request.query_params.get('status')

        if date_from:
            qs = qs.filter(attendance_date__gte=date_from)
        if date_to:
            qs = qs.filter(attendance_date__lte=date_to)
        if user_id and user.role in ('admin', 'district_head', 'constituency_mgr'):
            qs = qs.filter(user_id=user_id)
        if stat:
            qs = qs.filter(status=stat.upper())

        summary = {
            'total_records': qs.count(),
            'present':       qs.filter(status='PRESENT').count(),
            'incomplete':    qs.filter(status='INCOMPLETE').count(),
            'avg_work_hours': float(qs.filter(status='PRESENT').aggregate(avg=Avg('total_work_hours'))['avg'] or 0),
        }

        serializer = AttendanceReportSerializer(qs.order_by('-attendance_date'), many=True)
        return Response({
            'summary': summary,
            'records': serializer.data,
        })

    # ── Admin: Mark Absent ────────────────────────────────────
    @action(detail=False, methods=['POST'], url_path='mark-absent')
    def mark_absent(self, request):
        """Auto-mark ABSENT for users who have no record for a given date. Admin only."""
        if request.user.role != 'admin':
            return Response({'detail': 'Admin only.'}, status=status.HTTP_403_FORBIDDEN)

        target_date = request.data.get('date')
        if not target_date:
            return Response({'detail': 'date field required (YYYY-MM-DD).'}, status=status.HTTP_400_BAD_REQUEST)

        from campaign_os.accounts.models import User
        all_users = User.objects.filter(is_active=True)
        present_user_ids = set(
            Attendance.objects.filter(attendance_date=target_date).values_list('user_id', flat=True)
        )
        absent_users = all_users.exclude(id__in=present_user_ids)
        created = 0
        for u in absent_users:
            Attendance.objects.get_or_create(
                user=u,
                attendance_date=target_date,
                defaults={
                    'punch_in': timezone.make_aware(
                        timezone.datetime.combine(
                            date.fromisoformat(str(target_date)),
                            timezone.datetime.min.time()
                        )
                    ),
                    'status': 'ABSENT',
                },
            )
            created += 1

        return Response({'detail': f'Marked {created} users as ABSENT for {target_date}.'})
