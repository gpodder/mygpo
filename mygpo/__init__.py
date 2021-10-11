# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from mygpo.celery import celery as celery_app

__all__ = ('celery_app',)
