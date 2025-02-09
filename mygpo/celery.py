import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygpo.settings")
os.environ.setdefault('DJANGO_CONFIGURATION', 'Prod')

import configurations
configurations.setup()

celery = Celery("mygpo.celery")
celery.config_from_object("django.conf:settings", namespace="CELERY")
celery.autodiscover_tasks()
