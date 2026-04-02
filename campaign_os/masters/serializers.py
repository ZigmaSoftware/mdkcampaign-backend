"""
Serializers for master data
"""
from rest_framework import serializers
from campaign_os.masters.models import (
    Country, State, District, Constituency, Ward, Booth, PollingArea,
    Candidate, Party, Scheme, Issue, Achievement, TaskType, TaskCategory, CampaignActivityType, VolunteerRole, VolunteerType, Panchayat, Union
)
from django.contrib.auth import get_user_model

User = get_user_model()


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'code', 'created_at', 'updated_at']


class StateSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)
    
    class Meta:
        model = State
        fields = ['id', 'country', 'country_name', 'name', 'code', 'created_at', 'updated_at']


class DistrictSimpleSerializer(serializers.ModelSerializer):
    """Minimal district info - for nested contexts"""
    state_code = serializers.CharField(source='state.code', read_only=True)
    
    class Meta:
        model = District
        fields = ['id', 'name', 'code', 'state', 'state_code']


class DistrictDetailSerializer(serializers.ModelSerializer):
    """Full district details"""
    state_name = serializers.CharField(source='state.name', read_only=True)
    constituencies_count = serializers.SerializerMethodField()
    booths_count = serializers.SerializerMethodField()
    
    class Meta:
        model = District
        fields = [
            'id', 'state', 'state_name', 'name', 'code', 'description',
            'office_address', 'office_phone', 'office_email',
            'latitude', 'longitude', 'constituencies_count', 'booths_count',
            'created_at', 'updated_at'
        ]
    
    def get_constituencies_count(self, obj):
        return obj.constituencies.filter(is_active=True).count()
    
    def get_booths_count(self, obj):
        return Booth.objects.filter(
            ward__constituency__district=obj,
            is_active=True
        ).count()


class ConstituencySimpleSerializer(serializers.ModelSerializer):
    """Minimal constituency info"""
    district_name = serializers.CharField(source='district.name', read_only=True)
    
    class Meta:
        model = Constituency
        fields = ['id', 'name', 'code', 'district', 'district_name']


class ConstituencyDetailSerializer(serializers.ModelSerializer):
    """Full constituency details"""
    district_name = serializers.CharField(source='district.name', read_only=True)
    state_name = serializers.CharField(source='district.state.name', read_only=True)
    wards_count = serializers.SerializerMethodField()
    booths_count = serializers.SerializerMethodField()
    candidates = serializers.SerializerMethodField()
    
    class Meta:
        model = Constituency
        fields = [
            'id', 'district', 'district_name', 'state_name', 'name', 'code',
            'election_type', 'description', 'latitude', 'longitude',
            'total_population', 'wards_count', 'booths_count', 'candidates',
            'created_at', 'updated_at'
        ]
    
    def get_wards_count(self, obj):
        return obj.wards.filter(is_active=True).count()
    
    def get_booths_count(self, obj):
        return Booth.objects.filter(
            ward__constituency=obj,
            is_active=True
        ).count()
    
    def get_candidates(self, obj):
        candidates = obj.candidates.filter(is_active=True)
        return [{'id': c.id, 'name': c.name, 'party': c.party.name} for c in candidates]


class WardSimpleSerializer(serializers.ModelSerializer):
    """Minimal ward info"""
    constituency_name = serializers.CharField(source='constituency.name', read_only=True)
    
    class Meta:
        model = Ward
        fields = ['id', 'name', 'code', 'constituency', 'constituency_name']


class WardDetailSerializer(serializers.ModelSerializer):
    """Full ward details"""
    constituency_name = serializers.CharField(source='constituency.name', read_only=True)
    booths_count = serializers.SerializerMethodField()
    voters_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Ward
        fields = [
            'id', 'constituency', 'constituency_name', 'name', 'code',
            'description', 'latitude', 'longitude', 'booths_count', 'voters_count',
            'created_at', 'updated_at'
        ]
    
    def get_booths_count(self, obj):
        return obj.booths.filter(is_active=True).count()
    
    def get_voters_count(self, obj):
        return obj.booths.aggregate(
            total=serializers.IntegerField(default=0)
        )['total']


