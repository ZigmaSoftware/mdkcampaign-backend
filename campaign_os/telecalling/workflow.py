from __future__ import annotations

from collections import defaultdict
import re
from typing import Dict, Iterable

from campaign_os.activities.models import FieldSurvey
from campaign_os.voters.models import Voter
from django.db.models import Q

from .models import TelecallingAssignmentVoter, TelecallingFeedback


WORKFLOW_LABELS = {
    'unassigned': 'Unassigned',
    'assigned': 'Assigned',
    'already_assigned': 'Already Assigned',
    'already_contacted': 'Already Contacted',
    'pending_followup': 'Pending Follow-up',
    'pending_field_survey': 'Pending Field Survey',
    'reassigned': 'Reassigned',
    'completed': 'Completed',
}


PHONE_FIELDS = ('phone', 'phone2', 'alt_phoneno2', 'alt_phoneno3')
NON_DIGIT_RE = re.compile(r'\D+')


def _normalize_phone(value) -> str:
    raw = str(value or '').strip()
    if not raw:
        return ''
    digits = NON_DIGIT_RE.sub('', raw)
    if len(digits) > 10:
        digits = digits[-10:]
    return digits


def _collect_phone_numbers(voter) -> set[str]:
    numbers: set[str] = set()
    for field in PHONE_FIELDS:
        normalized = _normalize_phone(getattr(voter, field, ''))
        if normalized:
            numbers.add(normalized)
    return numbers


