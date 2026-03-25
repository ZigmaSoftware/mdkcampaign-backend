"""
Serializers for volunteer management
"""
from rest_framework import serializers
from campaign_os.volunteers.models import Volunteer, VolunteerTask, VolunteerAttendance


class VolunteerSerializer(serializers.ModelSerializer):
    user_name  = serializers.SerializerMethodField()
    booth_name = serializers.CharField(source='booth.name', read_only=True)
    username   = serializers.SerializerMethodField()
    phone      = serializers.SerializerMethodField()

    def get_user_name(self, obj):
        if obj.name:
            return obj.name
        if obj.user_id:
            return obj.user.get_full_name() or obj.user.username
        return f'Volunteer #{obj.id}'

    def get_username(self, obj):
        return obj.user.username if obj.user_id else ''

    def get_phone(self, obj):
        return obj.phone or (getattr(obj.user, 'phone', '') if obj.user_id else '')

    class Meta:
        model = Volunteer
        fields = [
            'id', 'user', 'user_name', 'username', 'name', 'phone',
            'booth', 'booth_name', 'ward', 'block',
            'status', 'volunteer_type', 'role', 'age', 'gender', 'joined_date',
            'source', 'skills', 'vehicle', 'notes', 'phone2',
            'experience_months', 'previous_campaigns',
            'voters_contacted', 'events_attended', 'hours_contributed',
            'performance_score', 'is_active', 'created_at',
        ]


class VolunteerTaskSerializer(serializers.ModelSerializer):
    volunteer_name = serializers.CharField(source='volunteer.user.get_full_name', read_only=True)

    class Meta:
        model = VolunteerTask
        fields = [
            'id', 'volunteer', 'volunteer_name', 'title', 'description',
            'assignment_type', 'target_count', 'due_date', 'priority',
            'status', 'completed_at', 'actual_count', 'completion_notes',
            'created_at',
        ]


class VolunteerAttendanceSerializer(serializers.ModelSerializer):
    volunteer_name = serializers.CharField(source='volunteer.user.get_full_name', read_only=True)

    class Meta:
        model = VolunteerAttendance
        fields = [
            'id', 'volunteer', 'volunteer_name',
            'date', 'check_in_time', 'check_out_time', 'location', 'notes',
            'created_at',
        ]
