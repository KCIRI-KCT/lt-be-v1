from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register(r'employees', views.EmployeeViewSet, basename='employee')
router.register(r'countries', views.CountryViewSet, basename='country')
router.register(r'states', views.StateViewSet, basename='state')
router.register(r'cities', views.CityViewSet, basename='city')
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'sites', views.SiteViewSet, basename='site')
router.register(r'chainages', views.ChainageViewSet, basename='chainage')
router.register(r'workers', views.WorkerViewSet, basename='worker')
router.register(r'attendances', views.AttendanceViewSet, basename='attendance')
router.register(r'cameras', views.CameraViewSet, basename='camera')
router.register(r'ai-alerts', views.AIAlertViewSet, basename='aialert')
router.register(r'ppe-acknowledgements', views.PPEAcknowledgementViewSet, basename='ppeacknowledgement')
router.register(r'ppe-notifications', views.PPENotificationViewSet, basename='ppenotification')
router.register(r'incidents', views.IncidentViewSet, basename='incident')
router.register(r'messages', views.MessageViewSet, basename='message')
router.register(r'reports', views.ReportViewSet, basename='report')

urlpatterns = [
    # Health Check Endpoint
    path('health/', views.health_check, name='api_health_check'),

    # Authentication & User Management Endpoints
    path('auth/register/', views.RegisterAPIView.as_view(), name='auth_register'),
    path('auth/login/', views.LoginAPIView.as_view(), name='auth_login'),
    path('auth/token/', views.CustomTokenObtainPairView.as_view(), name='auth_token_obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/', views.CustomTokenObtainPairView.as_view(), name='api_token_obtain_direct'),
    path('token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh_direct'),
    path('auth/request-otp/', views.RequestOTPAPIView.as_view(), name='auth_request_otp'),
    path('auth/forgot-password/', views.ForgotPasswordAPIView.as_view(), name='auth_forgot_password'),
    path('auth/forgot-username/', views.ForgotUsernameAPIView.as_view(), name='auth_forgot_username'),
    path('auth/profile/', views.UserProfileAPIView.as_view(), name='auth_profile'),

    # Dashboard & Analytics Summary Endpoints
    path('dashboard/metrics/', views.DashboardMetricsAPIView.as_view(), name='dashboard_metrics'),
    path('dashboard/progress-trend/', views.DashboardProgressTrendAPIView.as_view(), name='dashboard_progress_trend'),
    path('safety/alerts-summary/', views.SafetyAlertsSummaryAPIView.as_view(), name='safety_alerts_summary'),
    path('workers/attendance-summary/', views.WorkerAttendanceSummaryAPIView.as_view(), name='worker_attendance_summary'),
    path('cameras/ptz-control/', views.CameraControlAPIView.as_view(), name='cameras_ptz_control'),
    path('cameras/<int:pk>/ptz-control/', views.CameraDetailControlAPIView.as_view(), name='camera_detail_ptz_control'),

    # Resource ViewSets Router (Full CRUD endpoints)
    path('', include(router.urls)),
]
