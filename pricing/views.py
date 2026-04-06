from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import PricingPlan
from .serializers import PricingPlanDetailSerializer, PricingPlanListSerializer


class PricingPlanListAPIView(generics.ListAPIView):
    """GET /api/pricing-plans/ — active packages for the control panel."""

    permission_classes = [AllowAny]
    serializer_class = PricingPlanListSerializer

    def get_queryset(self):
        return PricingPlan.objects.filter(is_active=True).order_by("package_duration_minutes", "name")


class PricingPlanDetailAPIView(generics.RetrieveAPIView):
    """GET /api/pricing-plans/<id>/ — single package."""

    permission_classes = [AllowAny]
    queryset = PricingPlan.objects.all()
    serializer_class = PricingPlanDetailSerializer
