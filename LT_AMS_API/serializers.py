from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db import models
from .models import (
    Organization, Role, Employee, ApplicationUser, OTPRecord,
    Country, State, City, Project, Site, Chainage, Worker, Attendance,
    Camera, AIAlert, PPEAcknowledgement, PPENotification, Incident, Message, Report
)

import random




class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [
            'employee_id',
            'organization_id',
            'employee_code',
            'employee_name',
            'designation',
            'department',
            'email',
            'mobile_number',
            'status',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['employee_id', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    employee_code = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True, min_length=6, required=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True, allow_null=True)
    mobile_number = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    employee_name = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    role_id = serializers.CharField(required=False, default="1")

    class Meta:
        model = ApplicationUser
        fields = [
            'user_id',
            'username',
            'password',
            'employee_code',
            'email',
            'mobile_number',
            'employee_name',
            'role_id',
            'account_status'
        ]
        read_only_fields = ['user_id', 'account_status']

    def create(self, validated_data):
        employee_code = validated_data.pop('employee_code', None)
        email = validated_data.pop('email', None)
        mobile_number = validated_data.pop('mobile_number', None)
        employee_name = validated_data.pop('employee_name', None)
        role_id_raw = validated_data.pop('role_id', '1')
        password = validated_data.pop('password')
        username = validated_data.get('username')

        # Sanitize role_id to ensure it fits into PostgreSQL bigint
        try:
            digits = ''.join(c for c in str(role_id_raw) if c.isdigit())
            parsed_role = int(digits) if digits else 1
            role_id = parsed_role if parsed_role <= 9223372036854775807 else 1
        except (ValueError, TypeError):
            role_id = 1

        # Ensure a valid Role exists in table 'role' to satisfy fk_user_role constraint
        role_obj = Role.objects.filter(role_id=role_id).first()
        if not role_obj:
            role_obj = Role.objects.first()
            if not role_obj:
                role_obj = Role.objects.create(
                    role_id=role_id if role_id > 0 else 1,
                    role_name="Admin" if role_id == 1 else "User",
                    role_description="System Role",
                    status="ACTIVE"
                )

        validated_data['role_id'] = role_obj.role_id


        # 1. Determine employee_code
        if not employee_code:
            employee_code = f"EMP-{username.upper()}"


        # 2. Lookup existing employee or create new employee on the fly
        employee = Employee.objects.filter(employee_code=employee_code).first()

        if not employee:
            emp_email = email if email else f"{username}@landt.local"
            emp_mobile = mobile_number if mobile_number else f"9000{random.randint(100000, 999999)}"
            emp_name = employee_name if employee_name else username.capitalize()

            # Ensure unique email/mobile fallback if collisions occur
            if Employee.objects.filter(email=emp_email).exists():
                emp_email = f"{username}_{random.randint(100, 999)}@landt.local"
            if Employee.objects.filter(mobile_number=emp_mobile).exists():
                emp_mobile = f"9000{random.randint(100000, 999999)}"

            # Ensure an organization exists to satisfy fk_employee_organization constraint
            org = Organization.objects.first()
            if not org:
                org = Organization.objects.create(
                    organization_code="LT_ORG",
                    organization_name="L&T Construction",
                    status="ACTIVE"
                )

            employee = Employee.objects.create(
                organization_id=org.organization_id,
                employee_code=employee_code,
                employee_name=emp_name,
                designation="User",
                department="General",
                email=emp_email,
                mobile_number=emp_mobile,
                status="ACTIVE"
            )


        # 3. Create ApplicationUser linked to Employee
        user = ApplicationUser.objects.create_user(
            employee=employee,
            password=password,
            **validated_data
        )
        return user



class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid username or password.")

        if not user.is_active or user.account_status != 'ACTIVE':
            raise serializers.ValidationError("User account is inactive or disabled.")

        attrs['user'] = user
        return attrs


class RequestOTPSerializer(serializers.Serializer):
    identifier = serializers.CharField(
        required=True,
        help_text="Email or Mobile Number associated with the employee/user account."
    )
    purpose = serializers.ChoiceField(
        choices=OTPRecord.PURPOSE_CHOICES,
        required=True
    )

    def validate(self, attrs):
        identifier = attrs.get('identifier')
        # Check if identifier matches any employee's email or mobile_number
        employee = Employee.objects.filter(models.Q(email=identifier) | models.Q(mobile_number=identifier)).first()
        if not employee:
            raise serializers.ValidationError("No registered user found with the provided email or mobile number.")
        
        attrs['employee'] = employee
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)
    otp_code = serializers.CharField(max_length=6, required=True)
    new_password = serializers.CharField(min_length=6, write_only=True, required=True)

    def validate(self, attrs):
        identifier = attrs.get('identifier')
        otp_code = attrs.get('otp_code')

        otp_record = OTPRecord.objects.filter(
            identifier=identifier,
            otp_code=otp_code,
            purpose='FORGOT_PASSWORD',
            is_used=False
        ).order_by('-created_at').first()

        if not otp_record or not otp_record.is_valid():
            raise serializers.ValidationError("Invalid or expired OTP code.")

        # Find associated user
        employee = Employee.objects.filter(models.Q(email=identifier) | models.Q(mobile_number=identifier)).first()
        if not employee:
            raise serializers.ValidationError("No user associated with this identifier.")

        user = ApplicationUser.objects.filter(employee=employee).first()
        if not user:
            raise serializers.ValidationError("No application user account found for this employee.")

        attrs['user'] = user
        attrs['otp_record'] = otp_record
        return attrs


class ForgotUsernameSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)
    otp_code = serializers.CharField(max_length=6, required=True)

    def validate(self, attrs):
        identifier = attrs.get('identifier')
        otp_code = attrs.get('otp_code')

        otp_record = OTPRecord.objects.filter(
            identifier=identifier,
            otp_code=otp_code,
            purpose='FORGOT_USERNAME',
            is_used=False
        ).order_by('-created_at').first()

        if not otp_record or not otp_record.is_valid():
            raise serializers.ValidationError("Invalid or expired OTP code.")

        employee = Employee.objects.filter(models.Q(email=identifier) | models.Q(mobile_number=identifier)).first()
        if not employee:
            raise serializers.ValidationError("No employee record found for this identifier.")

        user = ApplicationUser.objects.filter(employee=employee).first()
        if not user:
            raise serializers.ValidationError("No application user account found for this employee.")

        attrs['username'] = user.username
        attrs['otp_record'] = otp_record
        return attrs


class ApplicationUserProfileSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)

    class Meta:
        model = ApplicationUser
        fields = [
            'user_id',
            'username',
            'role_id',
            'account_status',
            'last_login',
            'employee'
        ]


# ==============================================================================
# Location Serializers
# ==============================================================================
class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'
        read_only_fields = ['country_id', 'created_at', 'updated_at']


class StateSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)

    class Meta:
        model = State
        fields = '__all__'
        read_only_fields = ['state_id', 'created_at', 'updated_at']


class CitySerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    country_name = serializers.CharField(source='state.country.name', read_only=True)

    class Meta:
        model = City
        fields = '__all__'
        read_only_fields = ['city_id', 'created_at', 'updated_at']


# ==============================================================================
# Project & Site Hierarchy Serializers
# ==============================================================================
class ChainageSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source='site.name', read_only=True)

    class Meta:
        model = Chainage
        fields = '__all__'
        read_only_fields = ['chainage_id', 'created_at', 'updated_at']


class SiteSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    chainages = ChainageSerializer(many=True, read_only=True)

    class Meta:
        model = Site
        fields = '__all__'
        read_only_fields = ['site_id', 'created_at', 'updated_at']


class ProjectSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    manager_name = serializers.CharField(source='manager.employee_name', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.employee_name', read_only=True)
    engineer_name = serializers.CharField(source='engineer.employee_name', read_only=True)
    sites = SiteSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['project_id', 'created_at', 'updated_at']


# ==============================================================================
# Workforce Serializers
# ==============================================================================
class WorkerSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source='site.name', read_only=True)

    class Meta:
        model = Worker
        fields = '__all__'
        read_only_fields = ['worker_id', 'created_at', 'updated_at']


class AttendanceSerializer(serializers.ModelSerializer):
    worker_name = serializers.CharField(source='worker.name', read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)

    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['attendance_id', 'created_at', 'updated_at']


# ==============================================================================
# Camera & AI Monitoring Serializers
# ==============================================================================
class CameraSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source='site.name', read_only=True)

    class Meta:
        model = Camera
        fields = '__all__'
        read_only_fields = ['camera_id', 'created_at', 'updated_at']


class AIAlertSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source='camera.name', read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    acknowledged_by_username = serializers.CharField(source='acknowledged_by.username', read_only=True)

    class Meta:
        model = AIAlert
        fields = '__all__'
        read_only_fields = ['alert_id', 'created_at', 'updated_at']


class PPEAcknowledgementSerializer(serializers.ModelSerializer):
    acknowledged_by_username = serializers.CharField(source='acknowledged_by.username', read_only=True)

    class Meta:
        model = PPEAcknowledgement
        fields = '__all__'
        read_only_fields = ['acknowledgement_id', 'created_at', 'updated_at']


class PPENotificationSerializer(serializers.ModelSerializer):
    safety_officer_name = serializers.CharField(source='safety_officer.employee_name', read_only=True)

    class Meta:
        model = PPENotification
        fields = '__all__'
        read_only_fields = ['notification_id', 'created_at', 'updated_at']


# ==============================================================================
# Operations & Communication Serializers
# ==============================================================================
class IncidentSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source='site.name', read_only=True)
    reported_by_name = serializers.CharField(source='reported_by.employee_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.employee_name', read_only=True)

    class Meta:
        model = Incident
        fields = '__all__'
        read_only_fields = ['incident_id', 'created_at', 'updated_at']


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)

    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['message_id', 'created_at', 'updated_at']


class ReportSerializer(serializers.ModelSerializer):
    generated_by_username = serializers.CharField(source='generated_by.username', read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)

    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ['report_id', 'created_at', 'updated_at']

