"""
Voter app URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from campaign_os.voters import views

router = DefaultRouter()
router.register(r'voters', views.VoterViewSet, basename='voter')
router.register(r'contacts', views.VoterContactViewSet, basename='voter-contact')
router.register(r'surveys', views.VoterSurveyViewSet, basename='voter-survey')
router.register(r'preferences', views.VoterPreferenceViewSet, basename='voter-preference')
router.register(r'feedbacks', views.VoterFeedbackViewSet, basename='voter-feedback')

urlpatterns = [
    path('', include(router.urls)),
]
