from django.urls import path
from .views import BulkCameraLogIngestionView

urlpatterns = [
    path('v1/logs/ingest/', BulkCameraLogIngestionView.as_view(), name='bulk_camera_log_ingest_v1'),
    path('logs/ingest/', BulkCameraLogIngestionView.as_view(), name='bulk_camera_log_ingest'),
    path('v1/logs/', BulkCameraLogIngestionView.as_view(), name='camera_log_list_v1'),
    path('logs/', BulkCameraLogIngestionView.as_view(), name='camera_log_list'),
]
