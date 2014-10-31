

from django.conf import settings

from celery import Celery

celery = Celery('mygpo.celery')
celery.config_from_object('django.conf:settings')
celery.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
