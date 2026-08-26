import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from LT_AMS_API.models import Project, Site, Camera
from apps.logs.models import DetectionLog
from apps.logs.tasks import process_detection_batch_task
from apps.logs.consumers import DetectionAlertConsumer


class LogsAppTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.project = Project.objects.create(
            name="Test Project",
            code="PRJ-LOG-01"
        )
        self.site = Site.objects.create(
            name="Test Site 101",
            code="SITE-LOG-101",
            project=self.project
        )
        self.camera = Camera.objects.create(
            name="North Gate Camera",
            rtsp_url="rtsp://192.168.1.100/stream1",
            site=self.site
        )

    def test_detection_log_model(self):
        log = DetectionLog.objects.create(
            camera=self.camera,
            site=self.site,
            detection_type="no_helmet",
            confidence=0.95,
            severity="HIGH",
            is_alert=True
        )
        self.assertEqual(log.detection_type, "no_helmet")
        self.assertEqual(log.severity, "HIGH")
        self.assertTrue(log.is_alert)
        self.assertIn("no_helmet", str(log))

    def test_bulk_camera_log_ingestion_view(self):
        url = reverse('bulk_camera_log_ingest_v1')
        payload = [
            {
                "site_id": self.site.site_id,
                "camera_id": self.camera.camera_id,
                "detection_type": "no_vest",
                "confidence": 0.88,
                "severity": "HIGH",
                "is_alert": True
            },
            {
                "site_id": self.site.site_id,
                "camera_id": self.camera.camera_id,
                "detection_type": "person",
                "confidence": 0.92,
                "severity": "LOW",
                "is_alert": False
            }
        ]

        response = self.client.post(url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data.get('status'), 'processing')
        self.assertEqual(response.data.get('batch_count'), 2)

        # Verify logs were saved to database
        self.assertEqual(DetectionLog.objects.count(), 2)

    def test_get_camera_log_list(self):
        DetectionLog.objects.create(
            camera=self.camera,
            site=self.site,
            detection_type="fire_detected",
            confidence=0.99,
            severity="CRITICAL",
            is_alert=True
        )

        url = reverse('camera_log_list_v1')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['detection_type'], 'fire_detected')

    def test_process_detection_batch_task_with_string_codes(self):
        batch_payload = {
            "site_id": "SITE-LOG-101",
            "camera_id": "North Gate Camera",
            "detections": [
                {
                    "detection_type": "no_helmet",
                    "confidence": 0.96,
                    "severity": "CRITICAL",
                    "is_alert": True
                },
                {
                    "detection_type": "person",
                    "confidence": 0.85,
                    "severity": "LOW",
                    "is_alert": False
                }
            ]
        }

        result = process_detection_batch_task(batch_payload)
        self.assertEqual(result.get('status'), 'success')
        self.assertEqual(result.get('processed_count'), 2)

        self.assertEqual(DetectionLog.objects.count(), 2)
        log = DetectionLog.objects.filter(detection_type="no_helmet").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.site, self.site)
        self.assertEqual(log.camera, self.camera)

    async def test_websocket_consumer_alert_channel(self):
        site_id = self.site.site_id
        communicator = WebsocketCommunicator(
            DetectionAlertConsumer.as_asgi(),
            f"/ws/alerts/{site_id}/"
        )
        communicator.scope['url_route'] = {'kwargs': {'site_id': str(site_id)}}
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Broadcast event to group
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"site_{site_id}_alerts",
            {
                "type": "alert.message",
                "alert": {
                    "site_id": site_id,
                    "detection_type": "no_helmet",
                    "severity": "CRITICAL"
                }
            }
        )

        response = await communicator.receive_json_from()
        self.assertEqual(response.get('type'), 'alert.message')
        self.assertEqual(response.get('alert', {}).get('detection_type'), 'no_helmet')

        await communicator.disconnect()
