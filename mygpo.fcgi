#!/usr/bin/python
# -*- coding: utf-8 -*-
# my.gpodder.org FastCGI handler for lighttpd (default setup)
#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.


import sys
import os

# Add this directory as custom Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ['DJANGO_SETTINGS_MODULE'] = 'mygpo.settings'

# Start the FastCGI server for this application
from django.core.servers.fastcgi import runfastcgi
runfastcgi(method='threaded', daemonize='false')

