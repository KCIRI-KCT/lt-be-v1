from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import datetime


class Organization(models.Model):
    """
    Organization Model representing table 'organization'.
    """
    organization_id = models.BigAutoField(primary_key=True, db_column='organization_id')
    organization_code = models.CharField(max_length=50, unique=True, db_column='organization_code')
    organization_name = models.CharField(max_length=255, db_column='organization_name')
    organization_type = models.CharField(max_length=100, null=True, blank=True, db_column='organization_type')
    address = models.TextField(null=True, blank=True, db_column='address')
    city = models.CharField(max_length=100, null=True, blank=True, db_column='city')
    state = models.CharField(max_length=100, null=True, blank=True, db_column='state')
    country = models.CharField(max_length=100, null=True, blank=True, db_column='country')
    contact_person = models.CharField(max_length=255, null=True, blank=True, db_column='contact_person')
    contact_email = models.CharField(max_length=255, null=True, blank=True, db_column='contact_email')
    contact_phone = models.CharField(max_length=50, null=True, blank=True, db_column='contact_phone')
    status = models.CharField(max_length=20, default='ACTIVE', db_column='status')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'organization'
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def __str__(self):
        return f"{self.organization_code} - {self.organization_name}"


class Role(models.Model):
    """
    Role Model representing table 'role'.
    """
    role_id = models.BigAutoField(primary_key=True, db_column='role_id')
    role_name = models.CharField(max_length=100, db_column='role_name')
    role_description = models.TextField(null=True, blank=True, db_column='role_description')
    status = models.CharField(max_length=20, default='ACTIVE', db_column='status')

    class Meta:
        db_table = 'role'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return f"{self.role_id} - {self.role_name}"


class Employee(models.Model):


    """
    Employee Model representing table 'employee'.
    Stores data of all employees.
    """
    employee_id = models.BigAutoField(primary_key=True, db_column='employee_id')
    organization_id = models.BigIntegerField(db_column='organization_id', default=1)
    employee_code = models.CharField(max_length=50, unique=True, db_column='employee_code')
    employee_name = models.CharField(max_length=255, db_column='employee_name')
    designation = models.CharField(max_length=100, db_column='designation')
    department = models.CharField(max_length=100, db_column='department')
    email = models.EmailField(max_length=255, unique=True, db_column='email')
    mobile_number = models.CharField(max_length=20, unique=True, db_column='mobile_number')
    status = models.CharField(max_length=20, default='ACTIVE', db_column='status')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'employee'
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'

    def __str__(self):
        return f"{self.employee_code} - {self.employee_name}"


class ApplicationUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        username = self.model.normalize_username(username)

        # Filter out fields that do not exist as table columns in PostgreSQL application_user
        valid_fields = {'employee', 'employee_id', 'role_id', 'last_login', 'account_status'}
        filtered_fields = {k: v for k, v in extra_fields.items() if k in valid_fields}

        user = self.model(username=username, **filtered_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('role_id', 1)
        extra_fields.setdefault('account_status', 'ACTIVE')
        return self.create_user(username, password, **extra_fields)


class ApplicationUser(AbstractBaseUser):
    """
    Application User Model representing table 'application_user'.
    Matches PostgreSQL schema columns: user_id, employee_id, role_id, username, password_hash, last_login, account_status.
    """
    user_id = models.BigAutoField(primary_key=True, db_column='user_id')
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='application_users',
        db_column='employee_id',
        null=True,
        blank=True
    )
    role_id = models.BigIntegerField(default=1, db_column='role_id')
    username = models.CharField(max_length=150, unique=True, db_column='username')
    password = models.CharField(max_length=128, db_column='password_hash')
    last_login = models.DateTimeField(null=True, blank=True, db_column='last_login')
    account_status = models.CharField(max_length=20, default='ACTIVE', db_column='account_status')

    objects = ApplicationUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'application_user'
        verbose_name = 'Application User'
        verbose_name_plural = 'Application Users'

    @property
    def is_active(self):
        return self.account_status == 'ACTIVE'

    @property
    def is_staff(self):
        return self.account_status == 'ACTIVE'

    @property
    def is_superuser(self):
        return self.role_id == 1

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def __str__(self):
        return f"{self.username} (User ID: {self.user_id})"



