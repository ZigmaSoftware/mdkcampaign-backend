"""
Serializers for analytics dashboard
"""
from rest_framework import serializers
from campaign_os.analytics.models import DashboardSnapshot


class DashboardSnapshotSerializer(serializers.ModelSerializer):
    voter_contact_percentage = serializers.SerializerMethodField()
    booth_assignment_percentage = serializers.SerializerMethodField()
    event_completion_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = DashboardSnapshot
        fields = [
            'id', 'snapshot_date',
            'total_voters', 'voters_contacted', 'voter_contact_percentage',
            'voters_by_sentiment', 'total_booths', 'booths_assigned',
            'booths_working', 'booth_assignment_percentage',
            'total_volunteers', 'active_volunteers', 'avg_performance_score',
            'total_events', 'completed_events', 'event_completion_percentage',
            'total_attendees', 'surveys_conducted', 'feedback_received',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'voter_contact_percentage', 'booth_assignment_percentage',
            'event_completion_percentage'
        ]
    
    def get_voter_contact_percentage(self, obj):
        if obj.total_voters == 0:
            return 0
        return round((obj.voters_contacted / obj.total_voters) * 100, 2)
    
    def get_booth_assignment_percentage(self, obj):
        if obj.total_booths == 0:
            return 0
        return round((obj.booths_assigned / obj.total_booths) * 100, 2)
    
    def get_event_completion_percentage(self, obj):
        if obj.total_events == 0:
            return 0
        return round((obj.completed_events / obj.total_events) * 100, 2)
