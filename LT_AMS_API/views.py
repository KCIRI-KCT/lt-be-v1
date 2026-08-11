import random
from datetime import timedelta
from django.utils import timezone
from rest_framework import status, viewsets, filters
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import (
    Organization, Role, Employee, ApplicationUser, OTPRecord,
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



@extend_schema(
    summary="API Health Check",
    description="Check the status and version of the API service.",
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
        description="Authenticate user with username and password, returning JWT access and refresh tokens.",
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

            # Generate 6-digit OTP
            otp_code = str(random.randint(100000, 999999))
            expires_at = timezone.now() + timedelta(minutes=10)

            OTPRecord.objects.create(
                identifier=identifier,
                otp_code=otp_code,
                purpose=purpose,
                expires_at=expires_at
            )

            # In production, send via Email/SMS service here.
            return Response(
                {
                    "status": "success",
                    "message": f"OTP generated successfully for {purpose}.",
                    "data": {
                        "identifier": identifier,
                        "otp_code": otp_code,  # Provided for testing/development
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
        description="Reset user password using valid OTP code.",
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
        description="Retrieve username using valid OTP code verified against registered email/mobile.",
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
        description="Fetch detailed profile information for the authenticated user.",
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
    permission_classes = [AllowAny]

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


class EmployeeViewSet(StandardizedModelViewSet):
    """
    ViewSet for managing Employee data.
    Provides list, create, retrieve, update, and destroy actions.
    """
    queryset = Employee.objects.all().order_by('-created_at')
    serializer_class = EmployeeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee_code', 'employee_name', 'designation', 'department', 'email']


# ==============================================================================
# Location ViewSets
# ==============================================================================
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


# ==============================================================================
# Project & Site Hierarchy ViewSets
# ==============================================================================
class ProjectViewSet(StandardizedModelViewSet):
    queryset = Project.objects.all().order_by('-created_at')
    serializer_class = ProjectSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'status']


class SiteViewSet(StandardizedModelViewSet):
    queryset = Site.objects.all().order_by('-created_at')
    serializer_class = SiteSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'status', 'location']


class ChainageViewSet(StandardizedModelViewSet):
    queryset = Chainage.objects.all().order_by('-created_at')
    serializer_class = ChainageSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'km_marker', 'status']


# ==============================================================================
# Workforce ViewSets
# ==============================================================================
class WorkerViewSet(StandardizedModelViewSet):
    queryset = Worker.objects.all().order_by('-created_at')
    serializer_class = WorkerSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee_id', 'name', 'phone', 'email', 'designation', 'department', 'status']


class AttendanceViewSet(StandardizedModelViewSet):
    queryset = Attendance.objects.all().order_by('-date')
    serializer_class = AttendanceSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['worker__name', 'site__name', 'status']


# ==============================================================================
# Camera & AI Monitoring ViewSets
# ==============================================================================
class CameraViewSet(StandardizedModelViewSet):
    queryset = Camera.objects.all().order_by('-created_at')
    serializer_class = CameraSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'location', 'type', 'status']


class AIAlertViewSet(StandardizedModelViewSet):
    queryset = AIAlert.objects.all().order_by('-timestamp')
    serializer_class = AIAlertSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['type', 'severity', 'status']


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


# ==============================================================================
# Operations & Communication ViewSets
# ==============================================================================
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

