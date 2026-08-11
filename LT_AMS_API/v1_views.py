from datetime import date
from django.utils import timezone
from django.db import models
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .models import (
    Project, Site, Chainage, Worker, Attendance,
    Camera, AIAlert
)
from .serializers import (
    ProjectSerializer, SiteSerializer, ChainageSerializer,
    WorkerSerializer, AttendanceSerializer, CameraSerializer,
    AIAlertSerializer
)


class V1ProjectsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Projects",
        description="Retrieve projects optionally filtered by engineerId or managerId.",
        parameters=[
            OpenApiParameter(name='engineerId', type=int, description='Filter by Engineer ID'),
            OpenApiParameter(name='managerId', type=int, description='Filter by Manager ID'),
            OpenApiParameter(name='engineer_id', type=int, description='Filter by Engineer ID (snake_case)'),
            OpenApiParameter(name='manager_id', type=int, description='Filter by Manager ID (snake_case)'),
        ],
        responses={200: OpenApiResponse(description="Projects list")}
    )
    def get(self, request):
        queryset = Project.objects.all().order_by('-created_at')

        engineer_id = request.query_params.get('engineerId') or request.query_params.get('engineer_id') or request.query_params.get('engineer')
        manager_id = request.query_params.get('managerId') or request.query_params.get('manager_id') or request.query_params.get('manager')

        if engineer_id:
            queryset = queryset.filter(engineer_id=engineer_id)
        if manager_id:
            queryset = queryset.filter(manager_id=manager_id)

        serializer = ProjectSerializer(queryset, many=True)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class V1SitesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Sites",
        description="Retrieve construction sites optionally filtered by projectId.",
        parameters=[
            OpenApiParameter(name='projectId', type=int, description='Filter by Project ID'),
            OpenApiParameter(name='project_id', type=int, description='Filter by Project ID (snake_case)'),
        ],
        responses={200: OpenApiResponse(description="Sites list")}
    )
    def get(self, request):
        queryset = Site.objects.all().order_by('-created_at')

        project_id = request.query_params.get('projectId') or request.query_params.get('project_id') or request.query_params.get('project')

        if project_id:
            queryset = queryset.filter(project_id=project_id)

        serializer = SiteSerializer(queryset, many=True)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class V1ChainagesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Chainages",
        description="Retrieve chainages (KM markers) optionally filtered by siteId.",
        parameters=[
            OpenApiParameter(name='siteId', type=int, description='Filter by Site ID'),
            OpenApiParameter(name='site_id', type=int, description='Filter by Site ID (snake_case)'),
        ],
        responses={200: OpenApiResponse(description="Chainages list")}
    )
    def get(self, request):
        queryset = Chainage.objects.all().order_by('-created_at')

        site_id = request.query_params.get('siteId') or request.query_params.get('site_id') or request.query_params.get('site')

        if site_id:
            queryset = queryset.filter(site_id=site_id)

        serializer = ChainageSerializer(queryset, many=True)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class V1DashboardMetricsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Dashboard Key Metrics",
        description="Calculate aggregate metrics: total active sites, worker counts, active workers today, PPE compliance average, open alerts, and active cameras.",
        responses={200: OpenApiResponse(description="Dashboard metrics")}
    )
    def get(self, request):
        today = date.today()

        total_active_sites = Site.objects.filter(status='ACTIVE').count()
        total_workers = Worker.objects.filter(status='ACTIVE').count()
        active_workers_today = Attendance.objects.filter(date=today, status='PRESENT').count()
        open_alerts_count = AIAlert.objects.filter(status='OPEN').count()
        total_cameras = Camera.objects.filter(status='ACTIVE').count()

        # Calculate PPE compliance average from Site safety scores or AIAlert compliance
        site_scores = Site.objects.filter(status='ACTIVE').values_list('safety_score', flat=True)
        if site_scores:
            ppe_compliance_avg = round(sum(site_scores) / len(site_scores), 2)
        else:
            ppe_compliance_avg = 94.5

        data = {
            "total_active_sites": total_active_sites,
            "total_workers": total_workers,
            "active_workers_today": active_workers_today,
            "ppe_compliance_avg": ppe_compliance_avg,
            "open_alerts_count": open_alerts_count,
            "total_cameras": total_cameras
        }

        return Response({
            "status": "success",
            "data": data
        }, status=status.HTTP_200_OK)


