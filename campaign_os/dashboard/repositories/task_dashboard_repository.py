from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from django.db.models import QuerySet

try:
    from campaign_os.campaigns.models import CampaignEvent, Task
except Exception:  # pragma: no cover - safe fallback if module import changes
    CampaignEvent = None
    Task = None

try:
    from campaign_os.masters.models import CampaignActivityType, TaskCategory, TaskType
except Exception:  # pragma: no cover - safe fallback if module import changes
    CampaignActivityType = None
    TaskCategory = None
    TaskType = None


@dataclass
class TaskDashboardFilters:
    from_date: date | None = None
    to_date: date | None = None
    task_type: str = ''
    task_category: str = ''
    module: str = ''
    limit: int = 200


def normalize_text(value: str | None) -> str:
    return ' '.join(str(value or '').strip().lower().split())


def _field_choices(model, field_name: str) -> dict[str, str]:
    if not model:
        return {}
    try:
        return dict(model._meta.get_field(field_name).choices)
    except Exception:
        return {}


TASK_CATEGORY_LABELS = _field_choices(Task, 'category')
TASK_STATUS_LABELS = _field_choices(Task, 'status')
CAMPAIGN_EVENT_TYPE_LABELS = _field_choices(CampaignEvent, 'event_type')
CAMPAIGN_STATUS_LABELS = _field_choices(CampaignEvent, 'status')


