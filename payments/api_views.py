from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from game_sessions.prepaid_services import handle_stk_callback


class StkCallbackAPIView(APIView):
    """POST /api/payments/stk-callback/ — M-Pesa STK callback (Daraja-compatible JSON)."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        payment = handle_stk_callback(raw_body=request.body)
        if payment is None:
            return Response({"detail": "Not processed."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True, "payment_id": payment.id}, status=status.HTTP_200_OK)