class BoothSimpleSerializer(serializers.ModelSerializer):
    """Minimal booth info"""
    ward_name = serializers.CharField(source='ward.name', read_only=True, default=None)

    class Meta:
        model = Booth
        fields = ['id', 'number', 'name', 'code', 'status', 'panchayat', 'ward', 'ward_name']


class BoothDetailSerializer(serializers.ModelSerializer):
    """Full booth details with coverage stats"""
    ward_name      = serializers.CharField(source='ward.name',      read_only=True, default=None)
    panchayat_name = serializers.CharField(source='panchayat.name', read_only=True, default='')
    constituency_name = serializers.SerializerMethodField()
    primary_volunteer = serializers.PrimaryKeyRelatedField(read_only=True)
    agent_name = serializers.SerializerMethodField()
    agent_ids = serializers.PrimaryKeyRelatedField(
        source='agents', queryset=User.objects.all(), many=True, required=False
    )
    agent_names = serializers.SerializerMethodField()
    google_maps_url = serializers.SerializerMethodField()
    total_voters_calculated = serializers.SerializerMethodField()

    class Meta:
        model = Booth
        validators = []
        fields = [
            'id', 'ward', 'ward_name', 'panchayat', 'panchayat_name', 'constituency_name', 'number', 'name', 'code',
            'address', 'village', 'latitude', 'longitude',
            'total_voters', 'male_voters', 'female_voters', 'third_gender_voters',
            'total_voters_calculated', 'primary_agent', 'agent_name',
            'primary_volunteer',
            'agent_ids', 'agent_names',
            'status', 'sentiment', 'notes', 'google_maps_url',
            'created_at', 'updated_at'
        ]

    def get_constituency_name(self, obj):
        return ''

    def get_google_maps_url(self, obj):
        return obj.get_google_maps_url()

    def get_total_voters_calculated(self, obj):
        return obj.male_voters + obj.female_voters + obj.third_gender_voters

    def get_agent_names(self, obj):
        return [u.get_full_name() for u in obj.agents.all()]

    def get_agent_name(self, obj):
        if hasattr(obj, 'primary_volunteer') and obj.primary_volunteer_id:
            pv = obj.primary_volunteer
            return pv.name or (pv.user.get_full_name() if pv.user_id else f'Volunteer #{pv.id}')
        if obj.primary_agent_id:
            return obj.primary_agent.get_full_name()
        return ''


class PollingAreaSerializer(serializers.ModelSerializer):
    """Polling Area (Maps to 'area' in frontend)"""
    constituency_name = serializers.CharField(source='constituency.name', read_only=True)
    
    class Meta:
        model = PollingArea
        fields = [
            'id', 'constituency', 'constituency_name', 'name', 'code',
            'description', 'latitude', 'longitude', 'created_at', 'updated_at'
        ]


class PartySerializer(serializers.ModelSerializer):
    """Political Party"""
    candidates_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Party
        fields = [
            'id', 'name', 'code', 'abbreviation', 'description',
            'founded_year', 'headquarters', 'president_name',
            'primary_color', 'secondary_color', 'logo',
            'is_national', 'candidates_count', 'created_at', 'updated_at'
        ]
    
    def get_candidates_count(self, obj):
        return obj.candidates.filter(is_active=True).count()


class CandidateDetailSerializer(serializers.ModelSerializer):
    """Candidate details"""
    party_name = serializers.CharField(source='party.name', read_only=True)
    party_color = serializers.CharField(source='party.primary_color', read_only=True)
    constituency_name = serializers.CharField(source='constituency.name', read_only=True)
    
    class Meta:
        model = Candidate
        fields = [
            'id', 'name', 'father_name', 'date_of_birth', 'gender',
            'party', 'party_name', 'party_color', 'constituency', 'constituency_name',
            'phone', 'email', 'address', 'educational_qualification',
            'professional_background', 'photo', 'bio',
            'is_incumbent', 'election_symbol',
            'created_at', 'updated_at'
        ]


