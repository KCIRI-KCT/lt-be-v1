import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lt_be_v1.settings')

app = Celery('lt_be_v1')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()