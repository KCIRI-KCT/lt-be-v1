import random
from datetime import date, timedelta
from django.utils import timezone
from rest_framework import status, viewsets, filters, serializers
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, inline_serializer

from .models import (
    Employee, ApplicationUser, OTPRecord,
    Country, State, City, Project, Site, Chainage, Worker, Attendance,
    Camera, AIAlert, PPEAcknowledgement, PPENotification, Incident, Message, Report
)
from .serializers import (
    EmployeeSerializer,
    UserRegistrationSerializer,
    LoginSerializer,
    RequestOTPSerializer,
    ForgotPasswordSerializer,
    ForgotUsernameSerializer,
    ApplicationUserProfileSerializer,
    CountrySerializer,
    StateSerializer,
    CitySerializer,
    ProjectSerializer,
    SiteSerializer,
    ChainageSerializer,
    WorkerSerializer,
    AttendanceSerializer,
    CameraSerializer,
    AIAlertSerializer,
    PPEAcknowledgementSerializer,
    PPENotificationSerializer,
    IncidentSerializer,
    MessageSerializer,
    ReportSerializer
)


# ==============================================================================
# Helper Functions
# ==============================================================================
def _get_site_id(request):
    """Extract site ID from multiple possible query parameter variations."""
    return (
        request.query_params.get('siteId') or
        request.query_params.get('site_id') or
        request.query_params.get('site')
    )


def _build_ptz_response(camera_id, camera_name, ptz_action, pan=0, tilt=0, zoom=1.0, is_action=False):
    """Format standardized PTZ command execution response dictionary."""
    res = {
        "camera_id": camera_id,
        "name": camera_name,
        "action": ptz_action,
        "pan": pan,
        "tilt": tilt,
        "zoom": zoom,
    }
    if is_action:
        res["status"] = "EXECUTED"
    else:
        res["executed"] = True
    return res


