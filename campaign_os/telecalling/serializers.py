from rest_framework import serializers
from .models import TelecallingAssignment, TelecallingAssignmentVoter, TelecallingFeedback


class TelecallingAssignmentVoterSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TelecallingAssignmentVoter
        fields = ['id', 'voter', 'voter_name', 'voter_id_no', 'phone', 'address', 'booth_name', 'age', 'gender']


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
            TelecallingAssignmentVoter.objects.create(assignment=assignment, **v)
        return assignment


class TelecallingFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TelecallingFeedback
        fields = ['id', 'survey', 'voter_name', 'telecaller_name', 'action', 'date', 'created_at']
        read_only_fields = ['created_at']
