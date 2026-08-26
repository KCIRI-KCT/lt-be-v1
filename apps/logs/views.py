from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .serializers import (
    DetectionBatchPayloadSerializer,
    DetectionIngestionResponseSerializer,
    DetectionLogSerializer
)
from .models import DetectionLog
from .tasks import process_detection_batch_task


class BulkCameraLogIngestionView(APIView):
    """
    High-throughput edge ingestion endpoint for Jetson Orin Nano computer vision devices.
    Accepts detection batches (POST /api/v1/logs/ingest/) and stores logs in database.
    Also provides GET endpoint to list and inspect stored detection logs.
    """
    permission_classes = [AllowAny]
    serializer_class = DetectionBatchPayloadSerializer

    @extend_schema(
        summary="List camera detection logs",
        description="Retrieves recent computer vision detection logs stored in the database.",
        parameters=[
            OpenApiParameter(name='site_id', description='Filter by site ID', required=False, type=int),
            OpenApiParameter(name='severity', description='Filter by severity (HIGH, CRITICAL, MEDIUM, LOW)', required=False, type=str),
            OpenApiParameter(name='is_alert', description='Filter by alert status (true/false)', required=False, type=bool),
            OpenApiParameter(name='limit', description='Number of records to return (default 50)', required=False, type=int),
        ],
        responses={200: DetectionLogSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        qs = DetectionLog.objects.all().select_related('camera', 'site')
        site_id = request.query_params.get('site_id')
        severity = request.query_params.get('severity')
        is_alert = request.query_params.get('is_alert')
        limit = int(request.query_params.get('limit', 50))

        if site_id and site_id.isdigit():
            qs = qs.filter(site_id=int(site_id))
        if severity:
            qs = qs.filter(severity__iexact=severity)
        if is_alert is not None:
            qs = qs.filter(is_alert=is_alert.lower() == 'true')

        logs = qs[:limit]
        serializer = DetectionLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Ingest edge camera detection batch",
        description="Receives high-frequency camera detection logs from Jetson edge devices, saves them to the database, and broadcasts alerts.",
        request=DetectionBatchPayloadSerializer,
        responses={202: DetectionIngestionResponseSerializer}
    )
    def post(self, request, *args, **kwargs):
        data = request.data
        if not data:
            return Response(
                {"error": "No detection payload provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Count items for response metadata
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict) and "detections" in data and isinstance(data["detections"], list):
            count = len(data["detections"])
        else:
            count = 1

        # Always ensure database persistence
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
            res = process_detection_batch_task(data)
            task_id = "eager_sync_execution"
        else:
            try:
                task = process_detection_batch_task.delay(data)
                task_id = task.id
            except Exception:
                # Direct fallback if Celery/Broker is not running
                res = process_detection_batch_task(data)
                task_id = "fallback_sync_execution"

        return Response(
            {
                "status": "processing",
                "message": "Detection batch accepted and stored in database",
                "task_id": task_id,
                "batch_count": count
            },
            status=status.HTTP_202_ACCEPTED
        )
