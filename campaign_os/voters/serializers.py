"""
Voter serializers
"""
from rest_framework import serializers
from campaign_os.voters.models import Voter, VoterContact, VoterSurvey, VoterPreference, VoterFeedback


class VoterSimpleSerializer(serializers.ModelSerializer):
    """Minimal voter info"""
    class Meta:
        model = Voter
        fields = ['id', 'name', 'voter_id', 'phone', 'booth', 'sentiment']


class VoterFamilyMappingSerializer(serializers.ModelSerializer):
    """Lean voter payload used by the family-mapping screen."""
    booth_name = serializers.CharField(source='booth.name', read_only=True, default='')

    class Meta:
        model = Voter
        fields = [
            'id', 'name', 'voter_id', 'father_name', 'phone', 'phone2',
            'alt_phoneno2', 'alt_phoneno3', 'address', 'booth', 'booth_name',
            'age', 'gender',
        ]


class VoterSerializer(serializers.ModelSerializer):
    """Full voter details"""
    booth_name      = serializers.CharField(source='booth.name',      read_only=True, default='')
    village_name    = serializers.CharField(source='village.name',    read_only=True, default='')
    party_name      = serializers.SerializerMethodField()
    workflow_status = serializers.SerializerMethodField()
    workflow_label  = serializers.SerializerMethodField()
    is_locked       = serializers.SerializerMethodField()

    def get_party_name(self, obj):
        return obj.preferred_party.name if obj.preferred_party_id else ''

    def _workflow(self, obj):
        return (self.context.get('voter_status_map') or {}).get(obj.id, {})

    def get_workflow_status(self, obj):
        return self._workflow(obj).get('status', '')

    def get_workflow_label(self, obj):
        return self._workflow(obj).get('label', '')

    def get_is_locked(self, obj):
        return self._workflow(obj).get('is_locked', False)

    class Meta:
        model = Voter
        fields = [
            'id', 'name', 'father_name', 'date_of_birth', 'gender', 'age',
            'voter_id', 'aadhaar', 'phone', 'phone2', 'alt_phoneno2', 'alt_phoneno3', 'email', 'booth', 'booth_name',
            'village', 'village_name', 'address', 'pincode', 'latitude', 'longitude',
            'religion', 'caste', 'sub_caste', 'current_location', 'scheme_name', 'issue_name',
            'education_level', 'occupation', 'sentiment', 'preferred_party',
            'party_name', 'is_contacted', 'last_contacted_at', 'contact_count',
            'has_attended_event', 'is_volunteer', 'feedback_score', 'notes',
            'workflow_status', 'workflow_label', 'is_locked',
            'created_at', 'updated_at'
        ]


class VoterContactSerializer(serializers.ModelSerializer):
    """Voter contact history"""
    voter_name = serializers.CharField(source='voter.name', read_only=True)
    contacted_by_name = serializers.CharField(source='contacted_by.get_full_name', read_only=True)
    
    class Meta:
        model = VoterContact
        fields = [
            'id', 'voter', 'voter_name', 'contacted_by', 'contacted_by_name',
            'method', 'duration_minutes', 'notes', 'sentiment_after', 'created_at'
        ]


class VoterSurveySerializer(serializers.ModelSerializer):
    """Voter survey submission"""
    voter_name = serializers.CharField(source='voter.name', read_only=True)
    
    class Meta:
        model = VoterSurvey
        fields = ['id', 'voter', 'voter_name', 'survey_type', 'responses', 'score', 'created_at']


class VoterPreferenceSerializer(serializers.ModelSerializer):
    """Voter preferences"""
    issues = serializers.PrimaryKeyRelatedField(
        source='issues_of_interest',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = VoterPreference
        fields = [
            'id', 'voter', 'issues', 'preferred_language',
            'best_time_to_contact', 'do_not_contact'
        ]


class VoterFeedbackSerializer(serializers.ModelSerializer):
    """Voter feedback and grievances.

    Accepts either:
      - voter (int FK)  – when the exact Voter record is known
      - voter_name (str) – free-text name; will attempt a case-insensitive lookup
                           and link automatically; stored as-is if not found
    """
    # read-only display helpers
    voter_display_name = serializers.SerializerMethodField(read_only=True)
    assigned_to_name   = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    issue_name         = serializers.CharField(source='issue.name', read_only=True)

    class Meta:
        model = VoterFeedback
        fields = [
            'id', 'voter', 'voter_name', 'voter_phone', 'voter_display_name',
            'feedback_type', 'subject', 'description',
            'issue', 'issue_name', 'status', 'assigned_to', 'assigned_to_name',
            'resolution', 'resolved_at', 'created_at', 'updated_at',
        ]

    def get_voter_display_name(self, obj):
        if obj.voter_id:
            return obj.voter.name
        return obj.voter_name or '—'

    def validate(self, attrs):
        voter     = attrs.get('voter')
        name_raw  = attrs.get('voter_name', '').strip()

        if not voter and name_raw:
            # Try to resolve name → Voter FK automatically
            match = Voter.objects.filter(name__iexact=name_raw, is_active=True).first()
            if match:
                attrs['voter'] = match
                attrs['voter_name'] = match.name  # normalise
        return attrs
