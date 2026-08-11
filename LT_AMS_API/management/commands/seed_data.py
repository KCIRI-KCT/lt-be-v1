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
            (1, 'Admin', 'System Administrator with full permissions'),
            (2, 'Project Manager', 'Oversees project budget, timeline and operations'),
            (3, 'Site Supervisor', 'Manages daily site activities and workforce'),
            (4, 'Site Engineer', 'Manages engineering tasks on construction sites'),
            (5, 'Project Engineer', 'Handles project engineering design and planning'),
            (6, 'Safety Manager', 'Leads safety compliance and incident management'),
            (7, 'Safety Engineer', 'Monitors safety hazards and PPE compliance'),
        ]

        role_objs = {}
        for r_id, r_name, r_desc in roles_data:
            role, _ = Role.objects.get_or_create(
                role_id=r_id,
                defaults={'role_name': r_name, 'role_description': r_desc, 'status': 'ACTIVE'}
            )
            role_objs[r_name] = role

        # 3. Employees & Application Users
        users_data = [
            ('EMP_ADM_01', 'System Admin', 'System Administrator', 'IT & Admin', 'admin@landt.local', '9000000001', 'admin', 1),
            ('EMP_PM_01', 'Rajesh Kumar', 'Project Manager', 'Project Management', 'pm@landt.local', '9000000002', 'pm_user', 2),
            ('EMP_SS_01', 'Suresh Raina', 'Site Supervisor', 'Site Operations', 'supervisor@landt.local', '9000000003', 'supervisor_user', 3),
            ('EMP_SE_01', 'Venkatesh Iyer', 'Site Engineer', 'Civil Engineering', 'site_eng@landt.local', '9000000004', 'site_eng_user', 4),
            ('EMP_PE_01', 'Anand Verma', 'Project Engineer', 'Planning & Design', 'proj_eng@landt.local', '9000000005', 'proj_eng_user', 5),
            ('EMP_SM_01', 'Priya Sharma', 'Safety Manager', 'HSE & Safety', 'safety_mgr@landt.local', '9000000006', 'safety_mgr_user', 6),
            ('EMP_SE2_01', 'Rahul Dravid', 'Safety Engineer', 'HSE & Safety', 'safety_eng@landt.local', '9000000007', 'safety_eng_user', 7),
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
        pm_emp = Employee.objects.get(employee_code='EMP_PM_01')
        ss_emp = Employee.objects.get(employee_code='EMP_SS_01')
        se_emp = Employee.objects.get(employee_code='EMP_SE_01')

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
            name='CAM-SITE12-NORTH',
            site=site,
            defaults={
                'rtsp_url': 'rtsp://admin:admin123@192.168.1.100:554/stream1',
                'location': 'North Gate Entry',
                'status': 'ACTIVE',
                'type': 'PTZ',
                'resolution': '4K',
                'health_score': 99.0
            }
        )

        Worker.objects.get_or_create(
            employee_id='WRK-1001',
            defaults={
                'name': 'Arun Sharma',
                'phone': '9123456789',
                'designation': 'Site Operator',
                'department': 'Safety & Ops',
                'site': site,
                'status': 'ACTIVE'
            }
        )

        self.stdout.write(self.style.SUCCESS("All roles, users, and master data seeded successfully!"))
        self.stdout.write("Created User Credentials (Password for all accounts: Admin@123):")
        for _, _, desig, _, _, _, uname, _ in users_data:
            self.stdout.write(f"  - Username: '{uname}' | Designation: {desig}")
