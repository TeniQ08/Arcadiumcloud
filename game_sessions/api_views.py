from django.core.exceptions import ValidationError
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import STAFF_API_PERMISSIONS, is_admin, is_cashier
from stations.models import Station

from .dashboard_payload import open_sessions_queryset, session_payload_for_dashboard
from .models import GameSession
from .prepaid_services import (
    cancel_session,
    create_paid_extension_and_request_payment,
    create_session_and_request_payment,
    manual_extend_session,
    pause_session,
    resume_session,
)
from .serializers import CreateStkSessionSerializer, ManualExtendSessionSerializer, PaidExtendSessionSerializer
from .services import mark_expired_sessions
from .summary import build_dashboard_summary


def _validation_error_response(exc: ValidationError) -> Response:
    if getattr(exc, "message_dict", None):
        return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)
    messages = list(exc.messages) if hasattr(exc, "messages") else [str(exc)]
    return Response({"detail": messages}, status=status.HTTP_400_BAD_REQUEST)


def _can_paid_extend(user) -> bool:
    return is_admin(user) or is_cashier(user)


def _can_manual_extend(user) -> bool:
    if is_admin(user):
        return True
    if is_cashier(user):
        return bool(getattr(settings, "ALLOW_CASHIER_MANUAL_EXTEND", False))
    return False


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


class PauseSessionAPIView(APIView):
    """POST /api/sessions/<id>/pause/ — pause an active session."""

    permission_classes = STAFF_API_PERMISSIONS

    def post(self, request, pk: int):
        try:
            session = pause_session(pk)
        except ValidationError as exc:
            return _validation_error_response(exc)
        except GameSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Session pause requested.", "session": session_payload_for_dashboard(session)})


class ResumeSessionAPIView(APIView):
    """POST /api/sessions/<id>/resume/ — resume a paused session."""

    permission_classes = STAFF_API_PERMISSIONS

    def post(self, request, pk: int):
        try:
            session = resume_session(pk)
        except ValidationError as exc:
            return _validation_error_response(exc)
        except GameSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Session resume requested.", "session": session_payload_for_dashboard(session)})


class PaidExtendSessionAPIView(APIView):
    """POST /api/sessions/<id>/paid-extend/ — request STK payment for extra time."""

    permission_classes = STAFF_API_PERMISSIONS

    def post(self, request, pk: int):
        if not _can_paid_extend(request.user):
            return Response({"detail": "You do not have permission to request paid extensions."}, status=status.HTTP_403_FORBIDDEN)
        serializer = PaidExtendSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            session, payment = create_paid_extension_and_request_payment(
                session_id=pk,
                pricing_plan_id=data.get("pricing_plan_id"),
                duration_minutes=data.get("duration_minutes"),
                amount=data.get("amount"),
                customer_phone=data.get("customer_phone") or "",
                requested_by=request.user,
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        except (GameSession.DoesNotExist, Station.DoesNotExist):
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "message": "Paid extension STK push initiated.",
                "session": session_payload_for_dashboard(session),
                "payment": {
                    "id": payment.id,
                    "status": payment.status,
                    "amount_due": str(payment.amount_due),
                    "checkout_request_id": payment.checkout_request_id,
                    "extension_duration_minutes": payment.extension_duration_minutes,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class ManualExtendSessionAPIView(APIView):
    """POST /api/sessions/<id>/manual-extend/ — add time without payment."""

    permission_classes = STAFF_API_PERMISSIONS

    def post(self, request, pk: int):
        if not _can_manual_extend(request.user):
            return Response({"detail": "You do not have permission to manually extend sessions."}, status=status.HTTP_403_FORBIDDEN)
        serializer = ManualExtendSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            session, adjustment = manual_extend_session(
                session_id=pk,
                duration_minutes=data["duration_minutes"],
                reason=data["reason"],
                performed_by=request.user,
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        except GameSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "message": "Session manually extended.",
                "session": session_payload_for_dashboard(session),
                "adjustment": {
                    "id": adjustment.id,
                    "minutes_added": adjustment.minutes_added,
                    "reason": adjustment.reason,
                    "performed_by_id": adjustment.performed_by_id,
                    "created_at": adjustment.created_at.isoformat(),
                },
            },
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
                "message": "Session created; STK push initiated.",
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
