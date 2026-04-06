from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import STAFF_API_PERMISSIONS
from stations.models import Station

from .dashboard_payload import open_sessions_queryset, session_payload_for_dashboard
from .models import GameSession
from .prepaid_services import cancel_session, create_session_and_request_payment
from .serializers import CreateStkSessionSerializer
from .services import mark_expired_sessions
from .summary import build_dashboard_summary


def _validation_error_response(exc: ValidationError) -> Response:
    if getattr(exc, "message_dict", None):
        return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)
    messages = list(exc.messages) if hasattr(exc, "messages") else [str(exc)]
    return Response({"detail": messages}, status=status.HTTP_400_BAD_REQUEST)


class DashboardSummaryAPIView(APIView):
    """GET /api/dashboard/summary/ — aggregated counts (staff session required)."""

    permission_classes = STAFF_API_PERMISSIONS

    def get(self, request):
        mark_expired_sessions()
        return Response(build_dashboard_summary(), status=status.HTTP_200_OK)


class GameSessionListAPIView(APIView):
    """GET /api/sessions/ — recent sessions (newest first), staff only."""

    permission_classes = STAFF_API_PERMISSIONS

    def get(self, request):
        mark_expired_sessions()
        qs = GameSession.objects.select_related("station").order_by("-created_at")[:200]
        return Response(
            {
                "sessions": [
                    {
                        **session_payload_for_dashboard(s),
                        "station_name": s.station.name,
                    }
                    for s in qs
                ]
            },
            status=status.HTTP_200_OK,
        )


class GameSessionDetailAPIView(APIView):
    """GET /api/sessions/<id>/ — single session payload, staff only."""

    permission_classes = STAFF_API_PERMISSIONS

    def get(self, request, pk: int):
        mark_expired_sessions()
        try:
            s = GameSession.objects.select_related("station").get(pk=pk)
        except GameSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                **session_payload_for_dashboard(s),
                "station_name": s.station.name,
            },
            status=status.HTTP_200_OK,
        )


class CancelSessionAPIView(APIView):
    """POST /api/sessions/<id>/cancel/ — cancel before activation completes."""

    permission_classes = STAFF_API_PERMISSIONS

    def post(self, request, pk: int):
        try:
            session = cancel_session(pk)
        except ValidationError as exc:
            return _validation_error_response(exc)
        except GameSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {"message": "Session cancelled.", "session": session_payload_for_dashboard(session)},
            status=status.HTTP_200_OK,
        )


class OpenSessionsAPIView(APIView):
    """GET /api/sessions/open/ — open sessions for the control panel."""

    permission_classes = STAFF_API_PERMISSIONS

    def get(self, request):
        mark_expired_sessions()
        qs = open_sessions_queryset()
        return Response(
            {
                "sessions": [
                    {
                        **session_payload_for_dashboard(s),
                        "station_name": s.station.name,
                    }
                    for s in qs
                ]
            },
            status=status.HTTP_200_OK,
        )


class CreateStkSessionAPIView(APIView):
    """POST /api/sessions/create-and-request-payment/ — STK entrypoint."""

    permission_classes = STAFF_API_PERMISSIONS

    def post(self, request):
        serializer = CreateStkSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            session, payment = create_session_and_request_payment(
                station_id=data["station_id"],
                pricing_plan_id=data["pricing_plan_id"],
                customer_phone=data["customer_phone"],
                game_name=data.get("game_name") or "",
                notes=data.get("notes") or "",
                opened_by=request.user if request.user.is_authenticated else None,
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        except Station.DoesNotExist:
            return Response({"detail": "Station not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "message": "Session created; STK push initiated (stub).",
                "session": session_payload_for_dashboard(session),
                "payment": {
                    "id": payment.id,
                    "status": payment.status,
                    "amount_due": str(payment.amount_due),
                    "checkout_request_id": payment.checkout_request_id,
                },
            },
            status=status.HTTP_201_CREATED,
        )
