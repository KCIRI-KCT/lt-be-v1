from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from datetime import date
from .models import (
    Organization, Role, Employee, ApplicationUser,
    Country, State, City, Project, Site, Chainage,
    Worker, Attendance, Camera, AIAlert
)


class V1APIServiceTestCase(APITestCase):

    def setUp(self):
        # Create Organization & Role
        self.org = Organization.objects.create(
            organization_code="LT_TEST_ORG",
            organization_name="L&T Test Org"
        )
        self.role = Role.objects.create(
            role_id=1,
            role_name="Admin"
        )

        # Create Employees (Engineer and Manager)
        self.manager = Employee.objects.create(
            organization_id=self.org.organization_id,
            employee_code="MGR101",
            employee_name="Manager Bob",
            designation="Project Manager",
            department="Operations",
            email="manager.bob@example.com",
            mobile_number="9876500001"
        )
        self.engineer = Employee.objects.create(
            organization_id=self.org.organization_id,
            employee_code="ENG101",
            employee_name="Engineer Alice",
            designation="Site Engineer",
            department="Engineering",
            email="engineer.alice@example.com",
            mobile_number="9876500002"
        )

        # Create ApplicationUser & Authenticate Client via JWT
        self.user = ApplicationUser.objects.create_user(
            username="v1user",
            password="SecurePassword123!",
            employee=self.engineer,
            role_id=1
        )

        # Get JWT Access Token
        login_url = reverse('auth_login')
        login_response = self.client.post(login_url, {"username": "v1user", "password": "SecurePassword123!"}, format='json')
        self.access_token = login_response.data['data']['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        # Create Location Hierarchy
        self.country = Country.objects.create(name="India", code="IN")
        self.state = State.objects.create(name="Tamil Nadu", code="TN", country=self.country)
        self.city = City.objects.create(name="Chennai", state=self.state)

        # Create Project, Site, Chainage
        self.project = Project.objects.create(
            name="Metro Rail Extension Project",
            code="PRJ-METRO-01",
            city=self.city,
            manager=self.manager,
            engineer=self.engineer,
            status="ACTIVE"
        )
        self.site = Site.objects.create(
            name="Central Station Site",
            code="SITE-METRO-01",
            project=self.project,
            status="ACTIVE",
            safety_score=95.0
        )
        self.chainage = Chainage.objects.create(
            name="KM 10+500",
            site=self.site,
            km_marker="10+500",
            status="ACTIVE"
        )

        # Create Worker & Attendance
        self.worker = Worker.objects.create(
            employee_id="WRK-1001",
            name="Worker Dave",
            site=self.site,
            designation="Mason",
            status="ACTIVE"
        )
        self.attendance = Attendance.objects.create(
            worker=self.worker,
            site=self.site,
            date=date.today(),
            status="PRESENT"
        )

        # Create Camera & AI Alert
        self.camera = Camera.objects.create(
            name="CAM-SITE-01",
            rtsp_url="rtsp://192.168.1.100/stream",
            site=self.site,
            status="ACTIVE"
        )
        self.alert = AIAlert.objects.create(
            camera=self.camera,
            site=self.site,
            type="NO_HELMET",
            severity="HIGH",
            status="OPEN"
        )

    def test_unauthenticated_request_rejected(self):
        # Clear credentials
        self.client.credentials()
        url = reverse('v1_projects')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_projects_with_filters(self):
        url = reverse('v1_projects')
        
        # Test without filter
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 1)

        # Test filtering by engineerId
        response_eng = self.client.get(f"{url}?engineerId={self.engineer.employee_id}")
        self.assertEqual(response_eng.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_eng.data['data']), 1)

        # Test filtering by non-existent managerId
        response_empty = self.client.get(f"{url}?managerId=999999")
        self.assertEqual(response_empty.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_empty.data['data']), 0)

    def test_get_sites_with_filter(self):
        url = reverse('v1_sites')
        response = self.client.get(f"{url}?projectId={self.project.project_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 1)

    def test_get_chainages_with_filter(self):
        url = reverse('v1_chainages')
        response = self.client.get(f"{url}?siteId={self.site.site_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 1)

    def test_get_dashboard_metrics(self):
        url = reverse('v1_dashboard_metrics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        data = response.data['data']
        self.assertIn('total_active_sites', data)
        self.assertIn('total_workers', data)
        self.assertIn('active_workers_today', data)
        self.assertIn('ppe_compliance_avg', data)
        self.assertIn('open_alerts_count', data)
        self.assertIn('total_cameras', data)
        self.assertEqual(data['total_active_sites'], 1)

    def test_get_dashboard_progress_trend(self):
        url = reverse('v1_dashboard_progress_trend')

        # Test month range (default)
        res_month = self.client.get(f"{url}?range=month")
        self.assertEqual(res_month.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_month.data['data']['labels']), 12)

        # Test week range
        res_week = self.client.get(f"{url}?range=week")
        self.assertEqual(res_week.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_week.data['data']['labels']), 5)

        # Test year range
        res_year = self.client.get(f"{url}?range=year")
        self.assertEqual(res_year.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_year.data['data']['labels']), 5)

    def test_get_safety_alerts_with_filters(self):
        url = reverse('v1_safety_alerts')
        response = self.client.get(f"{url}?siteId={self.site.site_id}&status=OPEN&severity=HIGH")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['type'], 'NO_HELMET')

    def test_get_worker_attendance(self):
        url = reverse('v1_worker_attendance')
        response = self.client.get(f"{url}?siteId={self.site.site_id}&date={date.today()}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 1)

    def test_get_cameras(self):
        url = reverse('v1_cameras')
        response = self.client.get(f"{url}?siteId={self.site.site_id}&status=ACTIVE")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 1)
