import logging

from django.core.exceptions import ValidationError
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import STAFF_API_PERMISSIONS
from game_sessions.prepaid_services import STK_CALLBACK_MAX_BODY_BYTES, handle_stk_callback, retry_stk_push_for_payment

from .models import Payment
from .serializers import PaymentSerializer

logger = logging.getLogger(__name__)


class StkCallbackAPIView(APIView):
    """POST /api/payments/stk-callback/ — M-Pesa STK callback (Daraja-compatible JSON)."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        body = request.body
        if not isinstance(body, (bytes, bytearray)) or len(body) > STK_CALLBACK_MAX_BODY_BYTES:
            logger.warning("STK callback HTTP rejected: missing body or size over limit")
            payment = None
        else:
            payment = handle_stk_callback(raw_body=body)
        if payment is None:
            return Response({"detail": "Not processed."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True, "payment_id": payment.id}, status=status.HTTP_200_OK)


class PaymentListAPIView(generics.ListAPIView):
    """GET /api/payments/ — newest first (staff only)."""

    permission_classes = STAFF_API_PERMISSIONS
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return Payment.objects.select_related("session").order_by("-created_at")[:200]


class PaymentDetailAPIView(generics.RetrieveAPIView):
    """GET /api/payments/<id>/ — staff only."""

    permission_classes = STAFF_API_PERMISSIONS
    serializer_class = PaymentSerializer
    queryset = Payment.objects.select_related("session").all()


def _payment_validation_error(exc: ValidationError) -> Response:
    if getattr(exc, "message_dict", None):
        return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)
    messages = list(exc.messages) if hasattr(exc, "messages") else [str(exc)]
    return Response({"detail": messages}, status=status.HTTP_400_BAD_REQUEST)


class PaymentRetryStkAPIView(APIView):
    """POST /api/payments/<id>/retry-stk/ — re-issue STK stub for a pending payment."""

    permission_classes = STAFF_API_PERMISSIONS

    def post(self, request, pk: int):
        try:
            payment = retry_stk_push_for_payment(pk)
        except ValidationError as exc:
            return _payment_validation_error(exc)
        except Payment.DoesNotExist:
            return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "message": "STK retry initiated.",
                "payment": PaymentSerializer(payment).data,
            },
            status=status.HTTP_200_OK,
        )
