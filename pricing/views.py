from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import PricingPlan
from .serializers import PricingPlanDetailSerializer, PricingPlanListSerializer


class PrepaidPricingPlanListAPIView(generics.ListAPIView):
    """GET /api/pricing-plans/ — active prepaid packages only (additive)."""

    permission_classes = [AllowAny]
    serializer_class = PricingPlanListSerializer

    def get_queryset(self):
        return (
            PricingPlan.objects.filter(
                is_active=True,
                plan_kind=PricingPlan.PlanKind.PREPAID_PACKAGE,
            )
            .exclude(package_price__isnull=True)
            .exclude(package_duration_minutes__isnull=True)
            .order_by("package_duration_minutes", "name")
        )


class PricingPlanDetailAPIView(generics.RetrieveAPIView):
    """GET /api/pricing-plans/<id>/ — single plan (additive)."""

    permission_classes = [AllowAny]
    queryset = PricingPlan.objects.all()
    serializer_class = PricingPlanDetailSerializer
