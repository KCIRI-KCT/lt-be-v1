from django.contrib import admin
from .models import (
    Organization, Role, Employee, ApplicationUser, OTPRecord,
    Country, State, City, Project, Site, Chainage, Worker, Attendance,
    Camera, AIAlert, PPEAcknowledgement, PPENotification, Incident, Message, Report
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('organization_id', 'organization_code', 'organization_name', 'status', 'created_at')
    search_fields = ('organization_code', 'organization_name')
    list_filter = ('status',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_id', 'role_name', 'role_description', 'status')
    search_fields = ('role_name',)
    list_filter = ('status',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'employee_code', 'employee_name', 'department', 'designation', 'email', 'mobile_number', 'city', 'state', 'country', 'status')
    search_fields = ('employee_code', 'employee_name', 'email', 'mobile_number', 'department', 'address', 'city', 'state', 'country', 'pincode')
    list_filter = ('status', 'department', 'organization_id')
    ordering = ('-created_at',)


@admin.register(ApplicationUser)
class ApplicationUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'employee', 'role_id', 'account_status', 'is_active', 'is_staff', 'last_login')
    search_fields = ('username', 'employee__employee_code', 'employee__employee_name')
    list_filter = ('account_status', 'role_id')
    ordering = ('-user_id',)


@admin.register(OTPRecord)
class OTPRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'identifier', 'otp_code', 'purpose', 'is_used', 'expires_at', 'created_at')
    search_fields = ('identifier', 'otp_code')
    list_filter = ('purpose', 'is_used')
    ordering = ('-created_at',)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('country_id', 'name', 'code', 'status', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('status',)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('state_id', 'name', 'code', 'country', 'status', 'created_at')
    search_fields = ('name', 'code', 'country__name')
    list_filter = ('status',)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('city_id', 'name', 'state', 'status', 'created_at')
    search_fields = ('name', 'state__name')
    list_filter = ('status',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_id', 'code', 'name', 'city', 'status', 'progress', 'created_at')
    search_fields = ('code', 'name')
    list_filter = ('status',)


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('site_id', 'code', 'name', 'project', 'status', 'worker_count', 'safety_score', 'created_at')
    search_fields = ('code', 'name', 'project__name')
    list_filter = ('status',)


@admin.register(Chainage)
class ChainageAdmin(admin.ModelAdmin):
    list_display = ('chainage_id', 'name', 'site', 'km_marker', 'status', 'progress', 'safety_score')
    search_fields = ('name', 'km_marker', 'site__name')
    list_filter = ('status',)


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('worker_id', 'employee_id', 'name', 'designation', 'department', 'site', 'status')
    search_fields = ('employee_id', 'name', 'designation', 'department')
    list_filter = ('status', 'department')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('attendance_id', 'worker', 'site', 'date', 'check_in', 'check_out', 'status')
    search_fields = ('worker__name', 'site__name')
    list_filter = ('status', 'date')


@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ('camera_id', 'name', 'site', 'type', 'status', 'health_score')
    search_fields = ('name', 'site__name', 'rtsp_url')
    list_filter = ('status', 'type')


@admin.register(AIAlert)
class AIAlertAdmin(admin.ModelAdmin):
    list_display = ('alert_id', 'type', 'severity', 'site', 'camera', 'status', 'timestamp')
    search_fields = ('type', 'site__name', 'camera__name')
    list_filter = ('severity', 'status', 'type')


@admin.register(PPEAcknowledgement)
class PPEAcknowledgementAdmin(admin.ModelAdmin):
    list_display = ('acknowledgement_id', 'alert', 'acknowledged_by', 'acknowledged_by_role', 'timestamp')
    search_fields = ('acknowledged_by__username', 'notes')


@admin.register(PPENotification)
class PPENotificationAdmin(admin.ModelAdmin):
    list_display = ('notification_id', 'alert', 'safety_officer', 'status', 'created_at')
    search_fields = ('safety_officer__employee_name',)
    list_filter = ('status',)


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('incident_id', 'title', 'type', 'severity', 'site', 'status', 'reported_by', 'assigned_to')
    search_fields = ('title', 'description', 'site__name')
    list_filter = ('severity', 'status', 'type')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('message_id', 'sender', 'receiver', 'subject', 'priority', 'is_read', 'timestamp')
    search_fields = ('subject', 'content', 'sender__username', 'receiver__username')
    list_filter = ('priority', 'is_read')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'title', 'report_type', 'generated_by', 'site', 'format', 'status')
    search_fields = ('title', 'report_type', 'generated_by__username')
    list_filter = ('report_type', 'format', 'status')

