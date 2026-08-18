from django.db import migrations


def seed_demo_camera(apps, schema_editor):
    Site = apps.get_model('LT_AMS_API', 'Site')
    Camera = apps.get_model('LT_AMS_API', 'Camera')

    site = Site.objects.first()
    if site:
        Camera.objects.get_or_create(
            rtsp_url="http://10.1.82.235:8080/feed/0",
            defaults={
                "name": "Demo AI Feed Camera 01",
                "site": site,
                "location": "Main Entrance Gate",
                "status": "ACTIVE",
                "type": "FIXED",
                "resolution": "1080p",
                "health_score": 100.0,
            }
        )


def reverse_seed_demo_camera(apps, schema_editor):
    Camera = apps.get_model('LT_AMS_API', 'Camera')
    Camera.objects.filter(rtsp_url="http://10.1.82.235:8080/feed/0").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('LT_AMS_API', '0002_camera_city_country_aialert_message_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_demo_camera, reverse_seed_demo_camera),
    ]
