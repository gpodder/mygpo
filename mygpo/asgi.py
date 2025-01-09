"""
ASGI config for mygpo project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/asgi/
"""

import os

from configurations.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygpo.settings")
os.environ.setdefault('DJANGO_CONFIGURATION', 'Prod')

application = get_asgi_application()