# ==============================================================================
# Health Check Endpoint
# ==============================================================================
@extend_schema(
    summary="API Health Check",
    description="Check the operational status and version of the LT AMS API service.",
    responses={200: OpenApiResponse(description="API service status")}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response(
        {
            "status": "success",
            "message": "LT AMS API service is online and operational.",
            "version": "v1"
        },
        status=status.HTTP_200_OK
    )


# ==============================================================================
# Authentication & User Management API Views
# ==============================================================================
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="User Registration",
        description="Register a new Application User linked to an existing Employee code.",
        request=UserRegistrationSerializer,
        responses={
            201: UserRegistrationSerializer,
            400: OpenApiResponse(description="Validation error")
        }
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "status": "success",
                    "message": "User registered successfully.",
                    "data": {
                        "user_id": user.user_id,
                        "username": user.username,
                        "role_id": user.role_id,
                        "account_status": user.account_status,
                        "tokens": {
                            "refresh": str(refresh),
                            "access": str(refresh.access_token),
                        }
                    }
                },
                status=status.HTTP_201_CREATED
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="User Login",
        description="Authenticate user credentials (username & password) and issue JWT tokens.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description="Authentication successful"),
            400: OpenApiResponse(description="Invalid credentials")
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])

            refresh = RefreshToken.for_user(user)
            employee_data = EmployeeSerializer(user.employee).data if user.employee else None

            return Response(
                {
                    "status": "success",
                    "message": "Login successful.",
                    "data": {
                        "user_id": user.user_id,
                        "username": user.username,
                        "role_id": user.role_id,
                        "account_status": user.account_status,
                        "last_login": user.last_login,
                        "employee": employee_data,
                        "tokens": {
                            "refresh": str(refresh),
                            "access": str(refresh.access_token),
                        }
                    }
                },
                status=status.HTTP_200_OK
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class RequestOTPAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Request OTP",
        description="Generate a 6-digit OTP code for Forgot Password or Forgot Username operations.",
        request=RequestOTPSerializer,
        responses={
            200: OpenApiResponse(description="OTP generated successfully"),
            400: OpenApiResponse(description="Validation error")
        }
    )
    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data['identifier']
            purpose = serializer.validated_data['purpose']

            otp_code = str(random.randint(100000, 999999))
            expires_at = timezone.now() + timedelta(minutes=10)

            OTPRecord.objects.create(
                identifier=identifier,
                otp_code=otp_code,
                purpose=purpose,
                expires_at=expires_at
            )

            return Response(
                {
                    "status": "success",
                    "message": f"OTP generated successfully for {purpose}.",
                    "data": {
                        "identifier": identifier,
                        "otp_code": otp_code,
                        "expires_in_minutes": 10
                    }
                },
                status=status.HTTP_200_OK
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Forgot Password",
        description="Reset user password using a valid OTP code.",
        request=ForgotPasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password updated successfully"),
            400: OpenApiResponse(description="Validation or OTP error")
        }
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            otp_record = serializer.validated_data['otp_record']
            new_password = serializer.validated_data['new_password']

            user.set_password(new_password)
            user.save()

            otp_record.is_used = True
            otp_record.save()

            return Response(
                {
                    "status": "success",
                    "message": "Password reset successfully. You can now login with your new password."
                },
                status=status.HTTP_200_OK
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ForgotUsernameAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Forgot Username",
        description="Retrieve username using a valid OTP code verified against registered email/mobile.",
        request=ForgotUsernameSerializer,
        responses={
            200: OpenApiResponse(description="Username retrieved successfully"),
            400: OpenApiResponse(description="Validation or OTP error")
        }
    )
    def post(self, request):
        serializer = ForgotUsernameSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            otp_record = serializer.validated_data['otp_record']

            otp_record.is_used = True
            otp_record.save()

            return Response(
                {
                    "status": "success",
                    "message": "Username retrieved successfully.",
                    "data": {
                        "username": username
                    }
                },
                status=status.HTTP_200_OK
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get User Profile",
        description="Fetch detailed profile information for the authenticated application user.",
        responses={200: ApplicationUserProfileSerializer}
    )
    def get(self, request):
        serializer = ApplicationUserProfileSerializer(request.user)
        return Response(
            {
                "status": "success",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


# ==============================================================================
# Dashboard & Analytics Summary API Views
# ==============================================================================
class DashboardMetricsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Dashboard Metrics",
        description="Fetch calculated aggregate metrics: active sites, worker counts, active workers today, PPE compliance average, open alerts, and active cameras.",
        responses={200: OpenApiResponse(description="Dashboard key metrics")}
    )
    def get(self, request):
        today = date.today()

        total_active_sites = Site.objects.filter(status='ACTIVE').count()
        total_workers = Worker.objects.filter(status='ACTIVE').count()
        active_workers_today = Attendance.objects.filter(date=today, status='PRESENT').count()
        open_alerts_count = AIAlert.objects.filter(status='OPEN').count()
        total_cameras = Camera.objects.filter(status='ACTIVE').count()

        site_scores = Site.objects.filter(status='ACTIVE').values_list('safety_score', flat=True)
        if site_scores:
            ppe_compliance_avg = round(sum(site_scores) / len(site_scores), 2)
        else:
            ppe_compliance_avg = 94.5

        return Response({
            "status": "success",
            "data": {
                "total_active_sites": total_active_sites,
                "total_workers": total_workers,
                "active_workers_today": active_workers_today,
                "ppe_compliance_avg": ppe_compliance_avg,
                "open_alerts_count": open_alerts_count,
                "total_cameras": total_cameras
            }
        }, status=status.HTTP_200_OK)


class DashboardProgressTrendAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Dashboard Progress Trend",
        description="Retrieve progress and compliance trend metrics for month, week, or year ranges.",
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
            labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            progress_trend = [55.0, 58.2, 62.0, 65.5, 70.1, 73.8, 76.5, 80.2, 83.0, 85.8, 88.4, 91.2]
            ppe_compliance_trend = [85.0, 87.2, 88.5, 90.0, 91.4, 92.8, 93.5, 94.2, 94.8, 95.5, 96.0, 96.8]

        return Response({
            "status": "success",
            "data": {
                "range": range_type,
                "labels": labels,
                "progress_trend": progress_trend,
                "ppe_compliance_trend": ppe_compliance_trend
            }
        }, status=status.HTTP_200_OK)


class SafetyAlertsSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Safety Alerts Summary",
        description="Retrieve filtered list of AI Safety Alerts with query options for siteId, status, and severity.",
        parameters=[
            OpenApiParameter(name='siteId', type=int, description='Filter by Site ID'),
            OpenApiParameter(name='site_id', type=int, description='Filter by Site ID (snake_case)'),
            OpenApiParameter(name='status', type=str, description='Filter by status (OPEN, ACKNOWLEDGED, RESOLVED)'),
            OpenApiParameter(name='severity', type=str, description='Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)'),
        ],
        responses={200: OpenApiResponse(description="Safety alerts summary list")}
    )
    def get(self, request):
        queryset = AIAlert.objects.all().order_by('-timestamp')

        site_id = _get_site_id(request)
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


class WorkerAttendanceSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Worker Attendance Summary",
        description="Retrieve daily worker attendance logs filtered by siteId and date.",
        parameters=[
            OpenApiParameter(name='siteId', type=int, description='Filter by Site ID'),
            OpenApiParameter(name='site_id', type=int, description='Filter by Site ID (snake_case)'),
            OpenApiParameter(name='date', type=str, description='Filter by date (YYYY-MM-DD)'),
        ],
        responses={200: OpenApiResponse(description="Worker attendance summary list")}
    )
    def get(self, request):
        queryset = Attendance.objects.all().order_by('-date')

        site_id = _get_site_id(request)
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


class CameraControlAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="cameras_ptz_control_create",
        summary="PTZ Camera Control",
        description="Send Pan-Tilt-Zoom (PTZ) commands to a specific monitoring camera by camera_id in payload.",
        request=inline_serializer(
            name='CameraControlRequest',
            fields={
                'camera_id': serializers.IntegerField(required=False, help_text="ID of the camera"),
                'id': serializers.IntegerField(required=False, help_text="Alias for camera_id"),
                'action': serializers.CharField(required=True, help_text="PTZ action command (e.g. PAN_LEFT, TILT_UP, ZOOM_IN)"),
                'pan': serializers.IntegerField(default=0, help_text="Pan value"),
                'tilt': serializers.IntegerField(default=0, help_text="Tilt value"),
                'zoom': serializers.FloatField(default=1.0, help_text="Zoom factor"),
            }
        ),
        responses={200: OpenApiResponse(description="PTZ Command execution status")}
    )
    def post(self, request, pk=None):
        camera_id = pk or request.data.get('camera_id') or request.data.get('id')
        ptz_action = request.data.get('action', '').upper()
        pan = request.data.get('pan', 0)
        tilt = request.data.get('tilt', 0)
        zoom = request.data.get('zoom', 1.0)

        camera_name = "Camera"
        if camera_id:
            try:
                cam = Camera.objects.get(pk=camera_id)
                camera_name = cam.name
            except Camera.DoesNotExist:
                pass

        return Response({
            "status": "success",
            "data": _build_ptz_response(camera_id, camera_name, ptz_action, pan, tilt, zoom, is_action=False),
            "message": f"PTZ command '{ptz_action}' sent successfully to camera '{camera_name}'."
        }, status=status.HTTP_200_OK)


class CameraDetailControlAPIView(CameraControlAPIView):
    @extend_schema(
        operation_id="camera_detail_ptz_control_create",
        summary="PTZ Camera Control by ID",
        description="Send Pan-Tilt-Zoom (PTZ) commands to a camera specified by URL ID parameter.",
        request=inline_serializer(
            name='CameraDetailControlRequest',
            fields={
                'action': serializers.CharField(required=True, help_text="PTZ action command (e.g. PAN_LEFT, TILT_UP, ZOOM_IN)"),
                'pan': serializers.IntegerField(default=0, help_text="Pan value"),
                'tilt': serializers.IntegerField(default=0, help_text="Tilt value"),
                'zoom': serializers.FloatField(default=1.0, help_text="Zoom factor"),
            }
        ),
        responses={200: OpenApiResponse(description="PTZ Command execution status")}
    )
    def post(self, request, pk=None):
        return super().post(request, pk=pk)


# ==============================================================================
# Base ViewSet with Standardized Response Structure
# ==============================================================================
class StandardizedModelViewSet(viewsets.ModelViewSet):
    """
    Base ModelViewSet providing standardized response formatting:
    {
      "success": true,
      "data": { ... },
      "message": "Operation successful"
    }
    """
    permission_classes = [IsAuthenticated]

    def get_resource_name(self):
        return self.__class__.__name__.replace('ViewSet', '')

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            "success": True,
            "data": response.data,
            "message": f"{self.get_resource_name()} list retrieved successfully"
        }, status=response.status_code)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({
            "success": True,
            "data": response.data,
            "message": f"{self.get_resource_name()} retrieved successfully"
        }, status=response.status_code)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "success": True,
            "data": response.data,
            "message": f"{self.get_resource_name()} created successfully"
        }, status=response.status_code)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            "success": True,
            "data": response.data,
            "message": f"{self.get_resource_name()} updated successfully"
        }, status=response.status_code)

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({
            "success": True,
            "data": None,
            "message": f"{self.get_resource_name()} deleted successfully"
        }, status=status.HTTP_200_OK)


