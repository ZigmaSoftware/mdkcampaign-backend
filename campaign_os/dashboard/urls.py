from django.urls import path

from campaign_os.dashboard.views import (
    dashboard_booths,
    dashboard_filter_options,
    dashboard_summary,
    dashboard_tasks,
    dashboard_telecallers,
    dashboard_telecallers_by_date,
    task_dashboard_campaign_activity_status,
    task_dashboard_filter_options,
    task_dashboard_list,
    task_dashboard_summary,
    task_dashboard_type_category,
)


urlpatterns = [
    path('summary/', dashboard_summary, name='dashboard-summary'),
    path('booths/', dashboard_booths, name='dashboard-booths'),
    path('telecallers/', dashboard_telecallers, name='dashboard-telecallers'),
    path('telecallers/date-wise/', dashboard_telecallers_by_date, name='dashboard-telecallers-date-wise'),
    path('tasks/', dashboard_tasks, name='dashboard-tasks'),
    path('filters/', dashboard_filter_options, name='dashboard-filters'),
    path('task-dashboard/summary/', task_dashboard_summary, name='task-dashboard-summary'),
    path('task-dashboard/list/', task_dashboard_list, name='task-dashboard-list'),
    path('task-dashboard/type-category/', task_dashboard_type_category, name='task-dashboard-type-category'),
    path(
        'task-dashboard/campaign-activity-status/',
        task_dashboard_campaign_activity_status,
        name='task-dashboard-campaign-activity-status',
    ),
    path('task-dashboard/filters/', task_dashboard_filter_options, name='task-dashboard-filters'),
]
