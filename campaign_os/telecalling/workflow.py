from __future__ import annotations

from typing import Dict, Iterable

from .models import TelecallingAssignmentVoter, TelecallingFeedback


WORKFLOW_LABELS = {
    'assigned': 'Assigned',
    'pending_followup': 'Pending Follow-up',
    'pending_field_survey': 'Pending Field Survey',
    'reassigned': 'Reassigned',
    'completed': 'Completed',
}


def build_voter_status_map(voter_ids: Iterable[int]) -> Dict[int, dict]:
    """
    Compute current workflow state for each voter based on latest feedback and
    assignment timestamps.
    """
    voter_id_set = {int(v) for v in voter_ids if v}
    if not voter_id_set:
        return {}

    latest_feedback = {}
    feedback_qs = (
        TelecallingFeedback.objects
        .filter(is_active=True, survey__voter_id__in=voter_id_set)
        .select_related('survey')
        .order_by('survey__voter_id', '-date', '-created_at', '-id')
    )
    for feedback in feedback_qs:
        survey = feedback.survey
        voter_id = survey.voter_id if survey else None
        if voter_id and voter_id not in latest_feedback:
            latest_feedback[voter_id] = feedback

    latest_assignment = {}
    assignment_qs = (
        TelecallingAssignmentVoter.objects
        .filter(voter_id__in=voter_id_set)
        .select_related('assignment')
        .order_by('voter_id', '-assignment__created_at', '-assignment_id')
    )
    for row in assignment_qs:
        if row.voter_id not in latest_assignment:
            latest_assignment[row.voter_id] = row.assignment.created_at

    status_map: Dict[int, dict] = {}
    for voter_id in voter_id_set:
        feedback = latest_feedback.get(voter_id)
        if not feedback:
            status = 'assigned'
            is_locked = True
        elif feedback.action == 'followup_not_required':
            status = 'completed'
            is_locked = True
        elif feedback.followup_type == 'field_survey':
            status = 'pending_field_survey'
            is_locked = True
        else:
            latest_assignment_ts = latest_assignment.get(voter_id)
            feedback_ts = feedback.created_at
            if latest_assignment_ts and feedback_ts and latest_assignment_ts > feedback_ts:
                status = 'reassigned'
                is_locked = True
            else:
                status = 'pending_followup'
                is_locked = False

        status_map[voter_id] = {
            'status': status,
            'label': WORKFLOW_LABELS.get(status, status.replace('_', ' ').title()),
            'is_locked': is_locked,
        }

    return status_map
