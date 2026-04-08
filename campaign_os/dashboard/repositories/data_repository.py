from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from django.db.models import Case, CharField, Count, F, Q, Sum, Value, When

from campaign_os.activities.models import FieldSurvey
from campaign_os.campaigns.models import Task
from campaign_os.masters.models import Booth, Panchayat, PollingArea, Union, VolunteerRole
from campaign_os.telecalling.models import (
    TelecallingAssignment,
    TelecallingAssignmentVoter,
    TelecallingFeedback,
)
from campaign_os.volunteers.models import Volunteer
from campaign_os.voters.models import Voter


@dataclass
class DashboardFilters:
    date: date | None = None
    block: str = ''
    union: str = ''
    panchayat: str = ''
    booth: str = ''
    telecaller: str = ''
    volunteer_role: str = ''
    limit: int = 500
    block_id: int | None = None
    block_name: str = ''
    union_id: int | None = None
    union_name: str = ''
    panchayat_id: int | None = None
    panchayat_name: str = ''
    booth_id: int | None = None
    booth_number: str = ''
    booth_label: str = ''
    telecaller_id: int | None = None
    telecaller_name: str = ''
    telecaller_ids: tuple[int, ...] = ()
    telecaller_names: tuple[str, ...] = ()

    @property
    def has_telecaller_scope(self) -> bool:
        return bool(self.telecaller or self.volunteer_role or self.telecaller_ids or self.telecaller_names)

    @property
    def has_geography_scope(self) -> bool:
        return bool(
            self.block
            or self.union
            or self.panchayat
            or self.booth
            or self.block_id
            or self.union_id
            or self.panchayat_id
            or self.booth_id
        )


