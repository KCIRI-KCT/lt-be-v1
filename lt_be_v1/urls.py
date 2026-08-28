from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # OpenAPI Schema & Swagger Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Realtime / Application Log Routes
    path('api/logs/', include('apps.logs.urls')),

    # Application API Routes (v1 canonical + legacy /api/ prefix support)
    path('api/', include('LT_AMS_API.urls')),
    path('api/', include('LT_AMS_API.urls')),
]