class CandidateSimpleSerializer(serializers.ModelSerializer):
    """Minimal candidate info"""
    party_name = serializers.CharField(source='party.name', read_only=True)
    party_color = serializers.CharField(source='party.primary_color', read_only=True)
    
    class Meta:
        model = Candidate
        fields = ['id', 'name', 'party', 'party_name', 'party_color', 'is_incumbent']


class SchemeSerializer(serializers.ModelSerializer):
    """Campaign/Government Scheme"""
    constituency_name = serializers.CharField(source='constituency.name', read_only=True)
    
    class Meta:
        model = Scheme
        fields = [
            'id', 'name', 'description', 'scheme_type',
            'constituency', 'constituency_name',
            'launch_date', 'end_date',
            'target_population', 'beneficiaries', 'budget',
            'responsible_ministry', 'created_at', 'updated_at'
        ]


class IssueSerializer(serializers.ModelSerializer):
    """Community Issue/Grievance Type"""
    class Meta:
        model = Issue
        fields = [
            'id', 'name', 'description', 'category', 'priority',
            'created_at', 'updated_at'
        ]


class TaskTypeSerializer(serializers.ModelSerializer):
    """Task Type master"""
    status = serializers.ChoiceField(
        choices=[('active', 'Active'), ('inactive', 'Inactive')],
        required=False,
        write_only=True,
        help_text='active / inactive',
    )

    class Meta:
        model = TaskType
        fields = ['id', 'name', 'status', 'description', 'order', 'created_at', 'updated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['status'] = 'active' if instance.is_active else 'inactive'
        return data

    def create(self, validated_data):
        status_value = validated_data.pop('status', None)
        if status_value is not None:
            validated_data['is_active'] = status_value == 'active'
        return super().create(validated_data)

    def update(self, instance, validated_data):
        status_value = validated_data.pop('status', None)
        if status_value is not None:
            validated_data['is_active'] = status_value == 'active'
        return super().update(instance, validated_data)


class TaskCategorySerializer(serializers.ModelSerializer):
    """Task Category master"""
    task_type_name = serializers.CharField(source='task_type.name', read_only=True, default='')

    class Meta:
        model = TaskCategory
        fields = ['id', 'task_type', 'task_type_name', 'name', 'description', 'color', 'icon', 'priority', 'created_at', 'updated_at']


class AchievementSerializer(serializers.ModelSerializer):
    """Campaign Achievement"""
    panchayat_name = serializers.CharField(source='panchayat.name', read_only=True, default='')
    booth_name     = serializers.CharField(source='booth.name',     read_only=True, default='')

    class Meta:
        model = Achievement
        fields = [
            'id', 'name', 'description',
            'panchayat', 'panchayat_name', 'booth', 'booth_name',
            'feed_amount',
            'created_at', 'updated_at'
        ]


class CampaignActivityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignActivityType
        fields = ['id', 'name', 'description', 'order', 'is_active', 'created_at', 'updated_at']


class VolunteerRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = VolunteerRole
        fields = ['id', 'name', 'description', 'order', 'created_at', 'updated_at']


class VolunteerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VolunteerType
        fields = ['id', 'name', 'description', 'order', 'created_at', 'updated_at']


class PanchayatSerializer(serializers.ModelSerializer):
    union_name = serializers.CharField(source='union.name', read_only=True, default='')

    class Meta:
        model = Panchayat
        fields = ['id', 'union', 'union_name', 'name', 'code', 'category', 'description', 'created_at', 'updated_at']


class UnionSerializer(serializers.ModelSerializer):
    block_name = serializers.CharField(source='block.name', read_only=True, default='')

    class Meta:
        model = Union
        fields = ['id', 'block', 'block_name', 'name', 'code', 'description', 'created_at', 'updated_at']
