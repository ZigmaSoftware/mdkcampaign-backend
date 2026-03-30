"""
Analytics app URLs
"""
from django.urls import path
from campaign_os.analytics.views import AnalyticsViewSet

urlpatterns = [
    path('dashboard/', AnalyticsViewSet.as_view({'get': 'dashboard_stats'}), name='dashboard-stats'),
    path('booths/', AnalyticsViewSet.as_view({'get': 'booth_statistics'}), name='booth-stats'),
    path('booth-volunteers/<int:booth_id>/', AnalyticsViewSet.as_view({'get': 'booth_volunteers'}), name='booth-volunteers'),
    path('booth-voters/<int:booth_id>/', AnalyticsViewSet.as_view({'get': 'booth_voters_list'}), name='booth-voters'),
    path('constituencies/', AnalyticsViewSet.as_view({'get': 'constituency_stats'}), name='constituency-stats'),
    path('volunteers/', AnalyticsViewSet.as_view({'get': 'volunteer_performance'}), name='volunteer-perf'),
    path('sentiment/', AnalyticsViewSet.as_view({'get': 'sentiment_distribution'}), name='sentiment-dist'),
    path('events/', AnalyticsViewSet.as_view({'get': 'event_analytics'}), name='event-analytics'),
    path('coverage/', AnalyticsViewSet.as_view({'get': 'geographic_coverage'}), name='coverage'),
    path('wards/', AnalyticsViewSet.as_view({'get': 'ward_statistics'}), name='ward-stats'),
    path('ward-volunteers/<int:ward_id>/', AnalyticsViewSet.as_view({'get': 'ward_volunteers'}), name='ward-volunteers'),
    path('fix-links/', AnalyticsViewSet.as_view({'post': 'fix_links'}), name='fix-links'),
]
