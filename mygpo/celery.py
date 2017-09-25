import os

from django.conf import settings

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygpo.settings')

celery = Celery('mygpo.celery')
celery.config_from_object('django.conf:settings', namespace='CELERY')
celery.autodiscover_tasks()
