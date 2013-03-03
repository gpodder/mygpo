from __future__ import absolute_import

from django.conf import settings

from celery import Celery

import sys
import os


celery = Celery('mygpo.celery',
                broker=settings.BROKER_URL,
                backend=settings.BACKEND_URL,
                include=[
                    'mygpo.core.tasks',
                    'mygpo.users.tasks',
                    'mygpo.data.tasks',
                    'mygpo.admin.tasks',
                    'mygpo.directory.tasks',
                ])

celery.conf.update(
    **settings.CELERY_CONF
)

if __name__ == '__main__':
    celery.start()
