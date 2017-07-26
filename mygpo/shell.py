#
# This file collects imports that can be useful when doing maintenance stuff
# from the shell.
# You can then just run
#
# from mygpo.shell import *
#
# to get all relevant classes, and an instantiated db object.
#

from django.core.cache import cache

# Auto-import all Models
from django.apps import apps
from django.utils.module_loading import import_string
for m in apps.get_models():
    import_string('{module}.{model}'.format(module=m.__module__,
                                            model=m.__name__))