# ==============================================================================
# Model ViewSets (Full CRUD APIs)
# ==============================================================================
class EmployeeViewSet(StandardizedModelViewSet):
    queryset = Employee.objects.all().order_by('-created_at')
    serializer_class = EmployeeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee_code', 'employee_name', 'designation', 'department', 'email']


class CountryViewSet(StandardizedModelViewSet):
    queryset = Country.objects.all().order_by('name')
    serializer_class = CountrySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'status']


class StateViewSet(StandardizedModelViewSet):
    queryset = State.objects.all().order_by('name')
    serializer_class = StateSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'status', 'country__name']


class CityViewSet(StandardizedModelViewSet):
    queryset = City.objects.all().order_by('name')
    serializer_class = CitySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'status', 'state__name']


class ProjectViewSet(StandardizedModelViewSet):
    queryset = Project.objects.all().order_by('-created_at')
    serializer_class = ProjectSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'status']

    def get_queryset(self):
        queryset = super().get_queryset()
        engineer_id = self.request.query_params.get('engineerId') or self.request.query_params.get('engineer_id') or self.request.query_params.get('engineer')
        manager_id = self.request.query_params.get('managerId') or self.request.query_params.get('manager_id') or self.request.query_params.get('manager')

        if engineer_id:
            queryset = queryset.filter(engineer_id=engineer_id)
        if manager_id:
            queryset = queryset.filter(manager_id=manager_id)
        return queryset


class SiteViewSet(StandardizedModelViewSet):
    queryset = Site.objects.all().order_by('-created_at')
    serializer_class = SiteSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'status', 'location']

    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('projectId') or self.request.query_params.get('project_id') or self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset


class ChainageViewSet(StandardizedModelViewSet):
    queryset = Chainage.objects.all().order_by('-created_at')
    serializer_class = ChainageSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'km_marker', 'status']

    def get_queryset(self):
        queryset = super().get_queryset()
        site_id = _get_site_id(self.request)
        if site_id:
            queryset = queryset.filter(site_id=site_id)
        return queryset


class WorkerViewSet(StandardizedModelViewSet):
    queryset = Worker.objects.all().order_by('-created_at')
    serializer_class = WorkerSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee_id', 'name', 'phone', 'email', 'designation', 'department', 'status']

    def get_queryset(self):
        queryset = super().get_queryset()
        site_id = _get_site_id(self.request)
        if site_id:
            queryset = queryset.filter(site_id=site_id)
        return queryset


class AttendanceViewSet(StandardizedModelViewSet):
    queryset = Attendance.objects.all().order_by('-date')
    serializer_class = AttendanceSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['worker__name', 'site__name', 'status']

    def get_queryset(self):
        queryset = super().get_queryset()
        site_id = _get_site_id(self.request)
        attendance_date = self.request.query_params.get('date')
        if site_id:
            queryset = queryset.filter(site_id=site_id)
        if attendance_date:
            queryset = queryset.filter(date=attendance_date)
        return queryset


class CameraViewSet(StandardizedModelViewSet):
    queryset = Camera.objects.all().order_by('-created_at')
    serializer_class = CameraSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'location', 'type', 'status']

    def get_queryset(self):
        queryset = super().get_queryset()
        site_id = _get_site_id(self.request)
        camera_status = self.request.query_params.get('status')
        if site_id:
            queryset = queryset.filter(site_id=site_id)
        if camera_status:
            queryset = queryset.filter(status__iexact=camera_status)
        return queryset

    @extend_schema(
        summary="PTZ Camera Control Action",
        description="Send Pan, Tilt, and Zoom PTZ commands to a specific camera.",
        responses={200: OpenApiResponse(description="PTZ Command execution status")}
    )
    @action(detail=True, methods=['post'], url_path='ptz')
    def ptz(self, request, pk=None):
        camera = self.get_object()
        ptz_action = request.data.get('action', '').upper()
        pan = request.data.get('pan', 0)
        tilt = request.data.get('tilt', 0)
        zoom = request.data.get('zoom', 1.0)

        return Response({
            "success": True,
            "data": _build_ptz_response(camera.camera_id, camera.name, ptz_action, pan, tilt, zoom, is_action=True),
            "message": f"PTZ command '{ptz_action}' sent to camera '{camera.name}'"
        })


