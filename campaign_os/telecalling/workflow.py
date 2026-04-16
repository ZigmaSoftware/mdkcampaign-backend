from __future__ import annotations

from collections import defaultdict
import re
from typing import Dict, Iterable
from time import monotonic

from campaign_os.activities.models import FieldSurvey
from campaign_os.voters.models import Voter
from django.db.models import Q
from django.db.models.functions import Lower, Trim

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
WORKFLOW_CACHE_TTL_SECONDS = 20
_voter_status_cache: Dict[tuple, tuple[float, Dict[int, dict]]] = {}
_nonvoter_status_cache: Dict[tuple, tuple[float, Dict[int, dict]]] = {}


def _cache_get(cache_store, key):
    payload = cache_store.get(key)
    if not payload:
        return None
    expires_at, value = payload
    if monotonic() >= expires_at:
        cache_store.pop(key, None)
        return None
    return value


def _cache_set(cache_store, key, value):
    cache_store[key] = (monotonic() + WORKFLOW_CACHE_TTL_SECONDS, value)


def clear_workflow_caches():
    _voter_status_cache.clear()
    _nonvoter_status_cache.clear()


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


def _normalize_name(value) -> str:
    return str(value or '').strip().lower()


def _contact_key(name, phone) -> str:
    normalized_name = _normalize_name(name)
    normalized_phone = _normalize_phone(phone)
    if not normalized_name or not normalized_phone:
        return ''
    return f'{normalized_name}::{normalized_phone}'


def _contact_keys(name, phones) -> set[str]:
    return {
        key
        for key in (_contact_key(name, phone) for phone in (phones or ()))
        if key
    }


def _name_filter(field_name: str, names: set[str]) -> Q:
    query = Q()
    for name in names:
        if name:
            query |= Q(**{f'{field_name}__iexact': name})
    return query


def _iter_lookup_rows(base_queryset, *, name_field: str, phone_field: str, phone_values: set[str], normalized_names: set[str]):
    seen_ids: set[int] = set()
    querysets = []

    if phone_values:
        querysets.append(base_queryset.filter(**{f'{phone_field}__in': tuple(phone_values)}))

    if normalized_names:
        if len(normalized_names) <= 50:
            querysets.append(base_queryset.filter(_name_filter(name_field, normalized_names)))
        else:
            querysets.append(
                base_queryset
                .annotate(_lookup_name=Lower(Trim(name_field)))
                .filter(_lookup_name__in=list(normalized_names))
            )

    for queryset in querysets:
        for row in queryset:
            if row.id in seen_ids:
                continue
            seen_ids.add(row.id)
            yield row


def _build_assignment_contact_lookups(phone_values: set[str], names: set[str] | None = None):
    latest_any_by_key: Dict[str, dict] = {}
    latest_nonvoter_by_key: Dict[str, dict] = {}
    normalized_names = {name for name in (names or set()) if name}
    if not phone_values and not normalized_names:
        return latest_any_by_key, latest_nonvoter_by_key

    assignment_base_qs = (
        TelecallingAssignmentVoter.objects
        .select_related('assignment', 'voter')
        .order_by('-assignment__created_at', '-assignment_id', '-id')
    )
    for row in _iter_lookup_rows(
        assignment_base_qs,
        name_field='voter_name',
        phone_field='phone',
        phone_values=phone_values,
        normalized_names=normalized_names,
    ):
        info = {
            'created_at': row.assignment.created_at,
            'telecaller_id': row.assignment.telecaller_id,
            'telecaller_name': row.assignment.telecaller_name or '',
            'telecaller_phone': row.assignment.telecaller_phone or '',
            'entity_type': row.entity_type or 'voter',
        }
        row_phones = {row.phone or ''}
        voter = getattr(row, 'voter', None)
        if voter:
            row_phones.update(getattr(voter, field, '') or '' for field in PHONE_FIELDS)
        for key in _contact_keys(row.voter_name, row_phones):
            latest_any_by_key.setdefault(key, info)
            if info['entity_type'] != 'voter':
                latest_nonvoter_by_key.setdefault(key, info)

    return latest_any_by_key, latest_nonvoter_by_key


