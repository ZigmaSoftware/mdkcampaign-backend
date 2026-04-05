from django.urls import path

from campaign_os.dashboard.views import (
    dashboard_booths,
    dashboard_filter_options,
    dashboard_summary,
    dashboard_tasks,
    dashboard_telecallers,
)


urlpatterns = [
    path('summary/', dashboard_summary, name='dashboard-summary'),
    path('booths/', dashboard_booths, name='dashboard-booths'),
    path('telecallers/', dashboard_telecallers, name='dashboard-telecallers'),
    path('tasks/', dashboard_tasks, name='dashboard-tasks'),
    path('filters/', dashboard_filter_options, name='dashboard-filters'),
]