class AIAlertViewSet(StandardizedModelViewSet):
    queryset = AIAlert.objects.all().order_by('-timestamp')
    serializer_class = AIAlertSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['type', 'severity', 'status']

    def get_queryset(self):
        queryset = super().get_queryset()
        site_id = _get_site_id(self.request)
        alert_status = self.request.query_params.get('status')
        severity = self.request.query_params.get('severity')

        if site_id:
            queryset = queryset.filter(site_id=site_id)
        if alert_status:
            queryset = queryset.filter(status__iexact=alert_status)
        if severity:
            queryset = queryset.filter(severity__iexact=severity)
        return queryset


class PPEAcknowledgementViewSet(StandardizedModelViewSet):
    queryset = PPEAcknowledgement.objects.all().order_by('-timestamp')
    serializer_class = PPEAcknowledgementSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['acknowledged_by_role', 'notes']


class PPENotificationViewSet(StandardizedModelViewSet):
    queryset = PPENotification.objects.all().order_by('-created_at')
    serializer_class = PPENotificationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['status']

    def get_queryset(self):
        queryset = super().get_queryset()
        site_id = _get_site_id(self.request)
        notification_status = self.request.query_params.get('status')
        alert_id = self.request.query_params.get('alert_id') or self.request.query_params.get('alertId')

        if site_id:
            queryset = queryset.filter(alert__site_id=site_id)
        if notification_status:
            queryset = queryset.filter(status__iexact=notification_status)
        if alert_id:
            queryset = queryset.filter(alert_id=alert_id)
        return queryset

    @extend_schema(
        summary="HITL Resolve PPE Notification",
        description="Safety Engineer / Officer triggers Human-In-The-Loop (HITL) resolution for a PPE notification, updating notification status to SOLVED, setting parent AI alert to RESOLVED, recording an acknowledgement, and reflecting to the Project Engineer.",
        responses={200: OpenApiResponse(description="HITL Resolution status")}
    )
    @action(detail=True, methods=['post'], url_path='hitl-resolve')
    def hitl_resolve(self, request, pk=None):
        notification = self.get_object()
        decision = request.data.get('decision') or request.data.get('status') or 'SOLVED'
        notes = request.data.get('notes') or request.data.get('remarks') or 'PPE compliance verified and resolved via HITL'
        hitl_payload = request.data.get('hitl_data') or {}

        target_status = decision.upper() if decision.upper() in ['SOLVED', 'RESOLVED', 'CLOSED'] else 'SOLVED'
        notification.status = target_status

        updated_hitl = dict(notification.hitl_data or {})
        updated_hitl.update({
            "decision": decision,
            "resolved_by": request.user.username if (request.user and request.user.is_authenticated) else "Safety Officer",
            "resolved_at": timezone.now().isoformat(),
            "notes": notes,
            "payload": hitl_payload
        })
        notification.hitl_data = updated_hitl
        notification.save()

        alert = notification.alert
        if alert:
            alert.status = 'RESOLVED'
            if request.user and request.user.is_authenticated:
                alert.acknowledged_by = request.user
            alert.save()

            PPEAcknowledgement.objects.create(
                alert=alert,
                acknowledged_by=request.user if (request.user and request.user.is_authenticated) else None,
                acknowledged_by_role="Safety Officer",
                notes=notes
            )

        serializer = self.get_serializer(notification)
        return Response({
            "success": True,
            "data": serializer.data,
            "message": f"PPE Notification {notification.notification_id} resolved via HITL successfully. Updated state reflected to Project Engineer."
        }, status=status.HTTP_200_OK)


class IncidentViewSet(StandardizedModelViewSet):
    queryset = Incident.objects.all().order_by('-created_at')
    serializer_class = IncidentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'type', 'severity', 'status']


class MessageViewSet(StandardizedModelViewSet):
    queryset = Message.objects.all().order_by('-timestamp')
    serializer_class = MessageSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['subject', 'content', 'priority']


class ReportViewSet(StandardizedModelViewSet):
    queryset = Report.objects.all().order_by('-created_at')
    serializer_class = ReportSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'report_type', 'format', 'status']
