"""
Campaign apps URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from campaign_os.campaigns import views

router = DefaultRouter()
router.register(r'events', views.CampaignEventViewSet, basename='event')
router.register(r'attendees', views.EventAttendeeViewSet, basename='attendee')
router.register(r'tasks', views.TaskViewSet, basename='task')

urlpatterns = [path('', include(router.urls))]