class OTPRecord(models.Model):
    """
    OTP Record Model representing table 'otp_record'.
    Used for OTP validation in Forgot Password, Forgot Username, and Request OTP flows.
    """
    PURPOSE_CHOICES = (
        ('FORGOT_PASSWORD', 'Forgot Password'),
        ('FORGOT_USERNAME', 'Forgot Username'),
        ('LOGIN_OTP', 'Login OTP'),
    )

    identifier = models.CharField(max_length=255, db_column='identifier')
    otp_code = models.CharField(max_length=6, db_column='otp_code')
    purpose = models.CharField(max_length=50, choices=PURPOSE_CHOICES, db_column='purpose')
    expires_at = models.DateTimeField(db_column='expires_at')
    is_used = models.BooleanField(default=False, db_column='is_used')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')

    class Meta:
        db_table = 'otp_record'
        verbose_name = 'OTP Record'
        verbose_name_plural = 'OTP Records'

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP for {self.identifier} ({self.purpose})"


# ==============================================================================
# Location Models
# ==============================================================================
class Country(models.Model):
    country_id = models.BigAutoField(primary_key=True, db_column='country_id')
    name = models.CharField(max_length=100, db_column='name')
    code = models.CharField(max_length=10, unique=True, db_column='code')
    status = models.CharField(max_length=20, default='ACTIVE', db_index=True, db_column='status')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'country'
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'

    def __str__(self):
        return f"{self.name} ({self.code})"


class State(models.Model):
    state_id = models.BigAutoField(primary_key=True, db_column='state_id')
    name = models.CharField(max_length=100, db_column='name')
    code = models.CharField(max_length=10, db_column='code')
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states', db_column='country_id')
    status = models.CharField(max_length=20, default='ACTIVE', db_index=True, db_column='status')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'state'
        verbose_name = 'State'
        verbose_name_plural = 'States'

    def __str__(self):
        return f"{self.name} ({self.code})"


class City(models.Model):
    city_id = models.BigAutoField(primary_key=True, db_column='city_id')
    name = models.CharField(max_length=100, db_column='name')
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cities', db_column='state_id')
    status = models.CharField(max_length=20, default='ACTIVE', db_index=True, db_column='status')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'city'
        verbose_name = 'City'
        verbose_name_plural = 'Cities'

    def __str__(self):
        return self.name


# ==============================================================================
# Project & Site Hierarchy
# ==============================================================================
class Project(models.Model):
    project_id = models.BigAutoField(primary_key=True, db_column='project_id')
    name = models.CharField(max_length=255, db_column='name')
    code = models.CharField(max_length=50, unique=True, db_column='code')
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects', db_column='city_id')
    start_date = models.DateField(null=True, blank=True, db_column='start_date')
    end_date = models.DateField(null=True, blank=True, db_column='end_date')
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, db_column='budget')
    status = models.CharField(max_length=50, default='ACTIVE', db_index=True, db_column='status')
    progress = models.FloatField(default=0.0, db_column='progress')
    manager = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_projects', db_column='manager_id')
    supervisor = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_projects', db_column='supervisor_id')
    engineer = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='engineered_projects', db_column='engineer_id')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'project'
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Site(models.Model):
    site_id = models.BigAutoField(primary_key=True, db_column='site_id')
    name = models.CharField(max_length=255, db_column='name')
    code = models.CharField(max_length=50, unique=True, db_column='code')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sites', db_column='project_id')
    location = models.CharField(max_length=255, null=True, blank=True, db_column='location')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, db_column='latitude')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, db_column='longitude')
    status = models.CharField(max_length=50, default='ACTIVE', db_index=True, db_column='status')
    worker_count = models.IntegerField(default=0, db_column='worker_count')
    safety_score = models.FloatField(default=100.0, db_column='safety_score')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'site'
        verbose_name = 'Site'
        verbose_name_plural = 'Sites'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Chainage(models.Model):
    chainage_id = models.BigAutoField(primary_key=True, db_column='chainage_id')
    name = models.CharField(max_length=255, db_column='name')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='chainages', db_column='site_id')
    km_marker = models.CharField(max_length=50, db_column='km_marker')
    status = models.CharField(max_length=50, default='ACTIVE', db_index=True, db_column='status')
    progress = models.FloatField(default=0.0, db_column='progress')
    workers_count = models.IntegerField(default=0, db_column='workers_count')
    temperature = models.FloatField(null=True, blank=True, db_column='temperature')
    safety_score = models.FloatField(default=100.0, db_column='safety_score')
    elevation = models.FloatField(null=True, blank=True, db_column='elevation')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'chainage'
        verbose_name = 'Chainage'
        verbose_name_plural = 'Chainages'

    def __str__(self):
        return f"{self.name} ({self.km_marker})"


