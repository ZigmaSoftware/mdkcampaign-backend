"""
Main URL configuration for campaign_os
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from campaign_os.polls.views import poll_short_redirect

api_v1_patterns = [
    path('auth/', include('campaign_os.accounts.urls')),
    path('masters/', include('campaign_os.masters.urls')),
    path('elections/', include('campaign_os.elections.urls')),
    path('voters/', include('campaign_os.voters.urls')),
    path('volunteers/', include('campaign_os.volunteers.urls')),
    path('campaigns/', include('campaign_os.campaigns.urls')),
    path('analytics/',  include('campaign_os.analytics.urls')),
    path('activities/',   include('campaign_os.activities.urls')),
    path('attendance/',   include('campaign_os.attendance.urls')),
    path('polls/',        include('campaign_os.polls.urls')),
    path('telecalling/',  include('campaign_os.telecalling.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_v1_patterns)),

    # Short poll URL: /p/<token>/ → frontend poll page (public, no auth)
    path('p/<str:token>/', poll_short_redirect, name='poll_short_redirect'),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
