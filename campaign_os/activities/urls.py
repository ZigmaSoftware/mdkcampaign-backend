from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'logs',    views.ActivityLogViewSet,  basename='activity-log')
router.register(r'surveys', views.FieldSurveyViewSet,  basename='field-survey')

urlpatterns = [path('', include(router.urls))]
