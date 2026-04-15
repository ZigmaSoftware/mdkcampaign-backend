import re

from django.db import transaction
from django.db.models import Q
from rest_framework import serializers
from django.utils import timezone
from campaign_os.activities.models import FieldSurvey
from .models import TelecallingAssignment, TelecallingAssignmentVoter, TelecallingFeedback


NON_DIGIT_RE = re.compile(r'\D+')


def _normalize_phone(value) -> str:
    raw = str(value or '').strip()
    if not raw:
        return ''
    digits = NON_DIGIT_RE.sub('', raw)
    if len(digits) > 10:
        digits = digits[-10:]
    return digits


def _normalize_name(value) -> str:
    return str(value or '').strip().lower()


def _contact_key(name, phone) -> str:
    normalized_name = _normalize_name(name)
    normalized_phone = _normalize_phone(phone)
    if not normalized_name or not normalized_phone:
        return ''
    return f'{normalized_name}::{normalized_phone}'


def _row_entity_type(row) -> str:
    return (row.get('entity_type') or 'voter').strip().lower()


def _row_source_id(row):
    source_id = row.get('source_id')
    if source_id is not None:
        return source_id
    voter = row.get('voter')
    return getattr(voter, 'id', voter) if voter else None


def _row_contact_keys(row) -> set[str]:
    return {
        key
        for key in (
            _contact_key(row.get('voter_name'), row.get('phone')),
            _contact_key(row.get('voter_name'), row.get('phone2')),
            _contact_key(row.get('voter_name'), row.get('alt_phoneno2')),
            _contact_key(row.get('voter_name'), row.get('alt_phoneno3')),
        )
        if key
    }


def _build_name_query(names: set[str]):
    query = Q()
    for name in names:
        query |= Q(voter_name__iexact=name)
    return query


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

    def _cross_category_conflicts(self, voters_data):
        incoming_by_key = {}
        names = set()

        for row in voters_data:
            entity_type = _row_entity_type(row)
            source_id = _row_source_id(row)
            row_name = str(row.get('voter_name') or '').strip()
            keys = _row_contact_keys(row)
            if not row_name or not keys:
                continue
            names.add(row_name)
            for key in keys:
                incoming_by_key.setdefault(key, []).append({
                    'name': row_name,
                    'entity_type': entity_type,
                    'source_id': source_id,
                    'phone': key.split('::', 1)[1],
                })

        if not incoming_by_key or not names:
            return []

        existing_query = _build_name_query(names)
        if not existing_query:
            return []

        existing_rows = (
            TelecallingAssignmentVoter.objects
            .filter(assignment__is_active=True)
            .filter(existing_query)
            .select_related('assignment', 'voter')
            .order_by('-assignment__created_at', '-assignment_id', '-id')
        )

        conflict_candidates = []
        survey_query = Q()
        for existing in existing_rows:
            existing_entity = (existing.entity_type or 'voter').strip().lower()
            existing_phones = [existing.phone]
            voter = getattr(existing, 'voter', None)
            if voter:
                existing_phones.extend([
                    getattr(voter, 'phone', ''),
                    getattr(voter, 'phone2', ''),
                    getattr(voter, 'alt_phoneno2', ''),
                    getattr(voter, 'alt_phoneno3', ''),
                ])

            for existing_key in {_contact_key(existing.voter_name, phone) for phone in existing_phones}:
                if not existing_key or existing_key not in incoming_by_key:
                    continue

                for incoming in incoming_by_key[existing_key]:
                    if existing_entity == incoming['entity_type']:
                        continue

                    conflict_candidates.append({
                        'name': incoming['name'],
                        'phone': incoming['phone'],
                        'existing_entity': existing_entity,
                        'telecaller': existing.assignment.telecaller_name or '',
                        'key': existing_key,
                    })
                    survey_query |= Q(voter_name__iexact=incoming['name'])

        if not conflict_candidates:
            return []

        contacted_keys = set()
        if survey_query:
            for survey in FieldSurvey.objects.filter(is_active=True).filter(survey_query).select_related('voter'):
                survey_phones = [survey.phone]
                voter = getattr(survey, 'voter', None)
                if voter:
                    survey_phones.extend([
                        getattr(voter, 'phone', ''),
                        getattr(voter, 'phone2', ''),
                        getattr(voter, 'alt_phoneno2', ''),
                        getattr(voter, 'alt_phoneno3', ''),
                    ])
                for key in {_contact_key(survey.voter_name, phone) for phone in survey_phones}:
                    if key:
                        contacted_keys.add(key)

        conflicts = []
        seen = set()
        for candidate in conflict_candidates:
            unique_key = (candidate['key'], candidate['existing_entity'])
            if unique_key in seen:
                continue
            seen.add(unique_key)
            conflicts.append({
                **candidate,
                'status': 'Already Contacted' if candidate['key'] in contacted_keys else 'Already Assigned',
            })

        return conflicts

    def validate(self, attrs):
        voters_data = attrs.get('voters') or []
        conflicts = self._cross_category_conflicts(voters_data)
        if conflicts:
            first = conflicts[0]
            entity_label = first['existing_entity'].replace('_', ' ').title()
            telecaller_note = f" to {first['telecaller']}" if first.get('telecaller') else ''
            extra_count = len(conflicts) - 1
            extra_note = f" and {extra_count} more" if extra_count > 0 else ''
            raise serializers.ValidationError({
                'detail': (
                    f"{first['name']} ({first['phone']}) is {first['status']} "
                    f"as {entity_label}{telecaller_note}{extra_note}. Please refresh the list."
                )
            })
        return attrs

    def create(self, validated_data):
        voters_data = validated_data.pop('voters', [])
        with transaction.atomic():
            assignment  = TelecallingAssignment.objects.create(**validated_data)
            for v in voters_data:
                phone2 = v.pop('phone2', None)
                alt_phoneno2 = v.pop('alt_phoneno2', None)
                alt_phoneno3 = v.pop('alt_phoneno3', None)
                if not v.get('phone'):
                    v['phone'] = phone2 or alt_phoneno2 or alt_phoneno3 or ''
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
