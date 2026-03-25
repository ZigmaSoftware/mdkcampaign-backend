"""
Serializers for elections and polls
"""
from rest_framework import serializers
from campaign_os.elections.models import Election, Poll, PollQuestion, PollResponse


class ElectionSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    
    class Meta:
        model = Election
        fields = [
            'id', 'name', 'description', 'election_type', 'state', 'state_name',
            'announcement_date', 'nomination_start_date', 'nomination_end_date',
            'election_date', 'result_date', 'status', 'created_at', 'updated_at'
        ]


class PollQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollQuestion
        fields = ['id', 'poll', 'question_text', 'question_type', 'order', 'options']


class PollSerializer(serializers.ModelSerializer):
    constituency_name = serializers.CharField(source='constituency.name', read_only=True)
    election_name = serializers.CharField(source='election.name', read_only=True)
    
    class Meta:
        model = Poll
        fields = [
            'id', 'election', 'election_name', 'name', 'conducted_by',
            'constituency', 'constituency_name', 'sample_size',
            'sampling_method', 'poll_date_start', 'poll_date_end',
            'poll_results', 'accuracy_notes', 'created_at', 'updated_at'
        ]


class PollResponseSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    voter_name = serializers.CharField(source='voter.name', read_only=True)
    
    class Meta:
        model = PollResponse
        fields = [
            'id', 'poll', 'question', 'question_text', 'voter', 'voter_name',
            'response_text', 'response_value', 'created_at'
        ]