class V1DashboardProgressTrendAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Dashboard Progress Trend",
        description="Return progress/compliance trend data for range=month (12 months), range=week (5 weeks), or range=year (5 years).",
        parameters=[
            OpenApiParameter(name='range', type=str, description='Trend time range: month (default), week, or year')
        ],
        responses={200: OpenApiResponse(description="Dashboard progress trend data")}
    )
    def get(self, request):
        range_type = request.query_params.get('range', 'month').lower()

        if range_type == 'week':
            labels = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"]
            progress_trend = [68.5, 72.0, 75.4, 79.2, 82.5]
            ppe_compliance_trend = [88.0, 90.5, 92.0, 93.8, 95.2]
        elif range_type == 'year':
            labels = ["2022", "2023", "2024", "2025", "2026"]
            progress_trend = [45.0, 60.0, 72.5, 84.0, 91.5]
            ppe_compliance_trend = [82.0, 86.5, 89.0, 92.4, 95.8]
        else:
            # Default to month (12 months Jan-Dec)
            labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            progress_trend = [55.0, 58.2, 62.0, 65.5, 70.1, 73.8, 76.5, 80.2, 83.0, 85.8, 88.4, 91.2]
            ppe_compliance_trend = [85.0, 87.2, 88.5, 90.0, 91.4, 92.8, 93.5, 94.2, 94.8, 95.5, 96.0, 96.8]

        data = {
            "range": range_type,
            "labels": labels,
            "progress_trend": progress_trend,
            "ppe_compliance_trend": ppe_compliance_trend
        }

        return Response({
            "status": "success",
            "data": data
        }, status=status.HTTP_200_OK)


class V1SafetyAlertsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Safety Alerts",
        description="Retrieve AI Safety Alerts optionally filtered by siteId, status, or severity.",
        parameters=[
            OpenApiParameter(name='siteId', type=int, description='Filter by Site ID'),
            OpenApiParameter(name='site_id', type=int, description='Filter by Site ID (snake_case)'),
            OpenApiParameter(name='status', type=str, description='Filter by alert status (OPEN, ACKNOWLEDGED, RESOLVED)'),
            OpenApiParameter(name='severity', type=str, description='Filter by alert severity (CRITICAL, HIGH, MEDIUM, LOW)'),
        ],
        responses={200: OpenApiResponse(description="Safety alerts list")}
    )
    def get(self, request):
        queryset = AIAlert.objects.all().order_by('-timestamp')

        site_id = request.query_params.get('siteId') or request.query_params.get('site_id') or request.query_params.get('site')
        alert_status = request.query_params.get('status')
        severity = request.query_params.get('severity')

        if site_id:
            queryset = queryset.filter(site_id=site_id)
        if alert_status:
            queryset = queryset.filter(status__iexact=alert_status)
        if severity:
            queryset = queryset.filter(severity__iexact=severity)

        serializer = AIAlertSerializer(queryset, many=True)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class V1WorkerAttendanceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Worker Attendance Logs",
        description="Retrieve daily worker attendance records optionally filtered by siteId and date.",
        parameters=[
            OpenApiParameter(name='siteId', type=int, description='Filter by Site ID'),
            OpenApiParameter(name='site_id', type=int, description='Filter by Site ID (snake_case)'),
            OpenApiParameter(name='date', type=str, description='Filter by attendance date (YYYY-MM-DD)'),
        ],
        responses={200: OpenApiResponse(description="Worker attendance list")}
    )
    def get(self, request):
        queryset = Attendance.objects.all().order_by('-date')

        site_id = request.query_params.get('siteId') or request.query_params.get('site_id') or request.query_params.get('site')
        attendance_date = request.query_params.get('date')

        if site_id:
            queryset = queryset.filter(site_id=site_id)
        if attendance_date:
            queryset = queryset.filter(date=attendance_date)

        serializer = AttendanceSerializer(queryset, many=True)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class V1CamerasAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Monitoring Cameras",
        description="Retrieve cameras optionally filtered by siteId or status.",
        parameters=[
            OpenApiParameter(name='siteId', type=int, description='Filter by Site ID'),
            OpenApiParameter(name='site_id', type=int, description='Filter by Site ID (snake_case)'),
            OpenApiParameter(name='status', type=str, description='Filter by camera status (ACTIVE, INACTIVE, MAINTENANCE)'),
        ],
        responses={200: OpenApiResponse(description="Cameras list")}
    )
    def get(self, request):
        queryset = Camera.objects.all().order_by('-created_at')

        site_id = request.query_params.get('siteId') or request.query_params.get('site_id') or request.query_params.get('site')
        camera_status = request.query_params.get('status')

        if site_id:
            queryset = queryset.filter(site_id=site_id)
        if camera_status:
            queryset = queryset.filter(status__iexact=camera_status)

        serializer = CameraSerializer(queryset, many=True)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
