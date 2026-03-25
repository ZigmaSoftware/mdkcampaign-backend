"""
Volunteer app URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from campaign_os.volunteers import views

router = DefaultRouter()
router.register(r'volunteers', views.VolunteerViewSet, basename='volunteer')
router.register(r'tasks', views.VolunteerTaskViewSet, basename='task')
router.register(r'attendance', views.VolunteerAttendanceViewSet, basename='volunteer-attendance')

urlpatterns = [path('', include(router.urls))]