class DataRepository:
    def resolve_filters(self, filters: DashboardFilters) -> DashboardFilters:
        self._resolve_block(filters)
        self._resolve_union(filters)
        self._resolve_panchayat(filters)
        self._resolve_booth(filters)
        self._resolve_telecaller(filters)
        return filters

    def _resolve_block(self, filters: DashboardFilters) -> None:
        value = (filters.block or '').strip()
        if not value:
            return

        queryset = PollingArea.objects.filter(is_active=True)
        block = None
        if value.isdigit():
            block = queryset.filter(id=int(value)).first()
        if block is None:
            block = queryset.filter(
                Q(name__iexact=value) | Q(code__iexact=value)
            ).first()
        if block:
            filters.block_id = block.id
            filters.block_name = block.name or value
        else:
            filters.block_name = value

    def _resolve_union(self, filters: DashboardFilters) -> None:
        value = (filters.union or '').strip()
        if not value:
            return

        queryset = Union.objects.filter(is_active=True).select_related('block')
        if filters.block_id:
            queryset = queryset.filter(block_id=filters.block_id)
        union = None
        if value.isdigit():
            union = queryset.filter(id=int(value)).first()
        if union is None:
            union = queryset.filter(
                Q(name__iexact=value) | Q(code__iexact=value)
            ).first()
        if union:
            filters.union_id = union.id
            filters.union_name = union.name or value
            if union.block_id and not filters.block_id:
                filters.block_id = union.block_id
                filters.block_name = union.block.name if union.block_id else filters.block_name
        else:
            filters.union_name = value

    def _resolve_panchayat(self, filters: DashboardFilters) -> None:
        value = (filters.panchayat or '').strip()
        if not value:
            return

        queryset = Panchayat.objects.filter(is_active=True).select_related('union__block')
        if filters.union_id:
            queryset = queryset.filter(union_id=filters.union_id)
        elif filters.block_id:
            queryset = queryset.filter(union__block_id=filters.block_id)

        panchayat = None
        if value.isdigit():
            panchayat = queryset.filter(id=int(value)).first()
        if panchayat is None:
            panchayat = queryset.filter(
                Q(name__iexact=value) | Q(code__iexact=value)
            ).first()
        if panchayat:
            filters.panchayat_id = panchayat.id
            filters.panchayat_name = panchayat.name or value
            if panchayat.union_id and not filters.union_id:
                filters.union_id = panchayat.union_id
                filters.union_name = panchayat.union.name if panchayat.union_id else filters.union_name
            if panchayat.union_id and panchayat.union.block_id and not filters.block_id:
                filters.block_id = panchayat.union.block_id
                filters.block_name = panchayat.union.block.name if panchayat.union.block_id else filters.block_name
        else:
            filters.panchayat_name = value

    def _resolve_booth(self, filters: DashboardFilters) -> None:
        booth_value = (filters.booth or '').strip()
        if not booth_value:
            return

        booth_qs = Booth.objects.filter(is_active=True).select_related('panchayat__union__block')
        booth_qs = self._filter_booth_queryset(booth_qs, filters)
        booth = None
        if booth_value.isdigit():
            booth = booth_qs.filter(id=int(booth_value)).first()
            if booth is None:
                booth = booth_qs.filter(number__iexact=booth_value).first()
        else:
            booth = booth_qs.filter(
                Q(number__iexact=booth_value)
                | Q(code__iexact=booth_value)
                | Q(name__iexact=booth_value)
            ).first()

        if booth is None:
            filters.booth_number = booth_value
            filters.booth_label = booth_value
            return

        filters.booth_id = booth.id
        filters.booth_number = booth.number or booth_value
        filters.booth_label = f"{booth.number or booth.id} - {booth.name or 'Booth'}"

    def _resolve_telecaller(self, filters: DashboardFilters) -> None:
        telecaller_value = (filters.telecaller or '').strip()
        role_value = (filters.volunteer_role or '').strip()

        volunteer_qs = Volunteer.objects.filter(is_active=True).select_related('user', 'volunteer_role')

        names: set[str] = set()
        ids: set[int] = set()

        def add_volunteer(volunteer: Volunteer) -> None:
            if volunteer.id:
                ids.add(volunteer.id)
            for candidate in (
                volunteer.name,
                getattr(volunteer.user, 'username', None),
            ):
                if candidate:
                    names.add(candidate.strip())

        if telecaller_value:
            if telecaller_value.isdigit():
                volunteer = volunteer_qs.filter(id=int(telecaller_value)).first()
                if volunteer:
                    filters.telecaller_id = volunteer.id
                    filters.telecaller_name = volunteer.name or telecaller_value
                    add_volunteer(volunteer)
                else:
                    filters.telecaller_id = int(telecaller_value)
                    ids.add(int(telecaller_value))
            else:
                matches = volunteer_qs.filter(
                    Q(name__iexact=telecaller_value)
                    | Q(user__username__iexact=telecaller_value)
                    | Q(phone__iexact=telecaller_value)
                )
                matched = False
                for volunteer in matches:
                    matched = True
                    add_volunteer(volunteer)
                    filters.telecaller_name = volunteer.name or telecaller_value
                    if filters.telecaller_id is None:
                        filters.telecaller_id = volunteer.id
                if not matched:
                    names.add(telecaller_value)
                    filters.telecaller_name = telecaller_value
        elif role_value:
            role_matches = volunteer_qs.filter(
                Q(role__iexact=role_value) | Q(volunteer_role__name__iexact=role_value)
            )
            for volunteer in role_matches:
                add_volunteer(volunteer)

        filters.telecaller_ids = tuple(sorted(ids))
        filters.telecaller_names = tuple(sorted({name for name in names if name}))

    def _name_match_q(self, fields: Iterable[str], names: Iterable[str]) -> Q:
        q = Q()
        matched = False
        for field in fields:
            for name in names:
                matched = True
                q |= Q(**{f'{field}__iexact': name})
        return q if matched else Q(pk__isnull=True)

    def _field_name(self, prefix: str, field: str) -> str:
        return f'{prefix}{field}' if prefix else field

    def _filter_booth_queryset(self, queryset, filters: DashboardFilters):
        if filters.block_id:
            queryset = queryset.filter(panchayat__union__block_id=filters.block_id)
        elif filters.block:
            queryset = queryset.filter(
                Q(panchayat__union__block__name__iexact=filters.block)
                | Q(panchayat__union__block__code__iexact=filters.block)
            )

        if filters.union_id:
            queryset = queryset.filter(panchayat__union_id=filters.union_id)
        elif filters.union:
            queryset = queryset.filter(
                Q(panchayat__union__name__iexact=filters.union)
                | Q(panchayat__union__code__iexact=filters.union)
            )

        if filters.panchayat_id:
            queryset = queryset.filter(panchayat_id=filters.panchayat_id)
        elif filters.panchayat:
            queryset = queryset.filter(
                Q(panchayat__name__iexact=filters.panchayat)
                | Q(panchayat__code__iexact=filters.panchayat)
            )

        return queryset

    def _apply_booth_scope(self, queryset, prefix: str, filters: DashboardFilters):
        if filters.block_id:
            queryset = queryset.filter(**{
                self._field_name(prefix, 'panchayat__union__block_id'): filters.block_id
            })
        elif filters.block:
            queryset = queryset.filter(
                Q(**{self._field_name(prefix, 'panchayat__union__block__name__iexact'): filters.block})
                | Q(**{self._field_name(prefix, 'panchayat__union__block__code__iexact'): filters.block})
            )

        if filters.union_id:
            queryset = queryset.filter(**{
                self._field_name(prefix, 'panchayat__union_id'): filters.union_id
            })
        elif filters.union:
            queryset = queryset.filter(
                Q(**{self._field_name(prefix, 'panchayat__union__name__iexact'): filters.union})
                | Q(**{self._field_name(prefix, 'panchayat__union__code__iexact'): filters.union})
            )

        if filters.panchayat_id:
            queryset = queryset.filter(**{
                self._field_name(prefix, 'panchayat_id'): filters.panchayat_id
            })
        elif filters.panchayat:
            queryset = queryset.filter(
                Q(**{self._field_name(prefix, 'panchayat__name__iexact'): filters.panchayat})
                | Q(**{self._field_name(prefix, 'panchayat__code__iexact'): filters.panchayat})
            )

        return queryset

    def _get_scoped_booth_values(self, filters: DashboardFilters):
        booth_qs = self._filter_booth_queryset(
            Booth.objects.filter(is_active=True),
            filters,
        )

        if filters.booth_id:
            booth_qs = booth_qs.filter(id=filters.booth_id)
        elif filters.booth:
            booth_value = filters.booth.strip()
            booth_qs = booth_qs.filter(
                Q(number__iexact=booth_value)
                | Q(code__iexact=booth_value)
                | Q(name__iexact=booth_value)
            )

        rows = list(booth_qs.values('id', 'number', 'name', 'code'))
        booth_ids = tuple(row['id'] for row in rows if row.get('id'))
        booth_numbers = tuple(row['number'] for row in rows if row.get('number'))
        booth_names = tuple(row['name'] for row in rows if row.get('name'))
        booth_codes = tuple(row['code'] for row in rows if row.get('code'))
        booth_texts = tuple(
            sorted({value for value in [*booth_numbers, *booth_names, *booth_codes] if value})
        )
        return {
            'ids': booth_ids,
            'numbers': booth_numbers,
            'names': booth_names,
            'codes': booth_codes,
            'texts': booth_texts,
        }

    def get_survey_queryset(self, filters: DashboardFilters):
        queryset = FieldSurvey.objects.filter(is_active=True).select_related('voter__booth')

        if filters.date:
            queryset = queryset.filter(survey_date=filters.date)

        if filters.has_geography_scope:
            booth_scope = self._get_scoped_booth_values(filters)
            scope_q = Q()
            has_scope = False
            if booth_scope['ids']:
                scope_q |= Q(voter__booth_id__in=booth_scope['ids'])
                has_scope = True
            if booth_scope['numbers']:
                scope_q |= Q(booth_no__in=booth_scope['numbers'])
                has_scope = True
            if not has_scope:
                return queryset.none()
            queryset = queryset.filter(scope_q)

        if filters.booth_id:
            booth_q = Q(voter__booth_id=filters.booth_id)
            if filters.booth_number:
                booth_q |= Q(booth_no__iexact=filters.booth_number)
            queryset = queryset.filter(booth_q)
        elif filters.booth:
            booth_value = filters.booth.strip()
            queryset = queryset.filter(
                Q(booth_no__iexact=booth_value)
                | Q(voter__booth__number__iexact=booth_value)
                | Q(voter__booth__code__iexact=booth_value)
                | Q(voter__booth__name__iexact=booth_value)
            )

        if filters.has_telecaller_scope:
            if filters.telecaller_names:
                queryset = queryset.filter(
                    self._name_match_q(['surveyed_by', 'assigned_volunteer'], filters.telecaller_names)
                )
            else:
                queryset = queryset.none()

        return queryset

    def get_feedback_queryset(self, filters: DashboardFilters):
        queryset = TelecallingFeedback.objects.filter(is_active=True).select_related('survey__voter__booth')

        if filters.date:
            queryset = queryset.filter(date=filters.date)

        if filters.has_geography_scope:
            booth_scope = self._get_scoped_booth_values(filters)
            scope_q = Q()
            has_scope = False
            if booth_scope['ids']:
                scope_q |= Q(survey__voter__booth_id__in=booth_scope['ids'])
                has_scope = True
            if booth_scope['numbers']:
                scope_q |= Q(survey__booth_no__in=booth_scope['numbers'])
                has_scope = True
            if not has_scope:
                return queryset.none()
            queryset = queryset.filter(scope_q)

        if filters.booth_id:
            booth_q = Q(survey__voter__booth_id=filters.booth_id)
            if filters.booth_number:
                booth_q |= Q(survey__booth_no__iexact=filters.booth_number)
            queryset = queryset.filter(booth_q)
        elif filters.booth:
            booth_value = filters.booth.strip()
            queryset = queryset.filter(
                Q(survey__booth_no__iexact=booth_value)
                | Q(survey__voter__booth__number__iexact=booth_value)
                | Q(survey__voter__booth__code__iexact=booth_value)
                | Q(survey__voter__booth__name__iexact=booth_value)
            )

        if filters.has_telecaller_scope:
            if filters.telecaller_names:
                queryset = queryset.filter(
                    self._name_match_q(
                        ['telecaller_name', 'survey__surveyed_by', 'survey__assigned_volunteer'],
                        filters.telecaller_names,
                    )
                )
            else:
                queryset = queryset.none()

        return queryset

    def get_assignment_queryset(self, filters: DashboardFilters):
        queryset = TelecallingAssignment.objects.filter(is_active=True)

        if filters.date:
            queryset = queryset.filter(assigned_date=filters.date)

        if filters.telecaller_ids:
            queryset = queryset.filter(
                Q(telecaller_id__in=filters.telecaller_ids)
                | self._name_match_q(['telecaller_name'], filters.telecaller_names)
            )
        elif filters.telecaller_names:
            queryset = queryset.filter(self._name_match_q(['telecaller_name'], filters.telecaller_names))
        elif filters.telecaller or filters.volunteer_role:
            queryset = queryset.none()

        if filters.has_geography_scope:
            booth_scope = self._get_scoped_booth_values(filters)
            scope_q = Q()
            has_scope = False
            if booth_scope['ids']:
                scope_q |= Q(voters__voter__booth_id__in=booth_scope['ids'])
                has_scope = True
            if booth_scope['texts']:
                scope_q |= Q(voters__booth_name__in=booth_scope['texts'])
                has_scope = True
            if not has_scope:
                return queryset.none()
            queryset = queryset.filter(scope_q)

        if filters.booth_id:
            booth_q = Q(voters__voter__booth_id=filters.booth_id)
            if filters.booth_number:
                booth_q |= Q(voters__booth_name__icontains=filters.booth_number)
            queryset = queryset.filter(booth_q)
        elif filters.booth:
            booth_value = filters.booth.strip()
            queryset = queryset.filter(
                Q(voters__voter__booth__number__iexact=booth_value)
                | Q(voters__voter__booth__code__iexact=booth_value)
                | Q(voters__voter__booth__name__iexact=booth_value)
                | Q(voters__booth_name__iexact=booth_value)
            )

        return queryset.distinct()

    def get_assignment_voter_queryset(self, filters: DashboardFilters):
        queryset = TelecallingAssignmentVoter.objects.filter(
            assignment__is_active=True
        ).select_related('assignment', 'voter__booth')

        if filters.date:
            queryset = queryset.filter(assignment__assigned_date=filters.date)

        if filters.telecaller_ids:
            queryset = queryset.filter(
                Q(assignment__telecaller_id__in=filters.telecaller_ids)
                | self._name_match_q(['assignment__telecaller_name'], filters.telecaller_names)
            )
        elif filters.telecaller_names:
            queryset = queryset.filter(
                self._name_match_q(['assignment__telecaller_name'], filters.telecaller_names)
            )
        elif filters.telecaller or filters.volunteer_role:
            queryset = queryset.none()

        if filters.has_geography_scope:
            booth_scope = self._get_scoped_booth_values(filters)
            scope_q = Q()
            has_scope = False
            if booth_scope['ids']:
                scope_q |= Q(voter__booth_id__in=booth_scope['ids'])
                has_scope = True
            if booth_scope['texts']:
                scope_q |= Q(booth_name__in=booth_scope['texts'])
                has_scope = True
            if not has_scope:
                return queryset.none()
            queryset = queryset.filter(scope_q)

        if filters.booth_id:
            booth_q = Q(voter__booth_id=filters.booth_id)
            if filters.booth_number:
                booth_q |= Q(booth_name__icontains=filters.booth_number)
            queryset = queryset.filter(booth_q)
        elif filters.booth:
            booth_value = filters.booth.strip()
            queryset = queryset.filter(
                Q(voter__booth__number__iexact=booth_value)
                | Q(voter__booth__code__iexact=booth_value)
                | Q(voter__booth__name__iexact=booth_value)
                | Q(booth_name__iexact=booth_value)
            )

        return queryset

    def get_task_queryset(self, filters: DashboardFilters):
        queryset = Task.objects.filter(is_active=True).select_related(
            'task_category',
            'booth',
            'ward',
            'volunteer_role',
            'coordinator',
            'delivery_incharge',
        )

        if filters.date:
            queryset = queryset.filter(expected_datetime__date=filters.date)

        if filters.block_id:
            queryset = queryset.filter(
                Q(block_id=filters.block_id)
                | Q(union__block_id=filters.block_id)
                | Q(panchayat__union__block_id=filters.block_id)
                | Q(booth__panchayat__union__block_id=filters.block_id)
            )
        elif filters.block:
            queryset = queryset.filter(
                Q(block__name__iexact=filters.block)
                | Q(block__code__iexact=filters.block)
                | Q(union__block__name__iexact=filters.block)
                | Q(panchayat__union__block__name__iexact=filters.block)
                | Q(booth__panchayat__union__block__name__iexact=filters.block)
            )

        if filters.union_id:
            queryset = queryset.filter(
                Q(union_id=filters.union_id)
                | Q(panchayat__union_id=filters.union_id)
                | Q(booth__panchayat__union_id=filters.union_id)
            )
        elif filters.union:
            queryset = queryset.filter(
                Q(union__name__iexact=filters.union)
                | Q(union__code__iexact=filters.union)
                | Q(panchayat__union__name__iexact=filters.union)
                | Q(booth__panchayat__union__name__iexact=filters.union)
            )

        if filters.panchayat_id:
            queryset = queryset.filter(
                Q(panchayat_id=filters.panchayat_id)
                | Q(booth__panchayat_id=filters.panchayat_id)
            )
        elif filters.panchayat:
            queryset = queryset.filter(
                Q(panchayat__name__iexact=filters.panchayat)
                | Q(panchayat__code__iexact=filters.panchayat)
                | Q(booth__panchayat__name__iexact=filters.panchayat)
            )

        if filters.booth_id:
            queryset = queryset.filter(booth_id=filters.booth_id)
        elif filters.booth:
            booth_value = filters.booth.strip()
            queryset = queryset.filter(
                Q(booth__number__iexact=booth_value)
                | Q(booth__code__iexact=booth_value)
                | Q(booth__name__iexact=booth_value)
            )

        if filters.volunteer_role:
            queryset = queryset.filter(
                Q(volunteer_role__name__iexact=filters.volunteer_role)
                | Q(coordinator__role__iexact=filters.volunteer_role)
                | Q(delivery_incharge__role__iexact=filters.volunteer_role)
            )

        if filters.telecaller_ids:
            queryset = queryset.filter(
                Q(coordinator_id__in=filters.telecaller_ids)
                | Q(delivery_incharge_id__in=filters.telecaller_ids)
            )

        return queryset

    def get_total_voter_count(self, filters: DashboardFilters, assignment_scope_total: int = 0) -> int:
        if filters.has_telecaller_scope:
            return assignment_scope_total

        if filters.booth_id:
            linked_total = Voter.objects.filter(is_active=True, booth_id=filters.booth_id).count()
            booth = Booth.objects.filter(is_active=True, id=filters.booth_id).only('total_voters').first()
            stored_total = booth.total_voters or 0 if booth else 0
            return max(linked_total, stored_total)

        if filters.has_geography_scope:
            voter_qs = Voter.objects.filter(is_active=True)
            voter_qs = self._apply_booth_scope(voter_qs, 'booth__', filters)
            if filters.booth:
                booth_value = filters.booth.strip()
                voter_qs = voter_qs.filter(
                    Q(booth__number__iexact=booth_value)
                    | Q(booth__code__iexact=booth_value)
                    | Q(booth__name__iexact=booth_value)
                )
            linked_total = voter_qs.count()
            booth_qs = self._filter_booth_queryset(Booth.objects.filter(is_active=True), filters)
            if filters.booth and not filters.booth_id:
                booth_value = filters.booth.strip()
                booth_qs = booth_qs.filter(
                    Q(number__iexact=booth_value)
                    | Q(code__iexact=booth_value)
                    | Q(name__iexact=booth_value)
                )
            stored_total = booth_qs.aggregate(total=Sum('total_voters')).get('total') or 0
            return max(linked_total, stored_total)

        return Voter.objects.filter(is_active=True).count()

    def get_assignment_scope_voter_count(self, filters: DashboardFilters) -> int:
        assignment_voters = self.get_assignment_voter_queryset(filters)
        linked_total = assignment_voters.exclude(voter_id__isnull=True).values('voter_id').distinct().count()
        unlinked_total = assignment_voters.filter(voter_id__isnull=True).count()
        return linked_total + unlinked_total

    def get_booth_ranking_rows(self, filters: DashboardFilters):
        survey_filter = Q(voters__field_surveys__is_active=True)
        if filters.date:
            survey_filter &= Q(voters__field_surveys__survey_date=filters.date)
        if filters.has_telecaller_scope:
            if filters.telecaller_names:
                survey_filter &= self._name_match_q(
                    ['voters__field_surveys__surveyed_by', 'voters__field_surveys__assigned_volunteer'],
                    filters.telecaller_names,
                )
            else:
                return []

        booths = Booth.objects.filter(is_active=True).select_related('panchayat__union__block')
        booths = self._filter_booth_queryset(booths, filters)
        if filters.booth_id:
            booths = booths.filter(id=filters.booth_id)
        elif filters.booth:
            booth_value = filters.booth.strip()
            booths = booths.filter(
                Q(number__iexact=booth_value)
                | Q(code__iexact=booth_value)
                | Q(name__iexact=booth_value)
            )

        booths = booths.annotate(
            linked_total_voters=Count('voters', filter=Q(voters__is_active=True), distinct=True),
            surveyed_voters=Count('voters__field_surveys', filter=survey_filter, distinct=True),
            positive=Count(
                'voters__field_surveys',
                filter=survey_filter & Q(voters__field_surveys__support_level='positive'),
                distinct=True,
            ),
            negative=Count(
                'voters__field_surveys',
                filter=survey_filter & Q(voters__field_surveys__support_level='negative'),
                distinct=True,
            ),
            neutral=Count(
                'voters__field_surveys',
                filter=survey_filter & Q(voters__field_surveys__support_level='neutral'),
                distinct=True,
            ),
            followup=Count(
                'voters__field_surveys',
                filter=survey_filter & Q(voters__field_surveys__response_status='need_followup'),
                distinct=True,
            ),
        ).order_by('number', 'name')
        return list(booths)

    def get_telecaller_assignment_rows(self, filters: DashboardFilters):
        queryset = self.get_assignment_queryset(filters)
        return list(
            queryset.values('telecaller_id', 'telecaller_name').annotate(
                assigned_voters=Count('voters', distinct=True),
                assigned_booths=Count('voters__voter__booth', distinct=True),
            )
        )

    def get_telecaller_survey_rows(self, filters: DashboardFilters):
        queryset = self.get_survey_queryset(filters).annotate(
            telecaller_key=Case(
                When(surveyed_by__gt='', then=F('surveyed_by')),
                When(assigned_volunteer__gt='', then=F('assigned_volunteer')),
                default=Value('Unassigned'),
                output_field=CharField(),
            )
        )
        return list(
            queryset.values('telecaller_key').annotate(
                total_records=Count('id'),
                linked_voters=Count('voter', distinct=True),
                unlinked_records=Count('id', filter=Q(voter__isnull=True)),
                positive=Count('id', filter=Q(support_level='positive')),
                negative=Count('id', filter=Q(support_level='negative')),
                neutral=Count('id', filter=Q(support_level='neutral')),
            )
        )

    def get_telecaller_feedback_rows(self, filters: DashboardFilters):
        queryset = self.get_feedback_queryset(filters)
        return list(
            queryset.values('telecaller_name').annotate(
                required_surveys=Count('survey', filter=Q(action='followup_required', survey__isnull=False), distinct=True),
                closed_surveys=Count('survey', filter=Q(action='followup_not_required', survey__isnull=False), distinct=True),
                required_loose=Count('id', filter=Q(action='followup_required', survey__isnull=True)),
                closed_loose=Count('id', filter=Q(action='followup_not_required', survey__isnull=True)),
            )
        )

    def get_telecaller_directory(self, filters: DashboardFilters):
        queryset = Volunteer.objects.filter(is_active=True).select_related('user', 'volunteer_role')

        if filters.telecaller_ids:
            queryset = queryset.filter(id__in=filters.telecaller_ids)
        elif filters.telecaller_names:
            queryset = queryset.filter(
                self._name_match_q(['name', 'user__username'], filters.telecaller_names)
            )

        if filters.volunteer_role:
            queryset = queryset.filter(
                Q(role__iexact=filters.volunteer_role)
                | Q(volunteer_role__name__iexact=filters.volunteer_role)
            )

        return list(
            queryset.values(
                'id',
                'name',
                'phone',
                'role',
                'volunteer_role__name',
                'user__username',
            ).annotate(
                booth_count=Count('booths', distinct=True),
            )
        )

    def get_booth_options(self):
        return list(
            Booth.objects.filter(is_active=True)
            .select_related('panchayat__union__block')
            .values(
                'id', 'number', 'name',
                'panchayat_id', 'panchayat__name',
                'panchayat__union_id', 'panchayat__union__name',
                'panchayat__union__block_id', 'panchayat__union__block__name',
            )
            .order_by('number', 'name')
        )

    def get_telecaller_options(self):
        return list(
            Volunteer.objects.filter(is_active=True)
            .select_related('volunteer_role')
            .values('id', 'name', 'phone', 'role', 'volunteer_role__name')
            .order_by('name')
        )

    def get_block_options(self):
        return list(
            PollingArea.objects.filter(is_active=True)
            .values('id', 'name', 'code')
            .order_by('name')
        )

    def get_union_options(self):
        return list(
            Union.objects.filter(is_active=True)
            .select_related('block')
            .values('id', 'name', 'code', 'block_id', 'block__name')
            .order_by('name')
        )

    def get_panchayat_options(self):
        return list(
            Panchayat.objects.filter(is_active=True)
            .select_related('union__block')
            .values(
                'id', 'name', 'code',
                'union_id', 'union__name',
                'union__block_id', 'union__block__name',
            )
            .order_by('name')
        )

    def get_volunteer_role_options(self):
        master_roles = list(
            VolunteerRole.objects.filter(is_active=True)
            .values_list('name', flat=True)
            .order_by('order', 'name')
        )
        free_roles = list(
            Volunteer.objects.filter(is_active=True)
            .exclude(role__isnull=True)
            .exclude(role__exact='')
            .values_list('role', flat=True)
            .distinct()
            .order_by('role')
        )
        merged = []
        seen = set()
        for role in [*master_roles, *free_roles]:
            clean = (role or '').strip()
            key = clean.lower()
            if clean and key not in seen:
                seen.add(key)
                merged.append(clean)
        return merged
