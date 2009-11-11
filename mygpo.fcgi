#!/usr/bin/python
# -*- coding: utf-8 -*-
# my.gpodder.org FastCGI handler for lighttpd (default setup)

import sys
import os

# Add this directory as custom Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ['DJANGO_SETTINGS_MODULE'] = 'mygpo.settings'

# Start the FastCGI server for this application
from django.core.servers.fastcgi import runfastcgi
runfastcgi(method='threaded', daemonize='false')

