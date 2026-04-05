from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from stations.models import Station

from .models import GameSession
from .serializers import ExtendSessionSerializer, SessionActionSerializer, StartSessionSerializer
from .services import end_session, extend_session, pause_session, resume_session, start_session


def _session_payload(session: GameSession) -> dict:
    return {
        "id": session.id,
        "station_id": session.station_id,
        "opened_by_id": session.opened_by_id,
        "customer_name": session.customer_name,
        "start_time": session.start_time.isoformat(),
        "expected_end_time": session.expected_end_time.isoformat(),
        "actual_end_time": session.actual_end_time.isoformat() if session.actual_end_time else None,
        "status": session.status,
        "rate_per_hour": str(session.rate_per_hour),
    }


def _validation_error_response(exc: ValidationError) -> Response:
    if getattr(exc, "message_dict", None):
        return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)
    messages = list(exc.messages) if hasattr(exc, "messages") else [str(exc)]
    return Response({"detail": messages}, status=status.HTTP_400_BAD_REQUEST)


class OpenSessionsAPIView(APIView):
    """
    Read-only list of open sessions (active/paused/expired), newest first.
    MVP: no auth/filtering/pagination.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        qs = (
            GameSession.objects.exclude(status=GameSession.Status.COMPLETED)
            .select_related("station")
            .order_by("-start_time")
        )
        return Response(
            {
                "sessions": [
                    {
                        **_session_payload(s),
                        "station_name": s.station.name,
                    }
                    for s in qs
                ]
            },
            status=status.HTTP_200_OK,
        )


class StartSessionAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

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
            {"message": "Session started.", "session": _session_payload(session)},
            status=status.HTTP_201_CREATED,
        )


class PauseSessionAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

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
        return Response({"message": "Session paused.", "session": _session_payload(session)}, status=status.HTTP_200_OK)


class ResumeSessionAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

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
            {"message": "Session resumed.", "session": _session_payload(session)},
            status=status.HTTP_200_OK,
        )


class EndSessionAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

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
                "session": _session_payload(session),
                "payment": {
                    "amount_due": str(payment.amount_due),
                    "amount_paid": str(payment.amount_paid),
                    "payment_status": payment.status,
                },
            },
            status=status.HTTP_200_OK,
        )


class ExtendSessionAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

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
            {"message": "Session extended.", "session": _session_payload(session)},
            status=status.HTTP_200_OK,
        )
