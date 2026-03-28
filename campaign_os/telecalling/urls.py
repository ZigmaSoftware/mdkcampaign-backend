from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'assignments', views.TelecallingAssignmentViewSet, basename='telecalling-assignment')
router.register(r'feedbacks',   views.TelecallingFeedbackViewSet,   basename='telecalling-feedback')

urlpatterns = [path('', include(router.urls))]
