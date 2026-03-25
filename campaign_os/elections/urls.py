"""
Elections app URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from campaign_os.elections import views

router = DefaultRouter()
router.register(r'elections', views.ElectionViewSet, basename='election')
router.register(r'polls', views.PollViewSet, basename='poll')

urlpatterns = [path('', include(router.urls))]
