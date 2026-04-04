from rest_framework import serializers
from .models import TelecallingAssignment, TelecallingAssignmentVoter, TelecallingFeedback


class TelecallingAssignmentVoterSerializer(serializers.ModelSerializer):
    # Kept for backward-compatible request payloads from older/newer frontends.
    phone2 = serializers.CharField(required=False, allow_blank=True, write_only=True)
    alt_phoneno2 = serializers.CharField(required=False, allow_blank=True, write_only=True)
    alt_phoneno3 = serializers.CharField(required=False, allow_blank=True, write_only=True)
    workflow_status = serializers.SerializerMethodField()
    workflow_label = serializers.SerializerMethodField()
    is_locked = serializers.SerializerMethodField()

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
            'address', 'booth_name', 'age', 'gender',
            'workflow_status', 'workflow_label', 'is_locked',
        ]


class TelecallingAssignmentSerializer(serializers.ModelSerializer):
    voters = TelecallingAssignmentVoterSerializer(many=True)

    class Meta:
        model  = TelecallingAssignment
        fields = [
            'id', 'telecaller_id', 'telecaller_name', 'telecaller_phone',
            'assigned_date', 'voters', 'created_at',
        ]
        read_only_fields = ['created_at']

    def create(self, validated_data):
        voters_data = validated_data.pop('voters', [])
        assignment  = TelecallingAssignment.objects.create(**validated_data)
        for v in voters_data:
            v.pop('phone2', None)
            v.pop('alt_phoneno2', None)
            v.pop('alt_phoneno3', None)
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
