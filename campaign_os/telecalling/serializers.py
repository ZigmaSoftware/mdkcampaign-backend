from rest_framework import serializers
from django.utils import timezone
from .models import TelecallingAssignment, TelecallingAssignmentVoter, TelecallingFeedback


class TelecallingAssignmentVoterSerializer(serializers.ModelSerializer):
    # Kept for backward-compatible request payloads from older/newer frontends.
    phone2 = serializers.CharField(required=False, allow_blank=True, write_only=True)
    alt_phoneno2 = serializers.CharField(required=False, allow_blank=True, write_only=True)
    alt_phoneno3 = serializers.CharField(required=False, allow_blank=True, write_only=True)
    booth_no = serializers.SerializerMethodField()
    entity_type = serializers.CharField(required=False, allow_blank=True)
    source_id = serializers.IntegerField(required=False, allow_null=True)
    relation_label = serializers.CharField(required=False, allow_blank=True)
    workflow_status = serializers.SerializerMethodField()
    workflow_label = serializers.SerializerMethodField()
    is_locked = serializers.SerializerMethodField()

    def get_booth_no(self, obj):
        if obj.booth_no:
            return obj.booth_no
        voter = getattr(obj, 'voter', None)
        booth = getattr(voter, 'booth', None) if voter else None
        return getattr(booth, 'number', '') or ''

    def _workflow(self, obj):
        status_map = self.context.get('voter_status_map') or {}
        if obj.voter_id:
            return status_map.get(obj.voter_id, {})
        return {}

    def get_workflow_status(self, obj):
        return self._workflow(obj).get('status', 'assigned')

    def get_workflow_label(self, obj):
        return self._workflow(obj).get('label', 'Assigned')

    def get_is_locked(self, obj):
        return self._workflow(obj).get('is_locked', True)

    class Meta:
        model  = TelecallingAssignmentVoter
        fields = [
            'id', 'voter', 'voter_name', 'voter_id_no', 'phone',
            'phone2', 'alt_phoneno2', 'alt_phoneno3',
            'address', 'booth_name', 'booth_no', 'age', 'gender',
            'entity_type', 'source_id', 'relation_label',
            'workflow_status', 'workflow_label', 'is_locked',
        ]


class TelecallingAssignmentSerializer(serializers.ModelSerializer):
    voters = TelecallingAssignmentVoterSerializer(many=True)
    assignment_time = serializers.SerializerMethodField()

    def get_assignment_time(self, obj):
        if not obj.created_at:
            return ''
        return timezone.localtime(obj.created_at).strftime('%H:%M:%S')

    class Meta:
        model  = TelecallingAssignment
        fields = [
            'id', 'telecaller_id', 'telecaller_name', 'telecaller_phone',
            'assigned_date', 'assignment_time', 'voters', 'created_at',
        ]
        read_only_fields = ['created_at']

    def create(self, validated_data):
        voters_data = validated_data.pop('voters', [])
        assignment  = TelecallingAssignment.objects.create(**validated_data)
        for v in voters_data:
            v.pop('phone2', None)
            v.pop('alt_phoneno2', None)
            v.pop('alt_phoneno3', None)
            if not v.get('entity_type'):
                v['entity_type'] = 'voter'
            if v.get('source_id') is None and v.get('voter'):
                v['source_id'] = v.get('voter')
            TelecallingAssignmentVoter.objects.create(assignment=assignment, **v)
        return assignment


class TelecallingFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TelecallingFeedback
        fields = [
            'id', 'survey', 'voter_name', 'telecaller_name',
            'action', 'followup_type', 'date', 'created_at',
        ]
        read_only_fields = ['created_at']
