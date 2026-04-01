"""
URL configuration for masters app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from campaign_os.masters import views

router = DefaultRouter()
router.register(r'countries', views.CountryViewSet, basename='country')
router.register(r'states', views.StateViewSet, basename='state')
router.register(r'districts', views.DistrictViewSet, basename='district')
router.register(r'constituencies', views.ConstituencyViewSet, basename='constituency')
router.register(r'wards', views.WardViewSet, basename='ward')
router.register(r'booths', views.BoothViewSet, basename='booth')
router.register(r'areas', views.PollingAreaViewSet, basename='area')
router.register(r'parties', views.PartyViewSet, basename='party')
router.register(r'candidates', views.CandidateViewSet, basename='candidate')
router.register(r'schemes', views.SchemeViewSet, basename='scheme')
router.register(r'achievements', views.AchievementViewSet, basename='achievement')
router.register(r'task-types', views.TaskTypeViewSet, basename='task_type')
router.register(r'task-categories', views.TaskCategoryViewSet, basename='task_category')
router.register(r'campaign-activity-types', views.CampaignActivityTypeViewSet, basename='campaign_activity_type')
router.register(r'volunteer-roles', views.VolunteerRoleViewSet, basename='volunteer_role')
router.register(r'volunteer-types', views.VolunteerTypeViewSet, basename='volunteer_type')
router.register(r'panchayats', views.PanchayatViewSet, basename='panchayat')
router.register(r'unions', views.UnionViewSet, basename='union')

urlpatterns = [
    path('', include(router.urls)),
]