# ==============================================================================
# Workforce Models
# ==============================================================================
class Worker(models.Model):
    worker_id = models.BigAutoField(primary_key=True, db_column='worker_id')
    employee_id = models.CharField(max_length=50, unique=True, db_column='employee_id')
    name = models.CharField(max_length=255, db_column='name')
    phone = models.CharField(max_length=20, null=True, blank=True, db_column='phone')
    email = models.EmailField(max_length=255, null=True, blank=True, db_column='email')
    designation = models.CharField(max_length=100, db_column='designation')
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True, related_name='workers', db_column='site_id')
    department = models.CharField(max_length=100, null=True, blank=True, db_column='department')
    status = models.CharField(max_length=20, default='ACTIVE', db_index=True, db_column='status')
    photo = models.TextField(null=True, blank=True, db_column='photo')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'worker'
        verbose_name = 'Worker'
        verbose_name_plural = 'Workers'

    def __str__(self):
        return f"{self.employee_id} - {self.name}"


class Attendance(models.Model):
    attendance_id = models.BigAutoField(primary_key=True, db_column='attendance_id')
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='attendances', db_column='worker_id')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='attendances', db_column='site_id')
    date = models.DateField(default=datetime.date.today, db_column='date')
    check_in = models.DateTimeField(null=True, blank=True, db_column='check_in')
    check_out = models.DateTimeField(null=True, blank=True, db_column='check_out')
    status = models.CharField(max_length=20, default='PRESENT', db_index=True, db_column='status')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'attendance'
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendances'

    def __str__(self):
        return f"Attendance {self.worker} on {self.date}"


# ==============================================================================
# Camera & AI Monitoring Models
# ==============================================================================
class Camera(models.Model):
    camera_id = models.BigAutoField(primary_key=True, db_column='camera_id')
    name = models.CharField(max_length=255, db_column='name')
    rtsp_url = models.CharField(max_length=500, db_column='rtsp_url')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='cameras', db_column='site_id')
    location = models.CharField(max_length=255, null=True, blank=True, db_column='location')
    status = models.CharField(max_length=20, default='ACTIVE', db_index=True, db_column='status')
    type = models.CharField(max_length=50, default='FIXED', db_column='type')
    resolution = models.CharField(max_length=50, default='1080p', db_column='resolution')
    health_score = models.FloatField(default=100.0, db_column='health_score')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'camera'
        verbose_name = 'Camera'
        verbose_name_plural = 'Cameras'

    def __str__(self):
        return f"{self.name} ({self.site.name if self.site else 'No Site'})"


