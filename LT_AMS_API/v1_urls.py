from django.urls import path
from . import v1_views

urlpatterns = [
    # Projects API
    path('projects/', v1_views.V1ProjectsAPIView.as_view(), name='v1_projects'),

    # Sites API
    path('sites/', v1_views.V1SitesAPIView.as_view(), name='v1_sites'),

    # Chainages API
    path('chainages/', v1_views.V1ChainagesAPIView.as_view(), name='v1_chainages'),

    # Dashboard Metrics & Trends API
    path('dashboard/metrics/', v1_views.V1DashboardMetricsAPIView.as_view(), name='v1_dashboard_metrics'),
    path('dashboard/progress-trend/', v1_views.V1DashboardProgressTrendAPIView.as_view(), name='v1_dashboard_progress_trend'),

    # Safety Alerts API
    path('safety/alerts/', v1_views.V1SafetyAlertsAPIView.as_view(), name='v1_safety_alerts'),

    # Workforce Attendance API
    path('workers/attendance/', v1_views.V1WorkerAttendanceAPIView.as_view(), name='v1_worker_attendance'),

    # Cameras API
    path('cameras/', v1_views.V1CamerasAPIView.as_view(), name='v1_cameras'),
]
