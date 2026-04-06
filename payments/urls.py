from django.urls import path

from . import api_views

urlpatterns = [
    path("payments/stk-callback/", api_views.StkCallbackAPIView.as_view(), name="api_payments_stk_callback"),
    path(
        "payments/<int:pk>/retry-stk/",
        api_views.PaymentRetryStkAPIView.as_view(),
        name="api_payment_retry_stk",
    ),
    path("payments/<int:pk>/", api_views.PaymentDetailAPIView.as_view(), name="api_payment_detail"),
    path("payments/", api_views.PaymentListAPIView.as_view(), name="api_payments_list"),
]
