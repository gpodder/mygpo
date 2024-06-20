#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygpo.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
