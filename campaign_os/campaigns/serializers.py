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
    task_type_name         = serializers.CharField(source='task_type.name', read_only=True, default='')
    task_category_name     = serializers.CharField(source='task_category.name', read_only=True, default='')
    task_category_color    = serializers.CharField(source='task_category.color', read_only=True, default='')
    volunteer_role_name    = serializers.CharField(source='volunteer_role.name', read_only=True, default='')
    block_name             = serializers.CharField(source='block.name', read_only=True, default='')
    union_name             = serializers.CharField(source='union.name', read_only=True, default='')
    panchayat_name         = serializers.CharField(source='panchayat.name', read_only=True, default='')
    booth_name             = serializers.CharField(source='booth.name', read_only=True, default='')
    ward_name              = serializers.CharField(source='ward.name', read_only=True, default='')
    delivery_incharge_name = serializers.SerializerMethodField()
    coordinator_name       = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id',
            'task_type', 'task_type_name',
            'title', 'category',
            'task_category', 'task_category_name', 'task_category_color',
            'details', 'expected_datetime', 'venue',
            'block', 'block_name',
            'union', 'union_name',
            'panchayat', 'panchayat_name',
            'booth', 'booth_name',
            'ward', 'ward_name',
            'volunteer_role', 'volunteer_role_name',
            'delivery_incharge', 'delivery_incharge_name',
            'coordinator', 'coordinator_name',
            'qty', 'status', 'completed_datetime', 'notes',
            'is_active', 'created_at', 'updated_at',
        ]

    def validate(self, attrs):
        """
        Keep task_type and task_category consistent.
        - If category belongs to a type and type is missing, auto-fill it.
        - If both are present and mismatch, reject.
        """
        instance = getattr(self, 'instance', None)
        task_type = attrs.get('task_type', getattr(instance, 'task_type', None))
        task_category = attrs.get('task_category', getattr(instance, 'task_category', None))

        if task_category and task_category.task_type_id:
            if task_type and task_type.id != task_category.task_type_id:
                raise serializers.ValidationError({
                    'task_category': 'Selected task category does not belong to the selected task type.'
                })
            if not task_type:
                attrs['task_type'] = task_category.task_type

        return attrs

    def get_delivery_incharge_name(self, obj):
        if obj.delivery_incharge:
            v = obj.delivery_incharge
            return v.name or (v.user.get_full_name() if v.user_id else f'Volunteer #{v.id}')
        return None

    def get_coordinator_name(self, obj):
        if obj.coordinator:
            v = obj.coordinator
            return v.name or (v.user.get_full_name() if v.user_id else f'Volunteer #{v.id}')
        return None
