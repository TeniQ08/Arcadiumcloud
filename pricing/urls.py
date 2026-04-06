from django.urls import path

from . import views

urlpatterns = [
    path("pricing-plans/", views.PricingPlanListAPIView.as_view(), name="api_pricing_plans"),
    path("pricing-plans/<int:pk>/", views.PricingPlanDetailAPIView.as_view(), name="api_pricing_plan_detail"),
]
