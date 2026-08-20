from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from LT_AMS_API.models import (
    Organization, Role, Employee, ApplicationUser, Country, State, City, Project, Site, Camera, Worker
)

class Command(BaseCommand):
    help = 'Seed complete roles, employees, application users, and master hierarchy data.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding master data & user accounts...")

        # 1. Organization
        org, _ = Organization.objects.get_or_create(
            organization_code='LT_CORP',
            defaults={
                'organization_name': 'Larsen & Toubro Construction',
                'organization_type': 'Infrastructure',
                'country': 'India',
                'status': 'ACTIVE'
            }
        )

        # 2. Roles
        roles_data = [
            (1, 'Admin', 'System Administrator with full system permissions'),
            (2, 'Project Manager', 'Oversees project budget, timeline and site operations'),
            (3, 'Site Supervisor', 'Manages daily site activities and workforce supervision'),
            (4, 'Site Engineer', 'Manages engineering execution and quality on construction sites'),
            (6, 'Safety Manager', 'Leads safety compliance, risk assessment and incident response'),
            (7, 'Safety Engineer', 'Monitors site safety hazards and PPE compliance'),
        ]

        for r_id, r_name, r_desc in roles_data:
            Role.objects.get_or_create(
                role_id=r_id,
                defaults={'role_name': r_name, 'role_description': r_desc, 'status': 'ACTIVE'}
            )

        # 3. Employees & Application Users
        users_data = [
            ('LT_EMP_ADM01', 'System Administrator', 'Chief System Admin', 'IT & Enterprise Systems', 'admin@lt.com', '+919800000001', 'admin', 1),
            ('LT_EMP_PM01', 'Project Manager', 'Senior Project Manager', 'Project Management', 'projectmanager@lt.com', '+919800000002', 'projectmanager', 2),
            ('LT_EMP_SS01', 'Site Supervisor', 'Senior Site Supervisor', 'Site Operations', 'sitesupervisor@lt.com', '+919800000003', 'sitesupervisor', 3),
            ('LT_EMP_SE01', 'Site Engineer', 'Lead Site Engineer', 'Civil Engineering', 'siteengineer@lt.com', '+919800000004', 'siteengineer', 4),
            ('LT_EMP_SO01', 'safety officer', 'Safety Officer', 'Health Safety & Environment', 'safetyofficer@larsentoubro.com', '+919800000006', 'safetymanager', 6),
            ('LT_EMP_SE02', 'safety engineer', 'Safety Engineer', 'Health Safety & Environment', 'safetyengineer@larsentoubro.com', '+919800000007', 'safetyengineer', 7),
        ]

        hashed_password = make_password('Admin@123')

        for code, name, desig, dept, email, phone, username, role_id in users_data:
            emp, _ = Employee.objects.get_or_create(
                employee_code=code,
                defaults={
                    'organization_id': org.organization_id,
                    'employee_name': name,
                    'designation': desig,
                    'department': dept,
                    'email': email,
                    'mobile_number': phone,
                    'status': 'ACTIVE'
                }
            )

            ApplicationUser.objects.get_or_create(
                username=username,
                defaults={
                    'employee': emp,
                    'role_id': role_id,
                    'password': hashed_password,
                    'account_status': 'ACTIVE'
                }
            )

        # 4. Location Hierarchy
        country, _ = Country.objects.get_or_create(code='IND', defaults={'name': 'India', 'status': 'ACTIVE'})
        state, _ = State.objects.get_or_create(code='TN', country=country, defaults={'name': 'Tamil Nadu', 'status': 'ACTIVE'})
        city, _ = City.objects.get_or_create(name='Chennai', state=state, defaults={'status': 'ACTIVE'})

        # 5. Project & Site
        pm_emp = Employee.objects.get(employee_code='LT_EMP_PM01')
        ss_emp = Employee.objects.get(employee_code='LT_EMP_SS01')
        se_emp = Employee.objects.get(employee_code='LT_EMP_SE01')

        project, _ = Project.objects.get_or_create(
            code='PRJ-CHN-01',
            defaults={
                'name': 'Chennai Metro Rail Extension Phase II',
                'city': city,
                'budget': 50000000.00,
                'status': 'ACTIVE',
                'progress': 35.5,
                'manager': pm_emp,
                'supervisor': ss_emp,
                'engineer': se_emp
            }
        )

        site, _ = Site.objects.get_or_create(
            code='SITE-OMR-01',
            project=project,
            defaults={
                'name': 'OMR Corridor Station 12',
                'location': 'Old Mahabalipuram Road, Chennai',
                'latitude': 12.971598,
                'longitude': 80.243683,
                'status': 'ACTIVE',
                'worker_count': 45,
                'safety_score': 98.5
            }
        )

        # 6. Camera & Worker
        Camera.objects.get_or_create(
            name='CAM-OMR12-NORTH-GATE',
            site=site,
            defaults={
                'rtsp_url': 'rtsp://camera.omr12.landt.internal:554/live/stream1',
                'location': 'North Gate Entry & Inspection',
                'status': 'ACTIVE',
                'type': 'PTZ',
                'resolution': '4K',
                'health_score': 100.0
            }
        )

        Worker.objects.get_or_create(
            employee_id='WRK-1001',
            defaults={
                'name': 'Arun Kumar',
                'phone': '+919123456789',
                'designation': 'Equipment Operator',
                'department': 'Site Operations',
                'site': site,
                'status': 'ACTIVE'
            }
        )

        self.stdout.write(self.style.SUCCESS("All roles, users, and master data seeded successfully!"))
        self.stdout.write("Created User Credentials (Password for all accounts: Admin@123):")
        for _, _, desig, _, _, _, uname, _ in users_data:
            self.stdout.write(f"  - Username: '{uname}' | Designation: {desig}")
