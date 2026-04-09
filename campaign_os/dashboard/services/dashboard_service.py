from django.db.models import Case, CharField, Count, F, IntegerField, Q, Value, When
from django.utils import timezone

from campaign_os.dashboard.repositories.data_repository import DataRepository, DashboardFilters
from campaign_os.dashboard.services.aggregation_service import (
    booth_ranking_score,
    normalize_key,
    safe_pct,
    telecaller_efficiency_score,
)
from campaign_os.voters.models import Voter


GENDER_BUCKETS = (
    ('male', 'Male', Q(gender__in=['m', 'Male'])),
    ('female', 'Female', Q(gender__in=['f', 'Female'])),
    ('other', 'Others', Q(gender__in=['o', 'Other'])),
)

AGE_BUCKETS = (
    ('18_23', '18-23', Q(age__gte=18, age__lte=23)),
    ('23_30', '23-30', Q(age__gt=23, age__lte=30)),
    ('30_40', '30-40', Q(age__gt=30, age__lte=40)),
    ('40_50', '40-50', Q(age__gt=40, age__lte=50)),
    ('50_60', '50-60', Q(age__gt=50, age__lte=60)),
    ('60_70', '60-70', Q(age__gt=60, age__lte=70)),
    ('70_80', '70-80', Q(age__gt=70, age__lte=80)),
    ('80_90', '80-90', Q(age__gt=80, age__lte=90)),
    ('90_plus', '90+', Q(age__gt=90)),
)


