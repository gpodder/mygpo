#
# This file collects imports that can be useful when doing maintenance stuff
# from the shell.
# You can then just run
#
# from mygpo.shell import *
#
# to get all relevant classes, and an instantiated db object.
#

from mygpo.core.models import *
from mygpo.users.models import *
from mygpo.directory.models import *
from mygpo.share.models import *

from mygpo.db.couchdb import get_main_database

db = get_main_database()

from django.core.cache import cache
