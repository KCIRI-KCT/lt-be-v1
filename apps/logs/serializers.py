from rest_framework import serializers
from .models import DetectionLog


class DetectionItemSerializer(serializers.Serializer):
    site_id = serializers.IntegerField(required=False, allow_null=True)
    camera_id = serializers.IntegerField(required=False, allow_null=True)
    detection_type = serializers.CharField(max_length=100, required=False)
    type = serializers.CharField(max_length=100, required=False)
    confidence = serializers.FloatField(required=False, default=0.0)
    bbox = serializers.JSONField(required=False, allow_null=True)
    bounding_box = serializers.JSONField(required=False, allow_null=True)
    snapshot = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    image_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    severity = serializers.CharField(max_length=20, required=False, default='MEDIUM')
    is_alert = serializers.BooleanField(required=False, default=False)
    timestamp = serializers.DateTimeField(required=False)


class DetectionBatchPayloadSerializer(serializers.Serializer):
    site_id = serializers.IntegerField(required=False, allow_null=True)
    camera_id = serializers.IntegerField(required=False, allow_null=True)
    detections = DetectionItemSerializer(many=True, required=False)


class DetectionIngestionResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()
    task_id = serializers.CharField()
    batch_count = serializers.IntegerField()


class DetectionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectionLog
        fields = '__all__'
