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
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from mygpo.api.basic_auth import require_valid_user, check_username
from mygpo.api import APIEndpoint


class LoginEndpoint(APIEndpoint):
    """ authenticates the user with regular http basic auth """

    @method_decorator(require_valid_user)
    @method_decorator(check_username)
    @method_decorator(never_cache)
    def post(self, request, username):
        request.session.set_expiry(datetime.utcnow()+timedelta(days=365))
        return HttpResponse()


class LogoutEndpoint(APIEndpoint):
    """ logs out the user. does nothing if he wasn't logged in """

    @method_decorator(check_username)
    @method_decorator(never_cache)
    def post(self, request, username):
        auth.logout(request)
        return HttpResponse()
