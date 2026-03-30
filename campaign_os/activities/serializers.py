from rest_framework import serializers
from .models import ActivityLog, FieldSurvey


class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ActivityLog
        fields = [
            'id', 'category', 'activity_type', 'date',
            'hours_worked', 'village', 'booth_no', 'notes',
            'username', 'user_role',
            'created_at', 'updated_at',
        ]

    def validate_activity_type(self, value):
        if not value.strip():
            raise serializers.ValidationError("Activity type is required.")
        return value.strip()

    def validate_hours_worked(self, value):
        if value is not None and (value < 0 or value > 24):
            raise serializers.ValidationError("Hours worked must be between 0 and 24.")
        return value


class FieldSurveySerializer(serializers.ModelSerializer):
    class Meta:
        model  = FieldSurvey
        fields = [
            'id', 'voter', 'survey_date', 'block', 'village', 'booth_no',
            'voter_name', 'age', 'gender', 'phone', 'address',
            'is_registered', 'aware_of_candidate', 'likely_to_vote',
            'support_level', 'party_preference', 'key_issues', 'remarks',
            'response_status',
            'surveyed_by',
            'created_at', 'updated_at',
        ]

    def validate_voter_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Voter name is required.")
        return value.strip()

    def validate_age(self, value):
        if value is not None and (value < 18 or value > 120):
            raise serializers.ValidationError("Age must be between 18 and 120.")
        return value

    def validate_phone(self, value):
        if value and len(value.replace(' ', '').replace('-', '')) < 10:
            raise serializers.ValidationError("Enter a valid phone number (min 10 digits).")
        return value
