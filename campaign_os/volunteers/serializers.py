"""
Serializers for volunteer management
"""
from rest_framework import serializers
from campaign_os.volunteers.models import Volunteer, VolunteerTask, VolunteerAttendance
from campaign_os.masters.models import Booth


class VolunteerSerializer(serializers.ModelSerializer):
    user_name      = serializers.SerializerMethodField()
    booth_name     = serializers.CharField(source='booth.name', read_only=True)
    username       = serializers.SerializerMethodField()
    phone          = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    booths         = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Booth.objects.all(), required=False
    )
    booth_names    = serializers.SerializerMethodField()
    panchayat_name = serializers.SerializerMethodField()
    union_name     = serializers.SerializerMethodField()

    def get_user_name(self, obj):
        if obj.name:
            return obj.name
        if obj.user_id:
            return obj.user.get_full_name() or obj.user.username
        return f'Volunteer #{obj.id}'

    def get_username(self, obj):
        return obj.user.username if obj.user_id else ''

    def to_representation(self, obj):
        data = super().to_representation(obj)
        # Fall back to linked user's phone when the volunteer's own phone is blank
        if not data.get('phone') and obj.user_id:
            data['phone'] = getattr(obj.user, 'phone', '') or ''
        return data

    def get_booth_names(self, obj):
        return list(obj.booths.values_list('name', flat=True))

    def _effective_booth(self, obj):
        """Return primary booth FK if set, else the first M2M booth (uses prefetch cache)."""
        if obj.booth_id:
            return obj.booth
        booths = obj.booths.all()   # hits prefetch cache — no extra query
        return booths[0] if booths else None

    def get_panchayat_name(self, obj):
        try:
            return self._effective_booth(obj).panchayat.name or ''
        except AttributeError:
            return ''

    def get_union_name(self, obj):
        try:
            return self._effective_booth(obj).panchayat.union.name or ''
        except AttributeError:
            return ''

    def create(self, validated_data):
        booths = validated_data.pop('booths', [])
        instance = super().create(validated_data)
        if booths:
            instance.booths.set(booths)
        return instance

    def update(self, instance, validated_data):
        booths = validated_data.pop('booths', None)
        instance = super().update(instance, validated_data)
        if booths is not None:
            instance.booths.set(booths)
        return instance

    class Meta:
        model = Volunteer
        fields = [
            'id', 'user', 'user_name', 'username', 'name', 'voter_id', 'phone',
            'booth', 'booth_name', 'booths', 'booth_names', 'ward', 'block',
            'panchayat_name', 'union_name',
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
