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
#

from datetime import datetime, timedelta

from django.contrib import auth
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache

from mygpo.api.basic_auth import require_valid_user, check_username
from mygpo.decorators import allowed_methods


@csrf_exempt
@require_valid_user
@check_username
@allowed_methods(['POST'])
@never_cache
def login(request, username):
    """
    authenticates the user with regular http basic auth
    """

    request.session.set_expiry(datetime.utcnow()+timedelta(days=365))
    return HttpResponse()


@csrf_exempt
@check_username
@allowed_methods(['POST'])
@never_cache
def logout(request, username):
    """
    logs out the user. does nothing if he wasn't logged in
    """

    auth.logout(request)
    return HttpResponse()
