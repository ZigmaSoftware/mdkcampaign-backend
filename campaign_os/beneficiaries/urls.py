from django.urls import path, include
from rest_framework.routers import DefaultRouter
from campaign_os.beneficiaries import views

router = DefaultRouter()
router.register(r'beneficiaries', views.BeneficiaryViewSet, basename='beneficiary')

urlpatterns = [path('', include(router.urls))]