class AIAlert(models.Model):
    alert_id = models.BigAutoField(primary_key=True, db_column='alert_id')
    camera = models.ForeignKey(Camera, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_alerts', db_column='camera_id')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='ai_alerts', db_column='site_id')
    type = models.CharField(max_length=100, db_index=True, db_column='type')
    severity = models.CharField(max_length=20, default='MEDIUM', db_column='severity')
    timestamp = models.DateTimeField(default=timezone.now, db_column='timestamp')
    snapshot = models.TextField(null=True, blank=True, db_column='snapshot')
    status = models.CharField(max_length=50, default='OPEN', db_index=True, db_column='status')
    acknowledged_by = models.ForeignKey(ApplicationUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts', db_column='acknowledged_by')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'ai_alert'
        verbose_name = 'AI Alert'
        verbose_name_plural = 'AI Alerts'

    def __str__(self):
        return f"{self.type} [{self.severity}] - Alert {self.alert_id}"


class PPEAcknowledgement(models.Model):
    acknowledgement_id = models.BigAutoField(primary_key=True, db_column='acknowledgement_id')
    alert = models.ForeignKey(AIAlert, on_delete=models.CASCADE, related_name='acknowledgements', db_column='alert_id')
    acknowledged_by = models.ForeignKey(ApplicationUser, on_delete=models.CASCADE, related_name='ppe_acknowledgements', db_column='acknowledged_by')
    acknowledged_by_role = models.CharField(max_length=100, null=True, blank=True, db_column='acknowledged_by_role')
    notes = models.TextField(null=True, blank=True, db_column='notes')
    timestamp = models.DateTimeField(default=timezone.now, db_column='timestamp')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'ppe_acknowledgement'
        verbose_name = 'PPE Acknowledgement'
        verbose_name_plural = 'PPE Acknowledgements'

    def __str__(self):
        return f"Acknowledgement for Alert {self.alert_id}"


class PPENotification(models.Model):
    notification_id = models.BigAutoField(primary_key=True, db_column='notification_id')
    alert = models.ForeignKey(AIAlert, on_delete=models.CASCADE, related_name='notifications', db_column='alert_id')
    safety_officer = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='ppe_notifications', db_column='safety_officer_id')
    status = models.CharField(max_length=50, default='pending_review', db_index=True, db_column='status')
    hitl_data = models.JSONField(default=dict, blank=True, db_column='hitl_data')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'ppe_notification'
        verbose_name = 'PPE Notification'
        verbose_name_plural = 'PPE Notifications'

    def __str__(self):
        return f"Notification {self.notification_id} - Alert {self.alert_id}"


# ==============================================================================
# Operations & Communication Models
# ==============================================================================
class Incident(models.Model):
    incident_id = models.BigAutoField(primary_key=True, db_column='incident_id')
    title = models.CharField(max_length=255, db_column='title')
    description = models.TextField(db_column='description')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='incidents', db_column='site_id')
    type = models.CharField(max_length=100, db_column='type')
    severity = models.CharField(max_length=20, default='MEDIUM', db_column='severity')
    status = models.CharField(max_length=50, default='OPEN', db_index=True, db_column='status')
    reported_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='reported_incidents', db_column='reported_by')
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_incidents', db_column='assigned_to')
    resolution = models.TextField(null=True, blank=True, db_column='resolution')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'incident'
        verbose_name = 'Incident'
        verbose_name_plural = 'Incidents'

    def __str__(self):
        return f"Incident: {self.title}"


class Message(models.Model):
    message_id = models.BigAutoField(primary_key=True, db_column='message_id')
    sender = models.ForeignKey(ApplicationUser, on_delete=models.CASCADE, related_name='sent_messages', db_column='sender_id')
    receiver = models.ForeignKey(ApplicationUser, on_delete=models.CASCADE, related_name='received_messages', db_column='receiver_id')
    subject = models.CharField(max_length=255, db_column='subject')
    content = models.TextField(db_column='content')
    priority = models.CharField(max_length=20, default='NORMAL', db_column='priority')
    is_read = models.BooleanField(default=False, db_column='is_read')
    timestamp = models.DateTimeField(default=timezone.now, db_column='timestamp')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'message'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        return f"Msg from {self.sender} to {self.receiver}: {self.subject}"


class Report(models.Model):
    report_id = models.BigAutoField(primary_key=True, db_column='report_id')
    title = models.CharField(max_length=255, db_column='title')
    report_type = models.CharField(max_length=100, db_column='report_type')
    generated_by = models.ForeignKey(ApplicationUser, on_delete=models.CASCADE, related_name='reports', db_column='generated_by')
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports', db_column='site_id')
    format = models.CharField(max_length=20, default='PDF', db_column='format')
    file_url = models.TextField(null=True, blank=True, db_column='file_url')
    status = models.CharField(max_length=50, default='COMPLETED', db_index=True, db_column='status')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'report'
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'

    def __str__(self):
        return f"{self.report_type} Report: {self.title}"

