from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DeviceCommand, StationDevice
from .serializers import (
    CommandResultSerializer,
    HeartbeatSerializer,
    NextCommandQuerySerializer,
    acknowledge_command_status,
)
from .services import (
    apply_heartbeat_fields,
    authenticate_device,
    mark_offline_devices,
    reset_stale_sent_commands,
)


class DeviceHeartbeatAPIView(APIView):
    """POST /api/devices/heartbeat/"""

    authentication_classes = []
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = HeartbeatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        device = authenticate_device(data["device_id"], data["device_secret"])
        if device is None:
            return Response({"detail": "Invalid device credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        device = StationDevice.objects.select_for_update().get(pk=device.pk)
        apply_heartbeat_fields(device, data)
        device.save()

        mark_offline_devices()

        return Response(
            {
                "message": "Heartbeat received.",
                "device": {
                    "device_id": device.device_id,
                    "station_id": device.station_id,
                    "status": device.status,
                    "relay_state": device.relay_state,
                    "fault_state": device.fault_state,
                    "last_heartbeat_at": device.last_heartbeat_at.isoformat() if device.last_heartbeat_at else None,
                },
            },
            status=status.HTTP_200_OK,
        )


class DeviceNextCommandAPIView(APIView):
    """GET /api/devices/next-command/ — flat command_id + command for ESP32 firmware."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @transaction.atomic
    def get(self, request):
        serializer = NextCommandQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        device = authenticate_device(data["device_id"], data["device_secret"])
        if device is None:
            return Response({"detail": "Invalid device credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        mark_offline_devices()
        reset_stale_sent_commands(timeout_seconds=30)

        cmd = (
            DeviceCommand.objects.select_for_update()
            .filter(device=device, status=DeviceCommand.Status.PENDING)
            .order_by("created_at")
            .first()
        )

        if cmd is None:
            return Response({"command_id": None, "command": None}, status=status.HTTP_200_OK)

        cmd.status = DeviceCommand.Status.SENT
        cmd.sent_at = timezone.now()
        cmd.save(update_fields=["status", "sent_at"])

        return Response(
            {"command_id": cmd.id, "command": cmd.command},
            status=status.HTTP_200_OK,
        )


class DeviceCommandResultAPIView(APIView):
    """POST /api/devices/command-result/"""

    authentication_classes = []
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = CommandResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        device = authenticate_device(data["device_id"], data["device_secret"])
        if device is None:
            return Response({"detail": "Invalid device credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            cmd = DeviceCommand.objects.select_for_update().get(id=data["command_id"], device=device)
        except DeviceCommand.DoesNotExist:
            return Response({"detail": "Command not found."}, status=status.HTTP_404_NOT_FOUND)

        if cmd.status in (
            DeviceCommand.Status.ACKNOWLEDGED,
            DeviceCommand.Status.FAILED,
        ):
            return Response(
                {
                    "message": "Command already processed.",
                    "command": {
                        "id": cmd.id,
                        "status": cmd.status,
                    },
                },
                status=status.HTTP_200_OK,
            )

        cmd.status = acknowledge_command_status(data["status"])
        cmd.acknowledged_at = timezone.now()
        cmd.result_text = data.get("result_text", "")
        cmd.save(update_fields=["status", "acknowledged_at", "result_text"])

        return Response(
            {
                "message": "Command result recorded.",
                "command": {
                    "id": cmd.id,
                    "status": cmd.status,
                    "acknowledged_at": cmd.acknowledged_at.isoformat() if cmd.acknowledged_at else None,
                },
            },
            status=status.HTTP_200_OK,
        )
