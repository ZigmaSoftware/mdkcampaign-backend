from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from campaign_os.dashboard.repositories.task_dashboard_repository import (
    TaskDashboardFilters,
    TaskDashboardRepository,
)
from campaign_os.dashboard.services.aggregation_service import safe_pct


class TaskDashboardService:
    def __init__(self):
        self.repo = TaskDashboardRepository()

    def build_filters(self, validated_data: dict[str, Any]) -> TaskDashboardFilters:
        return TaskDashboardFilters(
            from_date=validated_data.get('from_date'),
            to_date=validated_data.get('to_date'),
            task_type=(validated_data.get('task_type') or '').strip(),
            task_category=(validated_data.get('task_category') or '').strip(),
            module=(validated_data.get('module') or '').strip(),
            limit=validated_data.get('limit') or 200,
        )

    def get_summary(self, validated_data: dict[str, Any]) -> dict[str, Any]:
        filters = self.build_filters(validated_data)
        rows = self._get_filtered_rows(filters)
        counts = self._classify_rows(rows)
        total = len(rows)
        campaign_count = sum(1 for row in rows if row['module'] == 'campaign')
        avg_completion_hours = self._avg_completion_hours(rows)

        return {
            'filters': self._serialize_filters(filters),
            'counts': {
                **counts,
                'total': total,
            },
            'derived': {
                'completion_rate_pct': safe_pct(counts['completed'], total),
                'overdue_risk_pct': safe_pct(counts['overdue'], counts['pending']),
                'campaign_task_ratio_pct': safe_pct(campaign_count, total),
                'avg_completion_time_hours': avg_completion_hours,
                'avg_completion_time_label': self._format_duration(avg_completion_hours),
            },
            'status_breakdown': [
                {'key': 'pending', 'label': 'Pending', 'count': counts['pending'], 'color': '#FF9933'},
                {'key': 'completed', 'label': 'Completed', 'count': counts['completed'], 'color': '#138808'},
                {'key': 'cancelled', 'label': 'Cancelled', 'count': counts['cancelled'], 'color': '#dc2626'},
            ],
            'due_breakdown': [
                {'key': 'today', 'label': 'Today', 'count': counts['today'], 'color': '#0d2455'},
                {'key': 'tomorrow', 'label': 'Tomorrow', 'count': counts['tomorrow'], 'color': '#2563eb'},
                {'key': 'overdue', 'label': 'Overdue', 'count': counts['overdue'], 'color': '#dc2626'},
            ],
        }

    def get_list(self, validated_data: dict[str, Any]) -> dict[str, Any]:
        filters = self.build_filters(validated_data)
        rows = self._get_filtered_rows(filters)
        sorted_rows = sorted(rows, key=self._sort_key)
        return {
            'filters': self._serialize_filters(filters),
            'total': len(sorted_rows),
            'rows': sorted_rows[:filters.limit],
        }

    def get_type_category_analytics(self, validated_data: dict[str, Any]) -> dict[str, Any]:
        filters = self.build_filters(validated_data)
        rows = self._get_filtered_rows(filters)

        type_groups = defaultdict(lambda: self._empty_group())
        category_groups = defaultdict(lambda: self._empty_group())

        for row in rows:
            self._apply_group_row(type_groups[row['task_type']], row)
            self._apply_group_row(category_groups[row['task_category']], row)

        type_distribution = [
            {
                'label': label,
                **self._finalize_group(metrics),
            }
            for label, metrics in type_groups.items()
        ]
        category_workload = [
            {
                'label': label,
                **self._finalize_group(metrics),
            }
            for label, metrics in category_groups.items()
        ]

        type_distribution.sort(key=lambda item: (item['total'], item['completed']), reverse=True)
        category_workload.sort(key=lambda item: (item['total'], item['completed']), reverse=True)

        return {
            'filters': self._serialize_filters(filters),
            'type_distribution': type_distribution[:10],
            'category_workload': category_workload[:12],
        }

    def get_campaign_activity_status(self, validated_data: dict[str, Any]) -> dict[str, Any]:
        filters = self.build_filters(validated_data)
        if filters.module == 'task':
            return {'filters': self._serialize_filters(filters), 'rows': []}

        campaign_rows = self.repo.get_campaign_rows(filters)
        masters = self.repo.get_activity_masters()
        rows_by_name: dict[str, dict[str, Any]] = {}

        for master in masters:
            name = master.get('name') or 'Campaign Activity'
            rows_by_name[name] = {
                'activity_name': name,
                'event_type': master.get('event_type') or '',
                'planned': 0,
                'in_progress': 0,
                'completed': 0,
                'pending': 0,
                'overdue': 0,
                'total': 0,
                'is_unmapped': False,
            }

        for row in campaign_rows:
            name = row['task_category']
            bucket = rows_by_name.setdefault(name, {
                'activity_name': name,
                'event_type': '',
                'planned': 0,
                'in_progress': 0,
                'completed': 0,
                'pending': 0,
                'overdue': 0,
                'total': 0,
                'is_unmapped': name.startswith('Unmapped · '),
            })
            raw_status = row['raw_status']
            if raw_status == 'planned':
                bucket['planned'] += 1
            elif raw_status == 'confirmed':
                bucket['in_progress'] += 1
            elif raw_status == 'completed':
                bucket['completed'] += 1

            if row['status'] == 'pending':
                bucket['pending'] += 1
                if self._due_bucket(row) == 'overdue':
                    bucket['overdue'] += 1

            bucket['total'] += 1

        ordered_rows = sorted(
            rows_by_name.values(),
            key=lambda item: (item['overdue'], item['pending'], item['completed'], item['activity_name']),
            reverse=True,
        )
        return {
            'filters': self._serialize_filters(filters),
            'rows': ordered_rows,
        }

    def get_filter_options(self) -> dict[str, Any]:
        return {
            'modules': [
                {'value': 'task', 'label': 'Task Management'},
                {'value': 'campaign', 'label': 'Campaign Tasks'},
            ],
            'task_types': self.repo.get_task_type_options(),
            'task_categories': self.repo.get_task_category_options(),
        }

    def _get_filtered_rows(self, filters: TaskDashboardFilters) -> list[dict[str, Any]]:
        rows = []
        rows.extend(self.repo.get_task_rows(filters))
        rows.extend(self.repo.get_campaign_rows(filters))
        for row in rows:
            row['due_bucket'] = self._due_bucket(row)
        return rows

    def _classify_rows(self, rows: list[dict[str, Any]]) -> dict[str, int]:
        result = {
            'today': 0,
            'tomorrow': 0,
            'overdue': 0,
            'pending': 0,
            'completed': 0,
            'cancelled': 0,
        }
        for row in rows:
            status = row['status']
            if status == 'completed':
                result['completed'] += 1
                continue
            if status == 'cancelled':
                result['cancelled'] += 1
                continue

            result['pending'] += 1
            due_bucket = row.get('due_bucket')
            if due_bucket == 'today':
                result['today'] += 1
            elif due_bucket == 'tomorrow':
                result['tomorrow'] += 1
            elif due_bucket == 'overdue':
                result['overdue'] += 1
        return result

    def _due_bucket(self, row: dict[str, Any]) -> str:
        if row['status'] != 'pending' or not row.get('due_date'):
            return 'other'

        today = date.today()
        tomorrow = today + timedelta(days=1)
        due_date = date.fromisoformat(row['due_date'])
        if due_date == today:
            return 'today'
        if due_date == tomorrow:
            return 'tomorrow'
        if due_date < today:
            return 'overdue'
        return 'upcoming'

    def _sort_key(self, row: dict[str, Any]):
        bucket_rank = {
            'overdue': 0,
            'today': 1,
            'tomorrow': 2,
            'upcoming': 3,
            'other': 4,
        }
        return (
            bucket_rank.get(row.get('due_bucket') or 'other', 4),
            row.get('due_date') or '9999-12-31',
            row.get('created_at') or '',
        )

    def _avg_completion_hours(self, rows: list[dict[str, Any]]) -> float:
        values = [row['completion_hours'] for row in rows if row.get('completion_hours') is not None]
        if not values:
            return 0.0
        return round(sum(values) / len(values), 1)

    def _format_duration(self, hours: float) -> str:
        if not hours:
            return '0h'
        if hours < 24:
            return f'{hours:.1f}h'
        days = int(hours // 24)
        remainder = round(hours - (days * 24), 1)
        if remainder <= 0:
            return f'{days}d'
        return f'{days}d {remainder:.1f}h'

    def _serialize_filters(self, filters: TaskDashboardFilters) -> dict[str, Any]:
        return {
            'from_date': filters.from_date.isoformat() if filters.from_date else '',
            'to_date': filters.to_date.isoformat() if filters.to_date else '',
            'task_type': filters.task_type,
            'task_category': filters.task_category,
            'module': filters.module,
            'limit': filters.limit,
        }

    def _empty_group(self) -> dict[str, Any]:
        return {
            'total': 0,
            'pending': 0,
            'completed': 0,
            'cancelled': 0,
            'today': 0,
            'tomorrow': 0,
            'overdue': 0,
            'task_count': 0,
            'campaign_count': 0,
        }

    def _apply_group_row(self, group: dict[str, Any], row: dict[str, Any]) -> None:
        group['total'] += 1
        if row['status'] == 'completed':
            group['completed'] += 1
        elif row['status'] == 'cancelled':
            group['cancelled'] += 1
        else:
            group['pending'] += 1
            if row['due_bucket'] == 'today':
                group['today'] += 1
            elif row['due_bucket'] == 'tomorrow':
                group['tomorrow'] += 1
            elif row['due_bucket'] == 'overdue':
                group['overdue'] += 1

        if row['module'] == 'campaign':
            group['campaign_count'] += 1
        else:
            group['task_count'] += 1

    def _finalize_group(self, group: dict[str, Any]) -> dict[str, Any]:
        return {
            **group,
            'completion_rate_pct': safe_pct(group['completed'], group['total']),
        }
