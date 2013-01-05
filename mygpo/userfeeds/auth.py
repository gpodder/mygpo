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

from functools import wraps

from django.http import HttpResponse, HttpResponseBadRequest, Http404

from mygpo.users.models import User
from mygpo.log import log


#############################################################################
#
def view_or_basicauth(view, request, username, token_name, realm = "", *args, **kwargs):

    user = User.get_user(username)
    if not user:
        raise Http404

    token = getattr(user, token_name, '')

    # check if a token is required at all
    if token == '':
        return view(request, username, *args, **kwargs)

    # this header format is used when passing auth-headers
    # from Aapache to fcgi
    if 'AUTHORIZATION' in request.META:
        auth = request.META['AUTHORIZATION']

    elif 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION']

    else:
        return auth_request()


    auth = auth.split(None, 1)

    if len(auth) == 2:
        auth_type, credentials = auth

        # NOTE: We are only support basic authentication for now.
        if auth_type.lower() == 'basic':
            credentials = credentials.decode('base64').split(':', 1)
            if len(credentials) == 2:

                uname, passwd = credentials

                if uname != username:
                    return auth_request()

                if token == passwd:
                    return view(request, uname, *args, **kwargs)

    return auth_request()


def auth_request(realm=''):
    # Either they did not provide an authorization header or
    # something in the authorization attempt failed. Send a 401
    # back to them to ask them to authenticate.
    response = HttpResponse()
    response.status_code = 401
    response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
    return response


#############################################################################
#
def require_token_auth(token_name):
    def wrapper(protected_view):

        @wraps(protected_view)
        def tmp(request, username, *args, **kwargs):
            return view_or_basicauth(protected_view, \
                                     request, \
                                     username, \
                                     token_name, \
                                     '', \
                                     *args, \
                                     **kwargs)
        return tmp
    return wrapper