class DashboardService:
    def __init__(self):
        self.repo = DataRepository()

    def _build_survey_aggregate_map(self) -> dict:
        aggregate_map = {
            'total_records': Count('id'),
            'linked_voters': Count('voter', distinct=True),
            'unlinked_records': Count('id', filter=Q(voter__isnull=True)),
            'positive': Count('id', filter=Q(support_level='positive')),
            'negative': Count('id', filter=Q(support_level='negative')),
            'neutral': Count('id', filter=Q(support_level='neutral')),
            'aware_yes': Count('id', filter=Q(aware_of_candidate='Yes')),
            'aware_no': Count('id', filter=Q(aware_of_candidate='No')),
            'aware_not_sure': Count('id', filter=Q(aware_of_candidate='Not Sure')),
            'vote_yes': Count('id', filter=Q(likely_to_vote='Yes')),
            'vote_no': Count('id', filter=Q(likely_to_vote='No')),
            'vote_not_sure': Count('id', filter=Q(likely_to_vote='Not Sure')),
            'not_reach': Count('id', filter=Q(response_status='not_reach')),
            'no_answer': Count('id', filter=Q(response_status='no_answer')),
            'wrong_number': Count('id', filter=Q(response_status='wrong_number')),
        }

        for key, _label, gender_q in GENDER_BUCKETS:
            aggregate_map[f'gender_{key}'] = Count('id', filter=gender_q)
            aggregate_map[f'gender_{key}_positive'] = Count('id', filter=gender_q & Q(support_level='positive'))
            aggregate_map[f'gender_{key}_neutral'] = Count('id', filter=gender_q & Q(support_level='neutral'))
            aggregate_map[f'gender_{key}_negative'] = Count('id', filter=gender_q & Q(support_level='negative'))

        for key, _label, age_q in AGE_BUCKETS:
            aggregate_map[f'age_{key}'] = Count('id', filter=age_q)
            aggregate_map[f'age_{key}_positive'] = Count('id', filter=age_q & Q(support_level='positive'))
            aggregate_map[f'age_{key}_neutral'] = Count('id', filter=age_q & Q(support_level='neutral'))
            aggregate_map[f'age_{key}_negative'] = Count('id', filter=age_q & Q(support_level='negative'))

        return aggregate_map

    def _get_overall_gender_totals(self, filters: DashboardFilters) -> dict[str, int]:
        if filters.has_telecaller_scope:
            queryset = self.repo.get_assignment_voter_queryset(filters).exclude(voter_id__isnull=True)
            totals = queryset.aggregate(
                male=Count('voter', filter=Q(voter__gender__in=['m', 'Male']), distinct=True),
                female=Count('voter', filter=Q(voter__gender__in=['f', 'Female']), distinct=True),
                other=Count('voter', filter=Q(voter__gender__in=['o', 'Other']), distinct=True),
            )
            return {
                'male': totals.get('male') or 0,
                'female': totals.get('female') or 0,
                'other': totals.get('other') or 0,
            }

        queryset = Voter.objects.filter(is_active=True).select_related('booth')
        queryset = self.repo._apply_booth_scope(queryset, 'booth__', filters)

        if filters.booth_id:
            queryset = queryset.filter(booth_id=filters.booth_id)
        elif filters.booth:
            booth_value = filters.booth.strip()
            queryset = queryset.filter(
                Q(booth__number__iexact=booth_value)
                | Q(booth__code__iexact=booth_value)
                | Q(booth__name__iexact=booth_value)
            )

        totals = queryset.aggregate(
            male=Count('id', filter=Q(gender__in=['m', 'Male'])),
            female=Count('id', filter=Q(gender__in=['f', 'Female'])),
            other=Count('id', filter=Q(gender__in=['o', 'Other'])),
        )
        return {
            'male': totals.get('male') or 0,
            'female': totals.get('female') or 0,
            'other': totals.get('other') or 0,
        }

    def build_filters(self, validated_data: dict) -> DashboardFilters:
        filters = DashboardFilters(
            date=validated_data.get('date'),
            block=(validated_data.get('block') or '').strip(),
            union=(validated_data.get('union') or '').strip(),
            panchayat=(validated_data.get('panchayat') or '').strip(),
            booth=(validated_data.get('booth') or '').strip(),
            telecaller=(validated_data.get('telecaller') or '').strip(),
            volunteer_role=(validated_data.get('volunteer_role') or '').strip(),
            limit=validated_data.get('limit') or 500,
        )
        return self.repo.resolve_filters(filters)

    def get_summary(self, validated_data: dict) -> dict:
        filters = self.build_filters(validated_data)
        surveys = self.repo.get_survey_queryset(filters)
        feedbacks = self.repo.get_feedback_queryset(filters)
        assignment_scope_total = self.repo.get_assignment_scope_voter_count(filters)
        survey_totals = surveys.aggregate(**self._build_survey_aggregate_map())
        overall_gender_totals = self._get_overall_gender_totals(filters)

        surveyed_voters = (survey_totals['linked_voters'] or 0) + (survey_totals['unlinked_records'] or 0)
        feedback_decision_ids = set(
            feedbacks.exclude(survey_id__isnull=True)
            .values_list('survey_id', flat=True)
            .distinct()
        )
        followup_feedback_ids = set(
            feedbacks.filter(action='followup_required')
            .exclude(survey_id__isnull=True)
            .values_list('survey_id', flat=True)
            .distinct()
        )
        feedback_closed_ids = set(
            feedbacks.filter(action='followup_not_required')
            .exclude(survey_id__isnull=True)
            .values_list('survey_id', flat=True)
            .distinct()
        )
        feedback_followups = len(followup_feedback_ids) + feedbacks.filter(
            action='followup_required', survey_id__isnull=True
        ).count()
        response_followups = surveys.filter(response_status='need_followup')
        if feedback_decision_ids:
            response_followups = response_followups.exclude(id__in=feedback_decision_ids)
        followup_count = feedback_followups + response_followups.count()
        followup_not_required_count = len(feedback_closed_ids) + feedbacks.filter(
            action='followup_not_required', survey_id__isnull=True
        ).count()

        total_voters = self.repo.get_total_voter_count(filters, assignment_scope_total=assignment_scope_total)
        not_reached = (survey_totals['not_reach'] or 0) + (survey_totals['no_answer'] or 0)

        party_rows = list(
            surveys.exclude(party_preference__isnull=True)
            .exclude(party_preference__exact='')
            .values('party_preference')
            .annotate(count=Count('id'))
            .order_by('-count', 'party_preference')[:8]
        )

        gender_breakdown = []
        for key, label, _gender_q in GENDER_BUCKETS:
            count = survey_totals.get(f'gender_{key}') or 0
            overall_count = overall_gender_totals.get(key) or 0
            gender_breakdown.append({
                'key': key,
                'label': label,
                'count': count,
                'overall_count': overall_count,
                'positive_count': survey_totals.get(f'gender_{key}_positive') or 0,
                'neutral_count': survey_totals.get(f'gender_{key}_neutral') or 0,
                'negative_count': survey_totals.get(f'gender_{key}_negative') or 0,
                'pct': safe_pct(count, overall_count),
            })

        age_breakdown = []
        for key, label, _age_q in AGE_BUCKETS:
            age_breakdown.append({
                'key': key,
                'label': label,
                'count': survey_totals.get(f'age_{key}') or 0,
                'positive_count': survey_totals.get(f'age_{key}_positive') or 0,
                'neutral_count': survey_totals.get(f'age_{key}_neutral') or 0,
                'negative_count': survey_totals.get(f'age_{key}_negative') or 0,
            })

        telecaller_count = len(self.get_telecaller_efficiency(validated_data)['rows'])

        return {
            'filters': {
                'date': str(filters.date) if filters.date else '',
                'block': filters.block_name or filters.block,
                'union': filters.union_name or filters.union,
                'panchayat': filters.panchayat_name or filters.panchayat,
                'booth': filters.booth_label or filters.booth,
                'telecaller': filters.telecaller_name or filters.telecaller,
                'volunteer_role': filters.volunteer_role,
            },
            'kpis': {
                'total_voters': total_voters,
                'surveyed_voters': surveyed_voters,
                'total_surveyed': surveyed_voters,
                'assigned_voters': assignment_scope_total,
                'coverage_pct': safe_pct(surveyed_voters, total_voters),
                'positive_pct': safe_pct(survey_totals['positive'] or 0, surveyed_voters),
                'positive_percent': safe_pct(survey_totals['positive'] or 0, surveyed_voters),
                'negative_risk_pct': safe_pct(survey_totals['negative'] or 0, surveyed_voters),
                'not_reachable_pct': safe_pct(not_reached, surveyed_voters),
                'followup_pct': safe_pct(followup_count, surveyed_voters),
                'followup_not_required_pct': safe_pct(followup_not_required_count, surveyed_voters),
                'telecaller_count': telecaller_count,
            },
            'support_breakdown': [
                {'key': 'positive', 'label': 'Positive', 'count': survey_totals['positive'] or 0},
                {'key': 'neutral', 'label': 'Neutral', 'count': survey_totals['neutral'] or 0},
                {'key': 'negative', 'label': 'Negative', 'count': survey_totals['negative'] or 0},
            ],
            'gender_breakdown': gender_breakdown,
            'age_breakdown': age_breakdown,
            'awareness_breakdown': [
                {'key': 'yes', 'label': 'Aware', 'count': survey_totals['aware_yes'] or 0},
                {'key': 'no', 'label': 'Not Aware', 'count': survey_totals['aware_no'] or 0},
                {'key': 'not_sure', 'label': 'Not Sure', 'count': survey_totals['aware_not_sure'] or 0},
            ],
            'vote_likelihood_breakdown': [
                {'key': 'yes', 'label': 'Likely', 'count': survey_totals['vote_yes'] or 0},
                {'key': 'no', 'label': 'Unlikely', 'count': survey_totals['vote_no'] or 0},
                {'key': 'not_sure', 'label': 'Not Sure', 'count': survey_totals['vote_not_sure'] or 0},
            ],
            'response_breakdown': [
                {'key': 'not_reached', 'label': 'Not Reached', 'count': survey_totals['not_reach'] or 0},
                {'key': 'no_answer', 'label': 'No Answer', 'count': survey_totals['no_answer'] or 0},
                {'key': 'wrong_number', 'label': 'Wrong Number', 'count': survey_totals['wrong_number'] or 0},
                {'key': 'followup', 'label': 'Follow-up', 'count': followup_count},
            ],
            'party_preference_breakdown': [
                {
                    'label': row['party_preference'],
                    'count': row['count'],
                    'pct': safe_pct(row['count'], surveyed_voters),
                }
                for row in party_rows
            ],
        }

    def get_booth_ranking(self, validated_data: dict) -> dict:
        filters = self.build_filters(validated_data)
        rows = []
        for booth in self.repo.get_booth_ranking_rows(filters):
            total_voters = max(booth.linked_total_voters or 0, booth.total_voters or 0)
            surveyed_voters = booth.surveyed_voters or 0
            positive = booth.positive or 0
            negative = booth.negative or 0
            neutral = booth.neutral or 0
            followup = booth.followup or 0
            coverage_pct = safe_pct(surveyed_voters, total_voters)
            positive_pct = safe_pct(positive, surveyed_voters)
            negative_pct = safe_pct(negative, surveyed_voters)
            followup_pct = safe_pct(followup, surveyed_voters)
            score = booth_ranking_score(coverage_pct, positive_pct, followup_pct)
            if not filters.booth and total_voters == 0 and surveyed_voters == 0:
                continue
            rows.append({
                'id': booth.id,
                'booth_number': booth.number or '',
                'booth_name': booth.name or '',
                'panchayat': booth.panchayat.name if booth.panchayat_id else '',
                'union': booth.panchayat.union.name if booth.panchayat_id and booth.panchayat.union_id else '',
                'block': (
                    booth.panchayat.union.block.name
                    if booth.panchayat_id and booth.panchayat.union_id and booth.panchayat.union.block_id
                    else ''
                ),
                'total_voters': total_voters,
                'surveyed_voters': surveyed_voters,
                'positive': positive,
                'negative': negative,
                'neutral': neutral,
                'followup': followup,
                'coverage_pct': coverage_pct,
                'positive_pct': positive_pct,
                'negative_pct': negative_pct,
                'followup_pct': followup_pct,
                'score': score,
            })

        rows.sort(
            key=lambda row: (
                row['score'],
                row['coverage_pct'],
                row['positive_pct'],
                row['surveyed_voters'],
            ),
            reverse=True,
        )
        rows = rows[:filters.limit]
        for index, row in enumerate(rows, start=1):
            row['rank'] = index
        return {'rows': rows}

    def get_telecaller_efficiency(self, validated_data: dict) -> dict:
        filters = self.build_filters(validated_data)
        assignment_rows = self.repo.get_telecaller_assignment_rows(filters)
        survey_rows = self.repo.get_telecaller_survey_rows(filters)
        feedback_rows = self.repo.get_telecaller_feedback_rows(filters)
        feedback_queryset = self.repo.get_feedback_queryset(filters)
        directory_rows = self.repo.get_telecaller_directory(filters)
        feedback_decision_ids = set(
            feedback_queryset.exclude(survey_id__isnull=True)
            .values_list('survey_id', flat=True)
            .distinct()
        )

        directory_by_id = {row['id']: row for row in directory_rows}
        directory_name_map = {}
        for row in directory_rows:
            for candidate in (row['name'], row['user__username']):
                key = normalize_key(candidate)
                if key:
                    directory_name_map[key] = row['id']

        def resolve_key(telecaller_id=None, telecaller_name=None):
            if telecaller_id and telecaller_id in directory_by_id:
                return f'id:{telecaller_id}'
            key = normalize_key(telecaller_name)
            if key and key in directory_name_map:
                return f"id:{directory_name_map[key]}"
            return key or 'unassigned'

        metrics = {}

        def ensure_row(key, telecaller_id=None, telecaller_name=None):
            if key not in metrics:
                directory = directory_by_id.get(telecaller_id) if telecaller_id else None
                if directory is None and key.startswith('id:'):
                    directory = directory_by_id.get(int(key.split(':', 1)[1]))
                metrics[key] = {
                    'telecaller_id': directory['id'] if directory else telecaller_id,
                    'telecaller_name': (
                        (directory.get('name') or '').strip()
                        if directory else (telecaller_name or 'Unassigned')
                    ),
                    'phone': directory.get('phone') if directory else '',
                    'role': (
                        (directory.get('volunteer_role__name') or directory.get('role') or '').strip()
                        if directory else ''
                    ),
                    'assigned_voters': 0,
                    'surveyed_voters': 0,
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0,
                    'followups': 0,
                    'closed_followups': 0,
                    'followup_not_required_pct': 0,
                    'assigned_booths': 0,
                }
            return metrics[key]

        for row in assignment_rows:
            key = resolve_key(row.get('telecaller_id'), row.get('telecaller_name'))
            item = ensure_row(key, row.get('telecaller_id'), row.get('telecaller_name'))
            item['assigned_voters'] += row.get('assigned_voters') or 0
            item['assigned_booths'] += row.get('assigned_booths') or 0

        for row in survey_rows:
            key = resolve_key(None, row.get('telecaller_key'))
            item = ensure_row(key, telecaller_name=row.get('telecaller_key'))
            surveyed = (row.get('linked_voters') or 0) + (row.get('unlinked_records') or 0)
            item['surveyed_voters'] += surveyed
            item['positive'] += row.get('positive') or 0
            item['negative'] += row.get('negative') or 0
            item['neutral'] += row.get('neutral') or 0

        survey_followup_counts = list(
            self.repo.get_survey_queryset(filters)
            .exclude(id__in=feedback_decision_ids)
            .annotate(
                telecaller_key=Case(
                    When(surveyed_by__gt='', then=F('surveyed_by')),
                    When(assigned_volunteer__gt='', then=F('assigned_volunteer')),
                    default=Value('Unassigned'),
                    output_field=CharField(),
                )
            )
            .values('telecaller_key')
            .annotate(need_followup=Count('id', filter=Q(response_status='need_followup')))
        )
        for row in survey_followup_counts:
            key = resolve_key(None, row.get('telecaller_key'))
            item = ensure_row(key, telecaller_name=row.get('telecaller_key'))
            item['followups'] += row.get('need_followup') or 0

        for row in feedback_rows:
            key = resolve_key(None, row.get('telecaller_name'))
            item = ensure_row(key, telecaller_name=row.get('telecaller_name'))
            item['followups'] += (row.get('required_surveys') or 0) + (row.get('required_loose') or 0)
            item['closed_followups'] += (row.get('closed_surveys') or 0) + (row.get('closed_loose') or 0)

        rows = []
        for item in metrics.values():
            denominator = item['assigned_voters'] or item['surveyed_voters']
            reach_pct = safe_pct(item['surveyed_voters'], denominator)
            positive_pct = safe_pct(item['positive'], item['surveyed_voters'])
            followup_pct = safe_pct(item['followups'], item['surveyed_voters'])
            followup_not_required_pct = safe_pct(item['closed_followups'], item['surveyed_voters'])
            item['reach_pct'] = reach_pct
            item['positive_pct'] = positive_pct
            item['followup_pct'] = followup_pct
            item['followup_not_required_pct'] = followup_not_required_pct
            item['efficiency_score'] = telecaller_efficiency_score(
                reach_pct,
                positive_pct,
                followup_not_required_pct,
            )
            rows.append(item)

        rows.sort(
            key=lambda row: (
                row['efficiency_score'],
                row['reach_pct'],
                row['positive_pct'],
                row['surveyed_voters'],
            ),
            reverse=True,
        )
        rows = rows[:filters.limit]
        for index, row in enumerate(rows, start=1):
            row['rank'] = index
        return {'rows': rows}

    def get_telecaller_efficiency_by_date(self, validated_data: dict) -> dict:
        requested_date = validated_data.get('date')

        if requested_date:
            activity_dates = [requested_date]
        else:
            base_filters = self.build_filters({**validated_data, 'date': None})
            survey_dates = set(
                self.repo.get_survey_queryset(base_filters)
                .exclude(survey_date__isnull=True)
                .values_list('survey_date', flat=True)
                .distinct()
            )
            assignment_dates = set(
                self.repo.get_assignment_queryset(base_filters)
                .exclude(assigned_date__isnull=True)
                .values_list('assigned_date', flat=True)
                .distinct()
            )
            feedback_dates = set(
                self.repo.get_feedback_queryset(base_filters)
                .exclude(date__isnull=True)
                .values_list('date', flat=True)
                .distinct()
            )
            activity_dates = sorted(survey_dates | assignment_dates | feedback_dates, reverse=True)

        rows = []
        for activity_date in activity_dates:
            daily_rows = self.get_telecaller_efficiency({**validated_data, 'date': activity_date}).get('rows', [])
            for row in daily_rows:
                rows.append({
                    'date': str(activity_date),
                    **row,
                })

        return {'rows': rows}

    def get_task_panel(self, validated_data: dict) -> dict:
        filters = self.build_filters(validated_data)
        queryset = self.repo.get_task_queryset(filters)
        now = timezone.now()
        summary = queryset.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            completed=Count('id', filter=Q(status='completed')),
            cancelled=Count('id', filter=Q(status='cancelled')),
            overdue=Count(
                'id',
                filter=Q(status__in=['pending', 'in_progress'], expected_datetime__lt=now),
            ),
        )
        summary['open'] = (summary['pending'] or 0) + (summary['in_progress'] or 0)
        summary['completion_pct'] = safe_pct(summary['completed'] or 0, summary['total'] or 0)

        priority_order = Case(
            When(status='in_progress', then=Value(0)),
            When(status='pending', then=Value(1)),
            When(status='completed', then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        )

        items = []
        for task in queryset.order_by(priority_order, 'expected_datetime', 'id')[:filters.limit]:
            items.append({
                'id': task.id,
                'title': task.title or '',
                'status': task.status or '',
                'expected_datetime': task.expected_datetime.isoformat() if task.expected_datetime else '',
                'task_category': task.task_category.name if task.task_category_id else '',
                'task_category_color': task.task_category.color if task.task_category_id else '',
                'volunteer_role': task.volunteer_role.name if task.volunteer_role_id else '',
                'coordinator': task.coordinator.name if task.coordinator_id else '',
                'delivery_incharge': task.delivery_incharge.name if task.delivery_incharge_id else '',
                'booth': task.booth.name if task.booth_id else '',
                'booth_number': task.booth.number if task.booth_id else '',
                'ward': task.ward.name if task.ward_id else '',
                'venue': task.venue or '',
                'notes': task.notes or '',
            })

        return {'summary': summary, 'items': items}

    def get_filter_options(self) -> dict:
        return {
            'blocks': [
                {
                    'id': block['id'],
                    'label': block['name'] or '',
                    'name': block['name'] or '',
                }
                for block in self.repo.get_block_options()
                if block['name']
            ],
            'unions': [
                {
                    'id': row['id'],
                    'label': row['name'] or '',
                    'name': row['name'] or '',
                    'block_id': row['block_id'],
                    'block_name': row['block__name'] or '',
                }
                for row in self.repo.get_union_options()
                if row['name']
            ],
            'panchayats': [
                {
                    'id': row['id'],
                    'label': row['name'] or '',
                    'name': row['name'] or '',
                    'union_id': row['union_id'],
                    'union_name': row['union__name'] or '',
                    'block_id': row['union__block_id'],
                    'block_name': row['union__block__name'] or '',
                }
                for row in self.repo.get_panchayat_options()
                if row['name']
            ],
            'booths': [
                {
                    'id': booth['id'],
                    'label': f"{booth['number'] or booth['id']} - {booth['name'] or 'Booth'}",
                    'number': booth['number'] or '',
                    'name': booth['name'] or '',
                    'panchayat_id': booth['panchayat_id'],
                    'panchayat_name': booth['panchayat__name'] or '',
                    'union_id': booth['panchayat__union_id'],
                    'union_name': booth['panchayat__union__name'] or '',
                    'block_id': booth['panchayat__union__block_id'],
                    'block_name': booth['panchayat__union__block__name'] or '',
                }
                for booth in self.repo.get_booth_options()
            ],
            'telecallers': [
                {
                    'id': row['id'],
                    'name': row['name'] or '',
                    'phone': row['phone'] or '',
                    'role': row['volunteer_role__name'] or row['role'] or '',
                }
                for row in self.repo.get_telecaller_options()
                if row['name']
            ],
            'volunteer_roles': self.repo.get_volunteer_role_options(),
        }