class TaskDashboardRepository:
    @property
    def campaign_available(self) -> bool:
        return CampaignEvent is not None

    def get_task_type_options(self) -> list[str]:
        task_types: list[str] = []
        if TaskType is not None:
            task_types.extend(
                list(
                    TaskType.objects.filter(is_active=True)
                    .values_list('name', flat=True)
                    .order_by('order', 'name')
                )
            )
        task_types.extend(label for label in CAMPAIGN_EVENT_TYPE_LABELS.values() if label)

        merged: list[str] = []
        seen: set[str] = set()
        for value in task_types:
            key = normalize_text(value)
            if value and key and key not in seen:
                seen.add(key)
                merged.append(value)
        return merged

    def get_task_category_options(self) -> list[str]:
        categories: list[str] = []
        if TaskCategory is not None:
            categories.extend(
                list(
                    TaskCategory.objects.filter(is_active=True)
                    .values_list('name', flat=True)
                    .order_by('priority', 'name')
                )
            )
        categories.extend(label for label in TASK_CATEGORY_LABELS.values() if label)
        if CampaignActivityType is not None:
            categories.extend(
                list(
                    CampaignActivityType.objects.filter(is_active=True)
                    .values_list('name', flat=True)
                    .order_by('order', 'name')
                )
            )

        merged: list[str] = []
        seen: set[str] = set()
        for value in categories:
            key = normalize_text(value)
            if value and key and key not in seen:
                seen.add(key)
                merged.append(value)
        return merged

    def get_activity_masters(self) -> list[dict[str, Any]]:
        if CampaignActivityType is None:
            return []
        rows = list(
            CampaignActivityType.objects.filter(is_active=True)
            .values('id', 'name', 'event_type')
            .order_by('order', 'name')
        )
        for row in rows:
            row['normalized_name'] = normalize_text(row.get('name'))
        return rows

    def get_task_rows(self, filters: TaskDashboardFilters) -> list[dict[str, Any]]:
        if Task is None or filters.module == 'campaign':
            return []

        queryset = Task.objects.filter(is_active=True).select_related(
            'task_type',
            'task_category',
            'delivery_incharge',
            'delivery_incharge__user',
            'coordinator',
            'coordinator__user',
            'block',
            'union',
            'panchayat',
            'booth',
            'ward',
        )
        if filters.from_date:
            queryset = queryset.filter(expected_datetime__date__gte=filters.from_date)
        if filters.to_date:
            queryset = queryset.filter(expected_datetime__date__lte=filters.to_date)

        normalized_type_filter = normalize_text(filters.task_type)
        normalized_category_filter = normalize_text(filters.task_category)
        rows: list[dict[str, Any]] = []

        for task in queryset:
            task_type = (task.task_type.name if task.task_type_id else '').strip() or 'General Task'
            task_category = (
                (task.task_category.name if task.task_category_id else '').strip()
                or TASK_CATEGORY_LABELS.get(task.category or '', '')
                or 'Uncategorized'
            )

            if normalized_type_filter and normalize_text(task_type) != normalized_type_filter:
                continue
            if normalized_category_filter and normalize_text(task_category) != normalized_category_filter:
                continue

            raw_status = (task.status or '').strip()
            normalized_status = self.normalize_task_status(raw_status)
            due_dt = task.expected_datetime
            location = ' · '.join([
                part for part in [
                    task.venue or '',
                    task.block.name if task.block_id else '',
                    task.union.name if task.union_id else '',
                    task.panchayat.name if task.panchayat_id else '',
                    task.booth.name if task.booth_id else '',
                    task.ward.name if task.ward_id else '',
                ]
                if part
            ])
            owner = ' · '.join([
                part for part in [
                    self._volunteer_name(task.delivery_incharge),
                    self._volunteer_name(task.coordinator),
                ]
                if part
            ])

            rows.append({
                'id': f'task-{task.id}',
                'source_id': task.id,
                'title': task.title or f'Task #{task.id}',
                'task_type': task_type,
                'task_category': task_category,
                'status': normalized_status,
                'status_display': TASK_STATUS_LABELS.get(raw_status, raw_status.replace('_', ' ').title() or 'Pending'),
                'raw_status': raw_status,
                'due_date': due_dt.date().isoformat() if due_dt else '',
                'due_datetime': due_dt.isoformat() if due_dt else '',
                'created_at': task.created_at.isoformat() if task.created_at else '',
                'module': 'task',
                'module_label': 'Task Management',
                'details': task.details or task.notes or '',
                'location': location,
                'owner': owner,
                'completion_hours': self._completion_hours(
                    task.created_at,
                    task.completed_datetime or (task.updated_at if raw_status == 'completed' else None),
                ),
            })

        return rows

    def get_campaign_rows(self, filters: TaskDashboardFilters) -> list[dict[str, Any]]:
        if CampaignEvent is None or filters.module == 'task':
            return []

        queryset = CampaignEvent.objects.filter(is_active=True).select_related('organized_by')
        if filters.from_date:
            queryset = queryset.filter(scheduled_date__gte=filters.from_date)
        if filters.to_date:
            queryset = queryset.filter(scheduled_date__lte=filters.to_date)

        normalized_type_filter = normalize_text(filters.task_type)
        activity_masters = self.get_activity_masters()
        masters_by_event_type: dict[str, list[dict[str, Any]]] = {}
        for master in activity_masters:
            masters_by_event_type.setdefault(master.get('event_type') or '', []).append(master)

        rows: list[dict[str, Any]] = []
        for event in queryset:
            event_type_label = CAMPAIGN_EVENT_TYPE_LABELS.get(event.event_type or '', event.event_type or 'Campaign')
            if normalized_type_filter and normalize_text(event_type_label) != normalized_type_filter:
                continue

            activity_name = self._infer_activity_name(event, masters_by_event_type)
            if filters.task_category and normalize_text(activity_name) != normalize_text(filters.task_category):
                continue

            raw_status = (event.status or '').strip()
            normalized_status = self.normalize_campaign_status(raw_status)
            due_dt = self._event_due_datetime(event)
            organizer = ''
            if event.organized_by_id:
                organizer = event.organized_by.get_full_name() or event.organized_by.username

            details = ' · '.join([
                part for part in [
                    event.description or '',
                    event.outcome_notes or '',
                    event.materials_prepared or '',
                ]
                if part
            ])

            rows.append({
                'id': f'campaign-{event.id}',
                'source_id': event.id,
                'title': event.title or f'Campaign Event #{event.id}',
                'task_type': event_type_label,
                'task_category': activity_name,
                'status': normalized_status,
                'status_display': CAMPAIGN_STATUS_LABELS.get(raw_status, raw_status.replace('_', ' ').title() or 'Planned'),
                'raw_status': raw_status,
                'due_date': event.scheduled_date.isoformat() if event.scheduled_date else '',
                'due_datetime': due_dt.isoformat() if due_dt else '',
                'created_at': event.created_at.isoformat() if event.created_at else '',
                'module': 'campaign',
                'module_label': 'Campaign Task',
                'details': details,
                'location': event.location or '',
                'owner': organizer,
                'completion_hours': self._completion_hours(
                    event.created_at,
                    event.updated_at if raw_status == 'completed' else None,
                ),
            })

        return rows

    def normalize_task_status(self, status: str) -> str:
        if status == 'completed':
            return 'completed'
        if status == 'cancelled':
            return 'cancelled'
        return 'pending'

    def normalize_campaign_status(self, status: str) -> str:
        if status == 'completed':
            return 'completed'
        if status == 'cancelled':
            return 'cancelled'
        return 'pending'

    def _event_due_datetime(self, event: Any) -> datetime | None:
        if not event.scheduled_date:
            return None
        if event.scheduled_time:
            return datetime.combine(event.scheduled_date, event.scheduled_time)
        return datetime.combine(event.scheduled_date, datetime.min.time())

    def _infer_activity_name(
        self,
        event: Any,
        masters_by_event_type: dict[str, list[dict[str, Any]]],
    ) -> str:
        candidates = masters_by_event_type.get(event.event_type or '', [])
        if not candidates:
            return CAMPAIGN_EVENT_TYPE_LABELS.get(event.event_type or '', event.event_type or 'Campaign')

        haystack = normalize_text(' '.join([
            event.title or '',
            event.description or '',
            event.location or '',
        ]))
        best_match: dict[str, Any] | None = None
        for candidate in candidates:
            normalized_name = candidate.get('normalized_name') or ''
            if normalized_name and normalized_name in haystack:
                if best_match is None or len(normalized_name) > len(best_match.get('normalized_name') or ''):
                    best_match = candidate

        if best_match:
            return best_match.get('name') or 'Campaign Activity'
        if len(candidates) == 1:
            return candidates[0].get('name') or 'Campaign Activity'

        return f"Unmapped · {CAMPAIGN_EVENT_TYPE_LABELS.get(event.event_type or '', event.event_type or 'Campaign')}"

    def _completion_hours(self, created_at: datetime | None, completed_at: datetime | None) -> float | None:
        if not created_at or not completed_at:
            return None
        delta = completed_at - created_at
        if delta.total_seconds() < 0:
            return None
        return round(delta.total_seconds() / 3600, 1)

    def _volunteer_name(self, volunteer: Any) -> str:
        if not volunteer:
            return ''
        if getattr(volunteer, 'name', None):
            return volunteer.name
        user = getattr(volunteer, 'user', None)
        if user:
            return user.get_full_name() or user.username
        return ''
