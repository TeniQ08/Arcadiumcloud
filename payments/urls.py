from django.urls import path

from . import api_views

urlpatterns = [
    path("payments/stk-callback/", api_views.StkCallbackAPIView.as_view(), name="api_payments_stk_callback"),
]
