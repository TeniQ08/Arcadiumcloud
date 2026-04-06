from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import STAFF_API_PERMISSIONS
from stations.models import Station

from .compatibility import dashboard_session_payload, open_sessions_queryset
from .models import GameSession
from .prepaid_services import cancel_prepaid_session, create_session_and_request_payment
from .summary import build_dashboard_summary
from .serializers import (
    CreatePrepaidSessionSerializer,
    ExtendSessionSerializer,
    SessionActionSerializer,
    StartSessionSerializer,
)
from .services import (
    end_session,
    extend_session,
    mark_expired_sessions,
    pause_session,
    resume_session,
    start_session,
)


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
        qs = (
            GameSession.objects.select_related("station")
            .order_by("-created_at")[:200]
        )
        return Response(
            {
                "sessions": [
                    {
                        **dashboard_session_payload(s),
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
                **dashboard_session_payload(s),
                "station_name": s.station.name,
            },
            status=status.HTTP_200_OK,
        )


class CancelPrepaidSessionAPIView(APIView):
    """POST /api/sessions/<id>/cancel/ — cancel prepaid before activation completes."""

    permission_classes = STAFF_API_PERMISSIONS

    def post(self, request, pk: int):
        try:
            session = cancel_prepaid_session(pk)
        except ValidationError as exc:
            return _validation_error_response(exc)
        except GameSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {"message": "Prepaid session cancelled.", "session": dashboard_session_payload(session)},
            status=status.HTTP_200_OK,
        )


class OpenSessionsAPIView(APIView):
    """
    Read-only list of open sessions (active/paused/expired), newest first.
    Staff session required (control panel).
    """

    permission_classes = STAFF_API_PERMISSIONS

    def get(self, request):
        mark_expired_sessions()
        qs = open_sessions_queryset()
        return Response(
            {
                "sessions": [
                    {
                        **dashboard_session_payload(s),
                        "station_name": s.station.name,
                    }
                    for s in qs
                ]
            },
            status=status.HTTP_200_OK,
        )


class StartSessionAPIView(APIView):
    permission_classes = STAFF_API_PERMISSIONS

    def post(self, request):
        serializer = StartSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            session = start_session(
                station_id=data["station_id"],
                opened_by=None,
                duration_minutes=data["duration_minutes"],
                customer_name=data.get("customer_name") or "",
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        except Station.DoesNotExist:
            return Response({"detail": "Station not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {"message": "Session started.", "session": dashboard_session_payload(session)},
            status=status.HTTP_201_CREATED,
        )


class CreatePrepaidSessionAPIView(APIView):
    """POST /api/sessions/create-and-request-payment/ — additive prepaid STK entrypoint."""

    permission_classes = STAFF_API_PERMISSIONS

    def post(self, request):
        serializer = CreatePrepaidSessionSerializer(data=request.data)
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
                "message": "Prepaid session created; STK push initiated (stub).",
                "session": dashboard_session_payload(session),
                "payment": {
                    "id": payment.id,
                    "status": payment.status,
                    "amount_due": str(payment.amount_due),
                    "checkout_request_id": payment.checkout_request_id,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class PauseSessionAPIView(APIView):
    permission_classes = STAFF_API_PERMISSIONS

    def post(self, request):
        serializer = SessionActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_id = serializer.validated_data["session_id"]
        try:
            session = pause_session(session_id=session_id)
        except ValidationError as exc:
            return _validation_error_response(exc)
        except GameSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Session paused.", "session": dashboard_session_payload(session)}, status=status.HTTP_200_OK)


class ResumeSessionAPIView(APIView):
    permission_classes = STAFF_API_PERMISSIONS

    def post(self, request):
        serializer = SessionActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_id = serializer.validated_data["session_id"]
        try:
            session = resume_session(session_id=session_id)
        except ValidationError as exc:
            return _validation_error_response(exc)
        except GameSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {"message": "Session resumed.", "session": dashboard_session_payload(session)},
            status=status.HTTP_200_OK,
        )


class EndSessionAPIView(APIView):
    permission_classes = STAFF_API_PERMISSIONS

    def post(self, request):
        serializer = SessionActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_id = serializer.validated_data["session_id"]
        try:
            session = end_session(session_id=session_id)
        except ValidationError as exc:
            return _validation_error_response(exc)
        except GameSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        payment = session.payment
        return Response(
            {
                "message": "Session ended.",
                "session": dashboard_session_payload(session),
                "payment": {
                    "amount_due": str(payment.amount_due),
                    "amount_paid": str(payment.amount_paid),
                    "payment_status": payment.status,
                },
            },
            status=status.HTTP_200_OK,
        )


class ExtendSessionAPIView(APIView):
    permission_classes = STAFF_API_PERMISSIONS

    def post(self, request):
        serializer = ExtendSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            session = extend_session(
                session_id=data["session_id"],
                additional_minutes=data["additional_minutes"],
                extended_by=None,
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        except GameSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {"message": "Session extended.", "session": dashboard_session_payload(session)},
            status=status.HTTP_200_OK,
        )
