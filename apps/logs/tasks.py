import logging
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from LT_AMS_API.models import Site, Camera
from .models import DetectionLog

logger = logging.getLogger(__name__)


def resolve_site_pk(raw_site_id):
    """Safely resolves site_id integer, numeric string, or site code to Site PK."""
    if not raw_site_id:
        return None
    if isinstance(raw_site_id, int):
        return raw_site_id
    if isinstance(raw_site_id, str):
        if raw_site_id.isdigit():
            return int(raw_site_id)
        site_obj = Site.objects.filter(code=raw_site_id).first() or Site.objects.filter(name=raw_site_id).first()
        if site_obj:
            return site_obj.site_id
    return None


def resolve_camera_pk(raw_camera_id):
    """Safely resolves camera_id integer, numeric string, or camera name to Camera PK."""
    if not raw_camera_id:
        return None
    if isinstance(raw_camera_id, int):
        return raw_camera_id
    if isinstance(raw_camera_id, str):
        if raw_camera_id.isdigit():
            return int(raw_camera_id)
        cam_obj = Camera.objects.filter(name=raw_camera_id).first()
        if cam_obj:
            return cam_obj.camera_id
    return None


@shared_task
def process_detection_batch_task(batch_data):
    """
    Celery task to bulk insert computer vision detection logs from Jetson edge devices
    and broadcast high-priority alerts to WebSocket channel layer groups in real time.
    """
    if not batch_data:
        return {"status": "empty", "count": 0}

    if isinstance(batch_data, dict) and "detections" in batch_data:
        detections = batch_data["detections"]
        default_site_id = batch_data.get("site_id") or batch_data.get("siteId")
        default_camera_id = batch_data.get("camera_id") or batch_data.get("cameraId")
    elif isinstance(batch_data, list):
        detections = batch_data
        default_site_id = None
        default_camera_id = None
    else:
        detections = [batch_data]
        default_site_id = None
        default_camera_id = None

    logs_to_create = []
    alerts_to_broadcast = []

    for item in detections:
        if not isinstance(item, dict):
            continue

        raw_site_id = item.get("site_id") or item.get("siteId") or default_site_id
        raw_camera_id = item.get("camera_id") or item.get("cameraId") or default_camera_id

        site_id = resolve_site_pk(raw_site_id)
        camera_id = resolve_camera_pk(raw_camera_id)

        detection_type = item.get("detection_type") or item.get("type") or item.get("alert_type") or "unknown"
        
        try:
            confidence = float(item.get("confidence", 0.0))
        except (ValueError, TypeError):
            confidence = 0.0

        bbox = item.get("bbox") or item.get("bounding_box") or item.get("boundingBox")
        snapshot = item.get("snapshot") or item.get("image_url") or item.get("snapshot_url")
        severity = str(item.get("severity", "MEDIUM")).upper()
        is_alert = item.get("is_alert", severity in ["HIGH", "CRITICAL"])
        ts = item.get("timestamp") or timezone.now()

        log_obj = DetectionLog(
            camera_id=camera_id,
            site_id=site_id,
            detection_type=detection_type,
            confidence=confidence,
            bbox=bbox,
            snapshot=snapshot,
            severity=severity,
            is_alert=is_alert,
            timestamp=ts,
        )
        logs_to_create.append(log_obj)

        if is_alert or severity in ["HIGH", "CRITICAL"]:
            alerts_to_broadcast.append({
                "site_id": site_id or raw_site_id,
                "camera_id": camera_id or raw_camera_id,
                "detection_type": detection_type,
                "confidence": confidence,
                "bbox": bbox,
                "snapshot": snapshot,
                "severity": severity,
                "is_alert": is_alert,
                "timestamp": str(ts),
            })

    # High-throughput bulk database insertion
    created_logs = []
    if logs_to_create:
        created_logs = DetectionLog.objects.bulk_create(logs_to_create)
    count = len(created_logs)

    # Real-time WebSocket broadcasting
    channel_layer = get_channel_layer()
    if channel_layer and alerts_to_broadcast:
        for alert in alerts_to_broadcast:
            broadcast_site_id = alert.get("site_id")
            if broadcast_site_id:
                group_name = f"site_{broadcast_site_id}_alerts"
                try:
                    async_to_sync(channel_layer.group_send)(
                        group_name,
                        {
                            "type": "alert.message",
                            "alert": alert,
                            "site_id": broadcast_site_id,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Could not broadcast alert to group {group_name}: {e}")

    logger.info(f"Successfully stored {count} detection logs in database. Broadcasted {len(alerts_to_broadcast)} alerts.")
    return {"status": "success", "processed_count": count, "alert_count": len(alerts_to_broadcast)}