def build_voter_status_map(voter_ids: Iterable[int]) -> Dict[int, dict]:
    """
    Compute current workflow state for each voter based on latest feedback and
    assignment timestamps.

    Handles two lookup paths:
      1. survey.voter_id FK (preferred, exact match)
      2. voter_name fallback for surveys where voter_id was not set
    """
    voter_id_set = {int(v) for v in voter_ids if v}
    if not voter_id_set:
        return {}

    current_voters = list(
        Voter.objects
        .filter(id__in=voter_id_set)
        .only('id', 'booth_id', *PHONE_FIELDS)
    )
    current_voter_ids = {voter.id for voter in current_voters}
    current_phone_values = {
        normalized
        for voter in current_voters
        for normalized in _collect_phone_numbers(voter)
    }

    related_voters = current_voters
    if current_phone_values:
        related_phone_q = Q()
        for field in PHONE_FIELDS:
            related_phone_q |= Q(**{f'{field}__in': tuple(current_phone_values)})
        related_voters = list(
            Voter.objects
            .filter(is_active=True)
            .filter(related_phone_q)
            .only('id', 'booth_id', *PHONE_FIELDS)
        )

    voter_meta = {
        voter.id: {
            'booth_id': voter.booth_id,
            'phones': _collect_phone_numbers(voter),
        }
        for voter in related_voters
    }
    expanded_voter_id_set = set(voter_meta.keys()) or voter_id_set

    # ── Collect voter_name → voter_id mapping from assignments ──
    name_to_voter_id: Dict[str, int] = {}
    assignment_qs = (
        TelecallingAssignmentVoter.objects
        .filter(voter_id__in=expanded_voter_id_set)
        .select_related('assignment')
        .order_by('voter_id', '-assignment__created_at', '-assignment_id')
    )
    latest_assignment: Dict[int, dict] = {}
    for row in assignment_qs:
        if row.voter_id not in latest_assignment:
            latest_assignment[row.voter_id] = {
                'created_at': row.assignment.created_at,
                'telecaller_id': row.assignment.telecaller_id,
                'telecaller_name': row.assignment.telecaller_name or '',
                'telecaller_phone': row.assignment.telecaller_phone or '',
            }
        # Build name → id mapping (lowercase for case-insensitive match)
        if row.voter_name:
            name_to_voter_id[row.voter_name.strip().lower()] = row.voter_id

    # ── Find latest feedback per voter (by voter_id FK) ──
    latest_feedback: Dict[int, object] = {}
    feedback_qs = (
        TelecallingFeedback.objects
        .filter(is_active=True, survey__voter_id__in=expanded_voter_id_set)
        .select_related('survey')
        .order_by('survey__voter_id', '-date', '-created_at', '-id')
    )
    for feedback in feedback_qs:
        survey = feedback.survey
        voter_id = survey.voter_id if survey else None
        if voter_id and voter_id not in latest_feedback:
            latest_feedback[voter_id] = feedback

    # ── Fallback: find feedbacks where survey.voter_id is null, match by name ──
    missing_ids = expanded_voter_id_set - set(latest_feedback.keys())
    if missing_ids and name_to_voter_id:
        # Get all feedbacks where survey has no voter_id
        name_fb_qs = (
            TelecallingFeedback.objects
            .filter(is_active=True, survey__voter_id__isnull=True)
            .select_related('survey')
            .order_by('-date', '-created_at', '-id')
        )
        for feedback in name_fb_qs:
            survey = feedback.survey
            if not survey or not survey.voter_name:
                continue
            name_key = survey.voter_name.strip().lower()
            voter_id = name_to_voter_id.get(name_key)
            if voter_id and voter_id in missing_ids and voter_id not in latest_feedback:
                latest_feedback[voter_id] = feedback

    surveyed_voter_ids = set(
        FieldSurvey.objects
        .filter(is_active=True, voter_id__in=expanded_voter_id_set)
        .exclude(voter_id__isnull=True)
        .values_list('voter_id', flat=True)
        .distinct()
    )
    voter_ids_by_phone = defaultdict(set)
    for voter_id, meta in voter_meta.items():
        for phone in meta.get('phones') or ():
            voter_ids_by_phone[phone].add(voter_id)

    # ── Build status map ──
    base_status_map: Dict[int, dict] = {}
    for voter_id in expanded_voter_id_set:
        feedback = latest_feedback.get(voter_id)
        latest_assignment_info = latest_assignment.get(voter_id, {})
        has_assignment = bool(latest_assignment_info)

        if not has_assignment:
            status = 'unassigned'
            is_locked = False
        elif not feedback:
            status = 'assigned'
            is_locked = True
        elif feedback.action == 'followup_not_required':
            status = 'completed'
            is_locked = True
        elif feedback.followup_type == 'field_survey':
            status = 'pending_field_survey'
            is_locked = True
        else:
            # followup_required + telephonic (or empty type)
            latest_assignment_ts = latest_assignment_info.get('created_at')
            feedback_ts = feedback.created_at
            if latest_assignment_ts and feedback_ts and latest_assignment_ts > feedback_ts:
                status = 'reassigned'
                is_locked = True
            else:
                status = 'pending_followup'
                is_locked = False

        base_status_map[voter_id] = {
            'status': status,
            'label': WORKFLOW_LABELS.get(status, status.replace('_', ' ').title()),
            'is_locked': is_locked,
            'telecaller_id': latest_assignment_info.get('telecaller_id'),
            'telecaller_name': latest_assignment_info.get('telecaller_name', ''),
            'telecaller_phone': latest_assignment_info.get('telecaller_phone', ''),
        }

    status_map: Dict[int, dict] = {}
    for voter_id in current_voter_ids:
        resolved = dict(base_status_map.get(voter_id, {
            'status': 'unassigned',
            'label': WORKFLOW_LABELS['unassigned'],
            'is_locked': False,
            'telecaller_id': None,
            'telecaller_name': '',
            'telecaller_phone': '',
        }))
        current_meta = voter_meta.get(voter_id, {})
        current_booth_id = current_meta.get('booth_id')

        if resolved['status'] == 'unassigned' and current_booth_id:
            related_assignment_info = None
            cross_status = ''
            for phone in current_meta.get('phones') or ():
                for related_voter_id in voter_ids_by_phone.get(phone, ()):
                    if related_voter_id == voter_id:
                        continue
                    related_meta = voter_meta.get(related_voter_id, {})
                    related_booth_id = related_meta.get('booth_id')
                    if not related_booth_id or related_booth_id == current_booth_id:
                        continue
                    has_related_assignment = related_voter_id in latest_assignment
                    has_related_contact = has_related_assignment and related_voter_id in surveyed_voter_ids
                    if has_related_contact:
                        cross_status = 'already_contacted'
                        related_assignment_info = latest_assignment.get(related_voter_id)
                        break
                    if has_related_assignment:
                        cross_status = 'already_assigned'
                        related_assignment_info = latest_assignment.get(related_voter_id)
                if cross_status == 'already_contacted':
                    break

            if cross_status:
                resolved['status'] = cross_status
                resolved['label'] = WORKFLOW_LABELS[cross_status]
                resolved['is_locked'] = True
                resolved['telecaller_id'] = related_assignment_info.get('telecaller_id') if related_assignment_info else None
                resolved['telecaller_name'] = related_assignment_info.get('telecaller_name', '') if related_assignment_info else ''
                resolved['telecaller_phone'] = related_assignment_info.get('telecaller_phone', '') if related_assignment_info else ''

        status_map[voter_id] = resolved

    return status_map