def _build_survey_contact_sets(phone_values: set[str], names: set[str] | None = None):
    all_keys: set[str] = set()
    nonvoter_keys: set[str] = set()
    normalized_names = {name for name in (names or set()) if name}
    if not phone_values and not normalized_names:
        return all_keys, nonvoter_keys

    survey_base_qs = (
        FieldSurvey.objects
        .filter(is_active=True)
        .select_related('voter')
        .order_by('-survey_date', '-created_at', '-id')
    )
    for survey in _iter_lookup_rows(
        survey_base_qs,
        name_field='voter_name',
        phone_field='phone',
        phone_values=phone_values,
        normalized_names=normalized_names,
    ):
        survey_phones = {survey.phone or ''}
        voter = getattr(survey, 'voter', None)
        if voter:
            survey_phones.update(getattr(voter, field, '') or '' for field in PHONE_FIELDS)
        for key in _contact_keys(survey.voter_name, survey_phones):
            all_keys.add(key)
            if not survey.voter_id:
                nonvoter_keys.add(key)

    return all_keys, nonvoter_keys


def _resolve_cross_status(contact_keys: set[str], assignment_lookup: Dict[str, dict], surveyed_keys: set[str]):
    fallback_info = None
    for key in contact_keys:
        assignment_info = assignment_lookup.get(key)
        if not assignment_info:
            continue
        if key in surveyed_keys:
            return 'already_contacted', assignment_info
        if fallback_info is None:
            fallback_info = assignment_info
    if fallback_info:
        return 'already_assigned', fallback_info
    return '', None


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

    cache_key = tuple(sorted(voter_id_set))
    cached = _cache_get(_voter_status_cache, cache_key)
    if cached is not None:
        return {voter_id: dict(status) for voter_id, status in cached.items()}

    current_voters = list(
        Voter.objects
        .filter(id__in=voter_id_set)
        .only('id', 'name', 'booth_id', *PHONE_FIELDS)
    )
    current_voter_ids = {voter.id for voter in current_voters}
    current_phone_values = {
        normalized
        for voter in current_voters
        for normalized in _collect_phone_numbers(voter)
    }
    current_name_values = {_normalize_name(voter.name) for voter in current_voters if _normalize_name(voter.name)}
    _, nonvoter_assignment_by_contact = _build_assignment_contact_lookups(current_phone_values, current_name_values)
    _, nonvoter_survey_contact_keys = _build_survey_contact_sets(current_phone_values, current_name_values)

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
            'name': voter.name or '',
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

        contact_keys = _contact_keys(current_meta.get('name'), current_meta.get('phones'))
        cross_entity_status, cross_entity_info = _resolve_cross_status(
            contact_keys,
            nonvoter_assignment_by_contact,
            nonvoter_survey_contact_keys,
        )
        if cross_entity_status and (
            resolved['status'] == 'unassigned' or
            (resolved['status'] == 'already_assigned' and cross_entity_status == 'already_contacted')
        ):
            resolved['status'] = cross_entity_status
            resolved['label'] = WORKFLOW_LABELS[cross_entity_status]
            resolved['is_locked'] = True
            resolved['telecaller_id'] = cross_entity_info.get('telecaller_id') if cross_entity_info else None
            resolved['telecaller_name'] = cross_entity_info.get('telecaller_name', '') if cross_entity_info else ''
            resolved['telecaller_phone'] = cross_entity_info.get('telecaller_phone', '') if cross_entity_info else ''

        status_map[voter_id] = resolved

    _cache_set(_voter_status_cache, cache_key, {voter_id: dict(status) for voter_id, status in status_map.items()})
    return status_map


