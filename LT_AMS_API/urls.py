from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

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
    # Health Check
    path('health/', views.health_check, name='api_health_check'),

    # v1 API Services
    path('v1/', include('LT_AMS_API.v1_urls')),

    # Authentication Endpoints
    path('auth/register/', views.RegisterAPIView.as_view(), name='auth_register'),
    path('auth/login/', views.LoginAPIView.as_view(), name='auth_login'),
    path('auth/request-otp/', views.RequestOTPAPIView.as_view(), name='auth_request_otp'),
    path('auth/forgot-password/', views.ForgotPasswordAPIView.as_view(), name='auth_forgot_password'),
    path('auth/forgot-username/', views.ForgotUsernameAPIView.as_view(), name='auth_forgot_username'),
    path('auth/profile/', views.UserProfileAPIView.as_view(), name='auth_profile'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Resource ViewSet Router
    path('', include(router.urls)),
]


