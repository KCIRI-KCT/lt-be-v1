from django.db import models
from django.utils import timezone
from LT_AMS_API.models import Camera, Site


class DetectionLog(models.Model):
    """
    DetectionLog Model representing table 'detection_log'.
    Stores high-throughput computer vision edge detection logs sent from Jetson Orin Nano.
    """
    log_id = models.BigAutoField(primary_key=True, db_column='log_id')
    camera = models.ForeignKey(
        Camera,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detection_logs',
        db_column='camera_id'
    )
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='detection_logs',
        db_column='site_id'
    )
    detection_type = models.CharField(max_length=100, db_index=True, db_column='detection_type')
    confidence = models.FloatField(default=0.0, db_column='confidence')
    bbox = models.JSONField(null=True, blank=True, db_column='bbox')
    snapshot = models.TextField(null=True, blank=True, db_column='snapshot')
    severity = models.CharField(max_length=20, default='MEDIUM', db_column='severity')
    is_alert = models.BooleanField(default=False, db_index=True, db_column='is_alert')
    timestamp = models.DateTimeField(default=timezone.now, db_index=True, db_column='timestamp')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')

    class Meta:
        db_table = 'detection_log'
        verbose_name = 'Detection Log'
        verbose_name_plural = 'Detection Logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.detection_type} ({self.confidence:.2f}) - Log {self.log_id}"
