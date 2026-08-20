# pyrefly: ignore [missing-import]
from rest_framework.test import APITestCase
# pyrefly: ignore [missing-import]
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .models import (
    Organization, Role, Employee, ApplicationUser, OTPRecord,
    Country, State, City, Project, Site, Chainage, Worker, Attendance,
    Camera, AIAlert, PPEAcknowledgement, PPENotification, Incident, Message, Report
)


class AuthAndCoreAPITestCase(APITestCase):

    def setUp(self):
        # Create initial test organization & role
        self.org = Organization.objects.create(
            organization_code="LT_ORG_TEST",
            organization_name="L&T Construction Test",
            status="ACTIVE"
        )
        self.role = Role.objects.create(
            role_id=1,
            role_name="Admin",
            role_description="Administrator",
            status="ACTIVE"
        )
        self.employee = Employee.objects.create(
            organization_id=self.org.organization_id,
            employee_code="EMP1001",
            employee_name="John Doe",
            designation="Software Engineer",
            department="Engineering",
            email="john.doe@example.com",
            mobile_number="9876543210",
            status="ACTIVE"
        )

    def test_health_check_endpoint(self):
        url = reverse('api_health_check')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['version'], 'v1')

    def test_user_registration_and_login_flow(self):
        # Register User
        register_url = reverse('auth_register')
        reg_payload = {
            "employee_code": "EMP1001",
            "username": "johndoe",
            "password": "SecurePassword123!",
            "role_id": "1"
        }
        reg_response = self.client.post(register_url, reg_payload, format='json')
        self.assertEqual(reg_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(reg_response.data['status'], 'success')
        self.assertIn('tokens', reg_response.data['data'])
        self.assertEqual(reg_response.data['data']['username'], 'johndoe')

        # Login User
        login_url = reverse('auth_login')
        login_payload = {
            "username": "johndoe",
            "password": "SecurePassword123!"
        }
        login_response = self.client.post(login_url, login_payload, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response.data['data']['tokens'])

        # Profile Access using Bearer Token
        access_token = login_response.data['data']['tokens']['access']
        profile_url = reverse('auth_profile')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        profile_response = self.client.get(profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data['data']['username'], 'johndoe')

    def test_unauthenticated_profile_access_fails(self):
        profile_url = reverse('auth_profile')
        self.client.credentials()  # Clear authorization
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_invalid_credentials(self):
        login_url = reverse('auth_login')
        login_payload = {
            "username": "non_existent_user",
            "password": "WrongPassword"
        }
        response = self.client.post(login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')

    def test_registration_with_alphanumeric_role_id(self):
        register_url = reverse('auth_register')
        reg_payload = {
            "username": "roleuser",
            "password": "Password123!",
            "role_id": "2026LT001"
        }
        reg_response = self.client.post(register_url, reg_payload, format='json')
        self.assertEqual(reg_response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', reg_response.data['data'])

    def test_request_otp_and_forgot_password_flow(self):
        # Create user account for employee
        user = ApplicationUser.objects.create_user(
            username="johndoe",
            password="OldPassword123",
            employee=self.employee
        )

        # Request OTP for Forgot Password
        otp_url = reverse('auth_request_otp')
        otp_payload = {
            "identifier": "john.doe@example.com",
            "purpose": "FORGOT_PASSWORD"
        }
        otp_response = self.client.post(otp_url, otp_payload, format='json')
        self.assertEqual(otp_response.status_code, status.HTTP_200_OK)
        otp_code = otp_response.data['data']['otp_code']

        # Reset Password using OTP
        forgot_pwd_url = reverse('auth_forgot_password')
        forgot_payload = {
            "identifier": "john.doe@example.com",
            "otp_code": otp_code,
            "new_password": "NewSuperPassword456!"
        }
        forgot_pwd_response = self.client.post(forgot_pwd_url, forgot_payload, format='json')
        self.assertEqual(forgot_pwd_response.status_code, status.HTTP_200_OK)

        # Verify Login with New Password
        login_url = reverse('auth_login')
        login_response = self.client.post(login_url, {"username": "johndoe", "password": "NewSuperPassword456!"}, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_request_otp_non_existent_identifier(self):
        otp_url = reverse('auth_request_otp')
        otp_payload = {
            "identifier": "unknown@example.com",
            "purpose": "FORGOT_PASSWORD"
        }
        response = self.client.post(otp_url, otp_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_forgot_password_invalid_otp(self):
        forgot_pwd_url = reverse('auth_forgot_password')
        forgot_payload = {
            "identifier": "john.doe@example.com",
            "otp_code": "000000",
            "new_password": "NewPassword123!"
        }
        response = self.client.post(forgot_pwd_url, forgot_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_forgot_username_flow(self):
        # Create user account
        ApplicationUser.objects.create_user(
            username="secret_user_99",
            password="Password123",
            employee=self.employee
        )

        # Request OTP for Forgot Username
        otp_url = reverse('auth_request_otp')
        otp_response = self.client.post(otp_url, {"identifier": "9876543210", "purpose": "FORGOT_USERNAME"}, format='json')
        self.assertEqual(otp_response.status_code, status.HTTP_200_OK)
        otp_code = otp_response.data['data']['otp_code']

        # Retrieve Username
        forgot_username_url = reverse('auth_forgot_username')
        forgot_un_response = self.client.post(forgot_username_url, {"identifier": "9876543210", "otp_code": otp_code}, format='json')
        self.assertEqual(forgot_un_response.status_code, status.HTTP_200_OK)
        self.assertEqual(forgot_un_response.data['data']['username'], "secret_user_99")

    def test_jwt_token_refresh_flow(self):
        # Create user and get tokens via login
        ApplicationUser.objects.create_user(username="refresher", password="Password123")
        login_url = reverse('auth_login')
        login_response = self.client.post(login_url, {"username": "refresher", "password": "Password123"}, format='json')
        refresh_token = login_response.data['data']['tokens']['refresh']

        # Refresh token endpoint
        token_refresh_url = reverse('token_refresh')
        response = self.client.post(token_refresh_url, {"refresh": refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_swagger_and_redoc_endpoints(self):
        swagger_url = reverse('swagger-ui')
        response = self.client.get(swagger_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        redoc_url = reverse('redoc')
        response = self.client.get(redoc_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        schema_url = reverse('schema')
        response = self.client.get(schema_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LocationAPITestCase(APITestCase):

    def setUp(self):
        self.user, _ = ApplicationUser.objects.get_or_create(username="loc_user", defaults={"password": "Password123"})
        self.client.force_authenticate(user=self.user)
        self.country = Country.objects.create(name="India", code="IN")
        self.state = State.objects.create(name="Maharashtra", code="MH", country=self.country)
        self.city = City.objects.create(name="Mumbai", state=self.state)

    def test_country_crud_and_search(self):
        url = reverse('country-list')
        
        # GET List
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        # POST Create
        payload = {"name": "United States", "code": "US"}
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        country_id = create_resp.data['data']['country_id']

        # GET Detail
        detail_url = reverse('country-detail', kwargs={'pk': country_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_resp.data['data']['name'], "United States")

        # PUT Update
        update_payload = {"name": "United States of America", "code": "USA", "status": "ACTIVE"}
        update_resp = self.client.put(detail_url, update_payload, format='json')
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(update_resp.data['data']['name'], "United States of America")

        # Search
        search_resp = self.client.get(f"{url}?search=America")
        self.assertEqual(search_resp.status_code, status.HTTP_200_OK)

        # DELETE Destroy
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)

    def test_state_crud_and_search(self):
        url = reverse('state-list')

        # GET List
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST Create
        payload = {"name": "Gujarat", "code": "GJ", "country": self.country.country_id}
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        state_id = create_resp.data['data']['state_id']

        # GET Detail
        detail_url = reverse('state-detail', kwargs={'pk': state_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

        # PUT Update
        update_resp = self.client.put(detail_url, {"name": "State of Gujarat", "code": "GJ", "country": self.country.country_id}, format='json')
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        # DELETE Destroy
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)

    def test_city_crud_and_search(self):
        url = reverse('city-list')

        # GET List
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST Create
        payload = {"name": "Pune", "state": self.state.state_id}
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        city_id = create_resp.data['data']['city_id']

        # GET Detail
        detail_url = reverse('city-detail', kwargs={'pk': city_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

        # PUT Update
        update_resp = self.client.put(detail_url, {"name": "Pune City", "state": self.state.state_id}, format='json')
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        # DELETE Destroy
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)


class ProjectHierarchyAPITestCase(APITestCase):

    def setUp(self):
        self.user, _ = ApplicationUser.objects.get_or_create(username="proj_user", defaults={"password": "Password123"})
        self.client.force_authenticate(user=self.user)
        self.country = Country.objects.create(name="India", code="IN")
        self.state = State.objects.create(name="Maharashtra", code="MH", country=self.country)
        self.city = City.objects.create(name="Mumbai", state=self.state)
        self.project = Project.objects.create(
            name="Bullet Train Project",
            code="PRJ_001",
            city=self.city,
            budget=5000000.00
        )
        self.site = Site.objects.create(
            name="Central Station Site",
            code="SITE_001",
            project=self.project,
            location="Bandra Kurla Complex"
        )
        self.chainage = Chainage.objects.create(
            name="KM 0-10 Segment",
            site=self.site,
            km_marker="KM-001"
        )

    def test_project_crud_and_search(self):
        url = reverse('project-list')

        # GET List
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST Create
        payload = {
            "name": "Metro Extension Line",
            "code": "PRJ_002",
            "city": self.city.city_id,
            "budget": "15000000.00",
            "status": "ACTIVE"
        }
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        prj_id = create_resp.data['data']['project_id']

        # GET Detail
        detail_url = reverse('project-detail', kwargs={'pk': prj_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

        # PUT Update
        update_resp = self.client.put(detail_url, {
            "name": "Metro Extension Line Phase 2",
            "code": "PRJ_002",
            "city": self.city.city_id,
            "budget": "20000000.00",
            "status": "ACTIVE"
        }, format='json')
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        # Search
        search_resp = self.client.get(f"{url}?search=Metro")
        self.assertEqual(search_resp.status_code, status.HTTP_200_OK)

        # DELETE Destroy
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)

    def test_site_crud_and_search(self):
        url = reverse('site-list')

        # GET List
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST Create
        payload = {
            "name": "North Yard Site",
            "code": "SITE_002",
            "project": self.project.project_id,
            "location": "Thane"
        }
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        site_id = create_resp.data['data']['site_id']

        # GET Detail
        detail_url = reverse('site-detail', kwargs={'pk': site_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

        # PUT Update
        update_resp = self.client.put(detail_url, {
            "name": "North Yard Depot",
            "code": "SITE_002",
            "project": self.project.project_id,
            "location": "Thane West"
        }, format='json')
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        # DELETE Destroy
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)

    def test_chainage_crud_and_search(self):
        url = reverse('chainage-list')

        # GET List
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST Create
        payload = {
            "name": "KM 10-20 Segment",
            "site": self.site.site_id,
            "km_marker": "KM-002",
            "status": "ACTIVE"
        }
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        ch_id = create_resp.data['data']['chainage_id']

        # GET Detail
        detail_url = reverse('chainage-detail', kwargs={'pk': ch_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

        # PUT Update
        update_resp = self.client.put(detail_url, {
            "name": "KM 10-20 Segment Updated",
            "site": self.site.site_id,
            "km_marker": "KM-002",
            "status": "ACTIVE"
        }, format='json')
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        # DELETE Destroy
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)


class WorkforceAPITestCase(APITestCase):

    def setUp(self):
        self.user, _ = ApplicationUser.objects.get_or_create(username="work_user", defaults={"password": "Password123"})
        self.client.force_authenticate(user=self.user)
        self.org = Organization.objects.create(organization_code="LT_WORKFORCE", organization_name="L&T Workforce Org")
        self.employee = Employee.objects.create(
            organization_id=self.org.organization_id,
            employee_code="EMP2002",
            employee_name="Alice Smith",
            designation="Site Manager",
            department="Operations",
            email="alice.smith@example.com",
            mobile_number="9876543211",
            status="ACTIVE"
        )
        self.country = Country.objects.create(name="India", code="IN")
        self.state = State.objects.create(name="Maharashtra", code="MH", country=self.country)
        self.city = City.objects.create(name="Mumbai", state=self.state)
        self.project = Project.objects.create(name="Bridge Const", code="PRJ_BRG", city=self.city)
        self.site = Site.objects.create(name="Bridge Pier Site", code="SITE_PIER", project=self.project)
        self.worker = Worker.objects.create(
            employee_id="WRK_101",
            name="Robert Johnson",
            designation="Welder",
            site=self.site
        )

    def test_employee_crud_and_search(self):
        url = reverse('employee-list')

        # GET List
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST Create
        payload = {
            "organization_id": self.org.organization_id,
            "employee_code": "EMP3003",
            "employee_name": "Charlie Brown",
            "designation": "Safety Officer",
            "department": "EHS",
            "email": "charlie.brown@example.com",
            "mobile_number": "9876543222",
            "status": "ACTIVE"
        }
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        emp_id = create_resp.data['data']['employee_id']

        # GET Detail
        detail_url = reverse('employee-detail', kwargs={'pk': emp_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

        # PUT Update
        update_resp = self.client.put(detail_url, {
            "organization_id": self.org.organization_id,
            "employee_code": "EMP3003",
            "employee_name": "Charlie Brown Jr.",
            "designation": "Senior Safety Officer",
            "department": "EHS",
            "email": "charlie.brown@example.com",
            "mobile_number": "9876543222",
            "status": "ACTIVE"
        }, format='json')
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        # Search
        search_resp = self.client.get(f"{url}?search=Charlie")
        self.assertEqual(search_resp.status_code, status.HTTP_200_OK)

        # DELETE Destroy
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)

    def test_worker_crud_and_search(self):
        url = reverse('worker-list')

        # GET List
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST Create
        payload = {
            "employee_id": "WRK_102",
            "name": "David Miller",
            "designation": "Electrician",
            "site": self.site.site_id,
            "phone": "9998887776",
            "email": "david.m@example.com"
        }
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        wrk_id = create_resp.data['data']['worker_id']

        # GET Detail
        detail_url = reverse('worker-detail', kwargs={'pk': wrk_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

        # PUT Update
        update_resp = self.client.put(detail_url, {
            "employee_id": "WRK_102",
            "name": "David Miller Updated",
            "designation": "Master Electrician",
            "site": self.site.site_id,
            "phone": "9998887776",
            "email": "david.m@example.com"
        }, format='json')
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        # DELETE Destroy
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)

    def test_attendance_crud_and_search(self):
        url = reverse('attendance-list')

        # GET List
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST Create
        payload = {
            "worker": self.worker.worker_id,
            "site": self.site.site_id,
            "status": "PRESENT"
        }
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        att_id = create_resp.data['data']['attendance_id']

        # GET Detail
        detail_url = reverse('attendance-detail', kwargs={'pk': att_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

        # PUT Update
        update_resp = self.client.put(detail_url, {
            "worker": self.worker.worker_id,
            "site": self.site.site_id,
            "status": "ABSENT"
        }, format='json')
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        # DELETE Destroy
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)


class CameraAndAIMonitoringAPITestCase(APITestCase):

    def setUp(self):
        self.user, _ = ApplicationUser.objects.get_or_create(username="ai_officer", defaults={"password": "Password123"})
        self.client.force_authenticate(user=self.user)
        self.country = Country.objects.create(name="India", code="IN")
        self.state = State.objects.create(name="Maharashtra", code="MH", country=self.country)
        self.city = City.objects.create(name="Mumbai", state=self.state)
        self.project = Project.objects.create(name="Camera Monitored Project", code="PRJ_CAM", city=self.city)
        self.site = Site.objects.create(name="Camera Site", code="SITE_CAM", project=self.project)
        self.camera = Camera.objects.create(
            name="Main Gate Cam",
            rtsp_url="rtsp://192.168.1.100:554/stream1",
            site=self.site,
            location="Entrance"
        )
        self.employee = Employee.objects.create(
            organization_id=1,
            employee_code="EMP_SAFETY",
            employee_name="Safety Officer Sam",
            designation="Safety Officer",
            department="EHS",
            email="sam.safety@example.com",
            mobile_number="9876543300"
        )
        self.ai_alert = AIAlert.objects.create(
            camera=self.camera,
            site=self.site,
            type="NO_HELMET",
            severity="HIGH",
            status="OPEN"
        )

    def test_camera_requires_authentication(self):
        url = reverse('camera-list')
        self.client.force_authenticate(user=None)
        unauth_resp = self.client.get(url)
        self.assertEqual(unauth_resp.status_code, status.HTTP_401_UNAUTHORIZED)

        post_unauth_resp = self.client.post(url, {
            "name": "Unauthenticated Cam",
            "rtsp_url": "http://10.1.82.235:8080/feed/0",
            "site": self.site.site_id
        })
        self.assertEqual(post_unauth_resp.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)
        auth_resp = self.client.get(url)
        self.assertEqual(auth_resp.status_code, status.HTTP_200_OK)

    def test_camera_crud_and_search(self):
        url = reverse('camera-list')

        # GET List
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST Create
        payload = {
            "name": "Tower Cam 2",
            "rtsp_url": "rtsp://192.168.1.101:554/stream1",
            "site": self.site.site_id,
            "location": "Crane Tower",
            "status": "ACTIVE",
            "type": "PTZ"
        }
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        cam_id = create_resp.data['data']['camera_id']

        # GET Detail
        detail_url = reverse('camera-detail', kwargs={'pk': cam_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

        # PUT Update
        update_resp = self.client.put(detail_url, {
            "name": "Tower Cam 2 (Updated)",
            "rtsp_url": "rtsp://192.168.1.101:554/stream1",
            "site": self.site.site_id,
            "location": "Crane Tower Top",
            "status": "ACTIVE",
            "type": "PTZ"
        }, format='json')
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        # Search
        search_resp = self.client.get(f"{url}?search=Tower")
        self.assertEqual(search_resp.status_code, status.HTTP_200_OK)

        # DELETE Destroy
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)

    def test_ai_alert_crud_and_search(self):
        url = reverse('aialert-list')

        # GET List
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST Create
        payload = {
            "camera": self.camera.camera_id,
            "site": self.site.site_id,
            "type": "NO_SAFETY_VEST",
            "severity": "MEDIUM",
            "status": "OPEN"
        }
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        alert_id = create_resp.data['data']['alert_id']

        # GET Detail
        detail_url = reverse('aialert-detail', kwargs={'pk': alert_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

        # PUT Update
        update_resp = self.client.put(detail_url, {
            "camera": self.camera.camera_id,
            "site": self.site.site_id,
            "type": "NO_SAFETY_VEST",
            "severity": "HIGH",
            "status": "ACKNOWLEDGED",
            "acknowledged_by": self.user.user_id
        }, format='json')
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        # DELETE Destroy
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)

    def test_ppe_acknowledgement_crud_and_search(self):
        url = reverse('ppeacknowledgement-list')

        # GET List
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST Create
        payload = {
            "alert": self.ai_alert.alert_id,
            "acknowledged_by": self.user.user_id,
            "acknowledged_by_role": "Safety Manager",
            "notes": "Worker warned and issued helmet."
        }
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        ack_id = create_resp.data['data']['acknowledgement_id']

        # GET Detail
        detail_url = reverse('ppeacknowledgement-detail', kwargs={'pk': ack_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

        # DELETE Destroy
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)

    def test_ppe_notification_crud_and_search(self):
        url = reverse('ppenotification-list')

        # GET List
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST Create
        payload = {
            "alert": self.ai_alert.alert_id,
            "safety_officer": self.employee.employee_id,
            "status": "pending_review"
        }
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        notif_id = create_resp.data['data']['notification_id']

        # GET Detail
        detail_url = reverse('ppenotification-detail', kwargs={'pk': notif_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

        # DELETE Destroy
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)

    def test_ppe_notification_hitl_resolve_flow_and_project_engineer_reflection(self):
        # 1. Create Safety Officer & Project Engineer employee accounts
        proj_eng_emp = Employee.objects.create(
            organization_id=1,
            employee_code="EMP_PROJ_ENG",
            employee_name="Project Engineer Peter",
            designation="Project Engineer",
            department="Engineering",
            email="peter.pe@example.com",
            mobile_number="9876543999"
        )
        self.project.engineer = proj_eng_emp
        self.project.save()

        # Create user for Project Engineer
        proj_eng_user = ApplicationUser.objects.create_user(
            username="proj_engineer",
            password="Password123",
            employee=proj_eng_emp,
            role_id=5
        )

        # 2. Create PPE Notification
        notif = PPENotification.objects.create(
            alert=self.ai_alert,
            safety_officer=self.employee,
            status="pending_review",
            hitl_data={"bounding_box": [10, 20, 50, 60]}
        )

        # 3. Verify all users (including Project Engineer) can view notification details
        self.client.force_authenticate(user=proj_eng_user)
        list_url = reverse('ppenotification-list')
        list_resp = self.client.get(list_url)
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(list_resp.data['success'])
        self.assertGreater(len(list_resp.data['data']), 0)

        detail_url = reverse('ppenotification-detail', kwargs={'pk': notif.notification_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_resp.data['data']['project_engineer_name'], "Project Engineer Peter")

        # 4. Safety Officer triggers HITL Resolution
        self.client.force_authenticate(user=self.user)
        hitl_url = reverse('ppenotification-hitl-resolve', kwargs={'pk': notif.notification_id})
        hitl_payload = {
            "decision": "SOLVED",
            "notes": "Safety helmet provided to operator and safety warning issued.",
            "hitl_data": {"confidence": 0.98, "verified": True}
        }
        hitl_resp = self.client.post(hitl_url, hitl_payload, format='json')
        self.assertEqual(hitl_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(hitl_resp.data['success'])
        self.assertEqual(hitl_resp.data['data']['status'], "SOLVED")

        # 5. Verify status reflection back to Project Engineer
        self.client.force_authenticate(user=proj_eng_user)
        pe_view_resp = self.client.get(detail_url)
        self.assertEqual(pe_view_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(pe_view_resp.data['data']['status'], "SOLVED")

        # Verify parent AIAlert status updated to RESOLVED
        self.ai_alert.refresh_from_db()
        self.assertEqual(self.ai_alert.status, "RESOLVED")

        # Verify PPEAcknowledgement entry created
        ack_exists = PPEAcknowledgement.objects.filter(alert=self.ai_alert).exists()
        self.assertTrue(ack_exists)


class OperationsAndCommunicationAPITestCase(APITestCase):

    def setUp(self):
        self.user, _ = ApplicationUser.objects.get_or_create(username="ops_user", defaults={"password": "Password123"})
        self.client.force_authenticate(user=self.user)
        self.country = Country.objects.create(name="India", code="IN")
        self.state = State.objects.create(name="Maharashtra", code="MH", country=self.country)
        self.city = City.objects.create(name="Mumbai", state=self.state)
        self.project = Project.objects.create(name="Operations Project", code="PRJ_OPS", city=self.city)
        self.site = Site.objects.create(name="Ops Site", code="SITE_OPS", project=self.project)

        self.reporter = Employee.objects.create(
            organization_id=1,
            employee_code="EMP_REPORTER",
            employee_name="Reporter Employee",
            designation="Site Engineer",
            department="Civil",
            email="reporter@example.com",
            mobile_number="9876543400"
        )
        self.assignee = Employee.objects.create(
            organization_id=1,
            employee_code="EMP_ASSIGNEE",
            employee_name="Assignee Employee",
            designation="Maintenance Lead",
            department="Maintenance",
            email="assignee@example.com",
            mobile_number="9876543401"
        )
        self.user1 = ApplicationUser.objects.create_user(username="user_sender", password="Password123")
        self.user2 = ApplicationUser.objects.create_user(username="user_receiver", password="Password123")

    def test_incident_crud_and_search(self):
        url = reverse('incident-list')

        # GET List
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST Create
        payload = {
            "title": "Minor Material Spill",
            "description": "Cement bags spilled near storage zone",
            "site": self.site.site_id,
            "type": "MATERIAL_SPILL",
            "severity": "LOW",
            "status": "OPEN",
            "reported_by": self.reporter.employee_id,
            "assigned_to": self.assignee.employee_id
        }
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        inc_id = create_resp.data['data']['incident_id']

        # GET Detail
        detail_url = reverse('incident-detail', kwargs={'pk': inc_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

        # PUT Update
        update_resp = self.client.put(detail_url, {
            "title": "Minor Material Spill (Resolved)",
            "description": "Cement bags cleaned up",
            "site": self.site.site_id,
            "type": "MATERIAL_SPILL",
            "severity": "LOW",
            "status": "CLOSED",
            "reported_by": self.reporter.employee_id,
            "assigned_to": self.assignee.employee_id,
            "resolution": "Area cleaned and repacked."
        }, format='json')
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        # Search
        search_resp = self.client.get(f"{url}?search=Spill")
        self.assertEqual(search_resp.status_code, status.HTTP_200_OK)

        # DELETE Destroy
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)

    def test_message_crud_and_search(self):
        url = reverse('message-list')

        # GET List
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST Create
        payload = {
            "sender": self.user1.user_id,
            "receiver": self.user2.user_id,
            "subject": "Daily Inspection Report",
            "content": "Please review the daily inspection report attached.",
            "priority": "HIGH"
        }
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        msg_id = create_resp.data['data']['message_id']

        # GET Detail
        detail_url = reverse('message-detail', kwargs={'pk': msg_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

        # PUT Update
        update_resp = self.client.put(detail_url, {
            "sender": self.user1.user_id,
            "receiver": self.user2.user_id,
            "subject": "Daily Inspection Report (Read)",
            "content": "Please review the daily inspection report attached.",
            "priority": "HIGH",
            "is_read": True
        }, format='json')
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        # DELETE Destroy
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)

    def test_report_crud_and_search(self):
        url = reverse('report-list')

        # GET List
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST Create
        payload = {
            "title": "Monthly Safety Audit Report",
            "report_type": "SAFETY_AUDIT",
            "generated_by": self.user1.user_id,
            "site": self.site.site_id,
            "format": "PDF",
            "status": "COMPLETED"
        }
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        rpt_id = create_resp.data['data']['report_id']

        # GET Detail
        detail_url = reverse('report-detail', kwargs={'pk': rpt_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

        # PUT Update
        update_resp = self.client.put(detail_url, {
            "title": "Monthly Safety Audit Report (Final)",
            "report_type": "SAFETY_AUDIT",
            "generated_by": self.user1.user_id,
            "site": self.site.site_id,
            "format": "PDF",
            "status": "COMPLETED"
        }, format='json')
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        # Search
        search_resp = self.client.get(f"{url}?search=Safety")
        self.assertEqual(search_resp.status_code, status.HTTP_200_OK)

        # DELETE Destroy
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_200_OK)

    def test_camera_ptz_control(self):
        cam = Camera.objects.create(
            name="Demo PTZ Camera",
            rtsp_url="http://10.1.82.235:8080/feed/0",
            site=self.site,
            type="PTZ"
        )
        url = reverse('camera-ptz', kwargs={'pk': cam.camera_id})
        
        # Test Unauthenticated
        self.client.force_authenticate(user=None)
        unauth_resp = self.client.post(url, {"action": "PAN LEFT", "pan": -30}, format='json')
        self.assertEqual(unauth_resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test Authenticated
        self.client.force_authenticate(user=self.user1)
        auth_resp = self.client.post(url, {"action": "PAN LEFT", "pan": -30, "zoom": 1.35}, format='json')
        self.assertEqual(auth_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(auth_resp.data['success'])
        self.assertEqual(auth_resp.data['data']['action'], 'PAN LEFT')


class DashboardAndAnalyticsAPITestCase(APITestCase):

    def setUp(self):
        self.user = ApplicationUser.objects.create_user(username="analytics_user", password="Password123!")
        self.client.force_authenticate(user=self.user)

    def test_dashboard_metrics_endpoint(self):
        url = reverse('dashboard_metrics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('total_active_sites', response.data['data'])

    def test_dashboard_progress_trend_endpoint(self):
        url = reverse('dashboard_progress_trend')
        res_month = self.client.get(f"{url}?range=month")
        self.assertEqual(res_month.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_month.data['data']['labels']), 12)

        res_week = self.client.get(f"{url}?range=week")
        self.assertEqual(res_week.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_week.data['data']['labels']), 5)

    def test_safety_alerts_summary_endpoint(self):
        url = reverse('safety_alerts_summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')

    def test_worker_attendance_summary_endpoint(self):
        url = reverse('worker_attendance_summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')

    def test_camera_control_endpoint(self):
        url = reverse('cameras_ptz_control')
        response = self.client.post(url, {"camera_id": 1, "action": "TILT_UP", "tilt": 15}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')


