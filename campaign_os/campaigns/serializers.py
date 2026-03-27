"""
Serializers for campaigns
"""
from rest_framework import serializers
from campaign_os.campaigns.models import CampaignEvent, EventAttendee, Task


class EventAttendeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventAttendee
        fields = [
            'id', 'event', 'attendee_type', 'name', 'phone', 'email',
            'voter', 'feedback', 'sentiment', 'created_at',
        ]


class CampaignEventSerializer(serializers.ModelSerializer):
    constituency_name = serializers.CharField(source='constituency.name', read_only=True)
    organizer_name = serializers.SerializerMethodField()
    attendee_count = serializers.SerializerMethodField()

    class Meta:
        model = CampaignEvent
        fields = [
            'id', 'title', 'description', 'event_type',
            'constituency', 'constituency_name',
            'organized_by', 'organizer_name',
            'scheduled_date', 'scheduled_time', 'location',
            'expected_attendees', 'actual_attendees', 'status',
            'materials_prepared', 'outcome_notes', 'special_guest_name',
            'attendee_count', 'is_active', 'created_at', 'updated_at',
        ]

    def get_organizer_name(self, obj):
        if obj.organized_by:
            return obj.organized_by.get_full_name() or obj.organized_by.username
        return None

    def get_attendee_count(self, obj):
        return obj.attendees.filter(is_active=True).count()


class TaskSerializer(serializers.ModelSerializer):
    delivery_incharge_name = serializers.SerializerMethodField()
    coordinator_name       = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'category', 'details',
            'expected_datetime', 'venue',
            'delivery_incharge', 'delivery_incharge_name',
            'coordinator', 'coordinator_name',
            'qty', 'status', 'completed_datetime', 'notes',
            'is_active', 'created_at', 'updated_at',
        ]

    def get_delivery_incharge_name(self, obj):
        if obj.delivery_incharge:
            return obj.delivery_incharge.get_full_name() or obj.delivery_incharge.username
        return None

    def get_coordinator_name(self, obj):
        if obj.coordinator:
            return obj.coordinator.get_full_name() or obj.coordinator.username
        return None
