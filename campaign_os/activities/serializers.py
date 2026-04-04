from rest_framework import serializers
from .models import ActivityLog, FieldSurvey


SUPPORT_LEVEL_ALIASES = {
    'positive': 'positive',
    'strong support': 'positive',
    'leaning support': 'positive',
    'neutral': 'neutral',
    'undecided': 'neutral',
    'negative': 'negative',
    'leaning against': 'negative',
    'strong against': 'negative',
}

RESPONSE_STATUS_ALIASES = {
    'not_reach': 'not_reach',
    'not reach': 'not_reach',
    'no_answer': 'no_answer',
    'no answer': 'no_answer',
    'need_followup': 'need_followup',
    'need followup': 'need_followup',
    'need_followups': 'need_followup',
    'interested': 'need_followup',
    'not_attend_call': 'no_answer',
    'not attend call': 'no_answer',
}


def _normalize_choice_value(value, alias_map):
    raw = (value or '').strip()
    if not raw:
        return ''
    return alias_map.get(raw.lower(), raw)


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
    support_level = serializers.CharField(required=False, allow_blank=True)
    response_status = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model  = FieldSurvey
        fields = [
            'id', 'voter', 'survey_date', 'block', 'village', 'booth_no',
            'voter_name', 'age', 'gender', 'phone', 'address',
            'is_registered', 'aware_of_candidate', 'likely_to_vote',
            'support_level', 'party_preference', 'key_issues', 'remarks',
            'response_status',
            'surveyed_by', 'assigned_volunteer',
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

    def validate_support_level(self, value):
        normalized = _normalize_choice_value(value, SUPPORT_LEVEL_ALIASES)
        if not normalized:
            return ''
        if normalized in {'positive', 'negative', 'neutral'}:
            return normalized

        instance = getattr(self, 'instance', None)
        if instance and (instance.support_level or '').strip() == (value or '').strip():
            return normalized

        raise serializers.ValidationError("Unsupported support level.")

    def validate_response_status(self, value):
        normalized = _normalize_choice_value(value, RESPONSE_STATUS_ALIASES)
        if not normalized:
            return ''
        if normalized in {'not_reach', 'no_answer', 'need_followup'}:
            return normalized

        instance = getattr(self, 'instance', None)
        if instance and (instance.response_status or '').strip() == (value or '').strip():
            return normalized

        raise serializers.ValidationError("Unsupported response status.")
