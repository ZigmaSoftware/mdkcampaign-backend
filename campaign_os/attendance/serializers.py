"""
Attendance serializers
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    username     = serializers.CharField(source='user.username',       read_only=True)
    full_name    = serializers.CharField(source='user.get_full_name',  read_only=True)
    role         = serializers.CharField(source='user.role',           read_only=True)
    punch_in_time  = serializers.SerializerMethodField()
    punch_out_time = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            'id', 'user', 'username', 'full_name', 'role',
            'attendance_date', 'punch_in', 'punch_out',
            'punch_in_time', 'punch_out_time',
            'status', 'total_work_hours', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'status', 'total_work_hours', 'created_at', 'updated_at']

    def get_punch_in_time(self, obj):
        if obj.punch_in:
            local = timezone.localtime(obj.punch_in)
            return local.strftime('%H:%M:%S')
        return None

    def get_punch_out_time(self, obj):
        if obj.punch_out:
            local = timezone.localtime(obj.punch_out)
            return local.strftime('%H:%M:%S')
        return None


class AttendanceReportSerializer(serializers.ModelSerializer):
    username  = serializers.CharField(source='user.username',       read_only=True)
    full_name = serializers.CharField(source='user.get_full_name',  read_only=True)
    role      = serializers.CharField(source='user.role',           read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'username', 'full_name', 'role',
            'attendance_date', 'status', 'total_work_hours',
            'punch_in', 'punch_out', 'notes',
        ]
