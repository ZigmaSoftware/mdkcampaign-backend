"""
Serializers for volunteer management
"""
from rest_framework import serializers
from campaign_os.volunteers.models import Volunteer, VolunteerTask, VolunteerAttendance


class VolunteerSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    booth_name = serializers.CharField(source='booth.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)

    class Meta:
        model = Volunteer
        fields = [
            'id', 'user', 'user_name', 'username', 'phone',
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