def build_nonvoter_status_map(entity_type: str, entries: Iterable[dict]) -> Dict[int, dict]:
    """
    Resolve assignment workflow states for volunteer / beneficiary telecalling rows.

    Matching priority:
      1. exact assignment row by (entity_type, source_id)
      2. latest FieldSurvey by normalized name + phone
      3. latest FieldSurvey by normalized name only (fallback when phone is blank)
    """
    normalized_type = (entity_type or '').strip().lower()
    if normalized_type not in {'volunteer', 'beneficiary'}:
        return {}

    prepared_entries = []
    source_ids: set[int] = set()
    names: set[str] = set()
    phone_values: set[str] = set()
    for entry in entries:
        source_id = entry.get('source_id')
        if not source_id:
            continue
        display_name = str(entry.get('name') or '').strip()
        normalized_name = _normalize_name(entry.get('name'))
        phones = {
            _normalize_phone(phone)
            for phone in (entry.get('phones') or [])
            if _normalize_phone(phone)
        }
        prepared_entries.append({
            'source_id': int(source_id),
            'display_name': display_name,
            'name': normalized_name,
            'phones': phones,
        })
        source_ids.add(int(source_id))
        if normalized_name:
            names.add(normalized_name)
        phone_values.update(phones)

    if not prepared_entries:
        return {}

    cache_key = (
        normalized_type,
        tuple(sorted(
            (
                entry['source_id'],
                entry['name'],
                tuple(sorted(entry['phones'])),
            )
            for entry in prepared_entries
        )),
    )
    cached = _cache_get(_nonvoter_status_cache, cache_key)
    if cached is not None:
        return {source_id: dict(status) for source_id, status in cached.items()}

    all_assignment_by_contact, _ = _build_assignment_contact_lookups(phone_values, names)
    all_survey_contact_keys, _ = _build_survey_contact_sets(phone_values, names)

    latest_assignment: Dict[int, dict] = {}
    assignment_qs = (
        TelecallingAssignmentVoter.objects
        .filter(entity_type=normalized_type, source_id__in=source_ids)
        .select_related('assignment')
        .order_by('source_id', '-assignment__created_at', '-assignment_id', '-id')
    )
    for row in assignment_qs:
        source_id = row.source_id
        if source_id and source_id not in latest_assignment:
            latest_assignment[source_id] = {
                'created_at': row.assignment.created_at,
                'telecaller_id': row.assignment.telecaller_id,
                'telecaller_name': row.assignment.telecaller_name or '',
                'telecaller_phone': row.assignment.telecaller_phone or '',
                'name': _normalize_name(row.voter_name),
                'phones': {
                    _normalize_phone(phone)
                    for phone in (row.phone, getattr(getattr(row, 'voter', None), 'phone2', ''))
                    if _normalize_phone(phone)
                },
            }

    survey_by_name_phone = {}
    survey_by_name = {}
    if names or phone_values:
        survey_base_qs = (
            FieldSurvey.objects
            .filter(is_active=True, voter__isnull=True)
            .order_by('-survey_date', '-created_at', '-id')
        )
        for survey in _iter_lookup_rows(
            survey_base_qs,
            name_field='voter_name',
            phone_field='phone',
            phone_values=phone_values,
            normalized_names=names,
        ):
            normalized_name = _normalize_name(survey.voter_name)
            if not normalized_name:
                continue
            normalized_phone = _normalize_phone(survey.phone)
            if normalized_phone:
                survey_by_name_phone.setdefault(f'{normalized_name}::{normalized_phone}', survey)
            survey_by_name.setdefault(normalized_name, survey)

    matched_surveys_by_source: Dict[int, object] = {}
    for entry in prepared_entries:
        matched_survey = None
        for phone in entry['phones']:
            matched_survey = survey_by_name_phone.get(f"{entry['name']}::{phone}")
            if matched_survey:
                break
        if not matched_survey and entry['name']:
            matched_survey = survey_by_name.get(entry['name'])
        if matched_survey:
            matched_surveys_by_source[entry['source_id']] = matched_survey

    latest_feedback: Dict[int, object] = {}
    matched_survey_ids = {survey.id for survey in matched_surveys_by_source.values() if getattr(survey, 'id', None)}
    if matched_survey_ids:
        feedback_qs = (
            TelecallingFeedback.objects
            .filter(is_active=True, survey_id__in=matched_survey_ids)
            .select_related('survey')
            .order_by('survey_id', '-date', '-created_at', '-id')
        )
        for feedback in feedback_qs:
            if feedback.survey_id and feedback.survey_id not in latest_feedback:
                latest_feedback[feedback.survey_id] = feedback

    status_map: Dict[int, dict] = {}
    for entry in prepared_entries:
        source_id = entry['source_id']
        assignment_info = latest_assignment.get(source_id, {})
        feedback = None
        matched_survey = matched_surveys_by_source.get(source_id)
        if matched_survey:
            feedback = latest_feedback.get(matched_survey.id)

        if not assignment_info:
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
            latest_assignment_ts = assignment_info.get('created_at')
            feedback_ts = feedback.created_at
            if latest_assignment_ts and feedback_ts and latest_assignment_ts > feedback_ts:
                status = 'reassigned'
                is_locked = True
            else:
                status = 'pending_followup'
                is_locked = False

        if status == 'unassigned':
            contact_keys = _contact_keys(entry['display_name'], entry['phones'])
            cross_status, cross_assignment_info = _resolve_cross_status(
                contact_keys,
                all_assignment_by_contact,
                all_survey_contact_keys,
            )
            if cross_status:
                status = cross_status
                is_locked = True
                assignment_info = cross_assignment_info or {}

        status_map[source_id] = {
            'status': status,
            'label': WORKFLOW_LABELS.get(status, status.replace('_', ' ').title()),
            'is_locked': is_locked,
            'telecaller_id': assignment_info.get('telecaller_id'),
            'telecaller_name': assignment_info.get('telecaller_name', ''),
            'telecaller_phone': assignment_info.get('telecaller_phone', ''),
        }

    _cache_set(_nonvoter_status_cache, cache_key, {source_id: dict(status) for source_id, status in status_map.items()})
    return status_map
