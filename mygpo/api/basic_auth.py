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

from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth import authenticate

from mygpo.log import log
from mygpo.decorators import repeat_on_conflict


@repeat_on_conflict(['user'])
def login(request, user):
    from django.contrib.auth import login
    login(request, user)



#############################################################################
#
def view_or_basicauth(view, request, test_func, realm = "", *args, **kwargs):
    """
    This is a helper function used by both 'require_valid_user' and
    'has_perm_or_basicauth' that does the nitty of determining if they
    are already logged in or if they have provided proper http-authorization
    and returning the view if all goes well, otherwise responding with a 401.
    """
    if test_func(request.user):
        # Already logged in, just return the view.
        return view(request, *args, **kwargs)

    # They are not logged in. See if they provided login credentials

    # the AUTHORIZATION header is used when passing auth-headers
    # from Aapache to fcgi
    auth = None
    for h in ('AUTHORIZATION', 'HTTP_AUTHORIZATION'):
        auth = request.META.get(h, auth)

    if not auth:
        return auth_request()


    auth = auth.split(None, 1)

    if len(auth) == 2:
        auth_type, credentials = auth

        # NOTE: We are only support basic authentication for now.
        if auth_type.lower() == 'basic':
            try:
                credentials = credentials.decode('base64').split(':', 1)

            except UnicodeDecodeError as e:
                return HttpResponseBadRequest(
                    'Could not decode credentials: {msg}'.format(msg=str(e)))

            if len(credentials) == 2:
                uname, passwd = credentials
                user = authenticate(username=uname, password=passwd)
                if user is not None and user.is_active:
                    login(request, user=user)
                    request.user = user

                    return view(request, *args, **kwargs)

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
def require_valid_user(protected_view):
    """
    A simple decorator that requires a user to be logged in. If they are not
    logged in the request is examined for a 'authorization' header.

    If the header is present it is tested for basic authentication and
    the user is logged in with the provided credentials.

    If the header is not present a http 401 is sent back to the
    requestor to provide credentials.

    The purpose of this is that in several django projects I have needed
    several specific views that need to support basic authentication, yet the
    web site as a whole used django's provided authentication.

    The uses for this are for urls that are access programmatically such as
    by rss feed readers, yet the view requires a user to be logged in. Many rss
    readers support supplying the authentication credentials via http basic
    auth (and they do NOT support a redirect to a form where they post a
    username/password.)

    XXX: Fix usage descriptions, ideally provide an example as doctest.
    """
    @wraps(protected_view)
    def wrapper(request, *args, **kwargs):
        def check_valid_user(user):
            return user.is_authenticated()

        return view_or_basicauth(protected_view, \
                                 request, \
                                 check_valid_user, \
                                 '', \
                                 *args, \
                                 **kwargs)
    return wrapper


def check_username(protected_view):
    """
    decorator to check whether the username passed to the view (from the URL)
    matches the username with which the user is authenticated.
    """
    @wraps(protected_view)
    def wrapper(request, username, *args, **kwargs):

        if request.user.username.lower() == username.lower():
            return protected_view(request, *args, username=username, **kwargs)

        else:
            log('username in authentication (%s) and in requested resource (%s) don\'t match' % (request.user.username, username))
            return HttpResponseBadRequest('username in authentication (%s) and in requested resource (%s) don\'t match' % (request.user.username, username))

    return wrapper


#############################################################################
#
def has_perm_or_basicauth(perm, realm = ""):
    """
    This is similar to the above decorator 'logged_in_or_basicauth'
    except that it requires the logged in user to have a specific
    permission.

    Use:

    @logged_in_or_basicauth('asforums.view_forumcollection')
    def your_view:
        ...

    """
    def view_decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            return view_or_basicauth(func, request,
                                     lambda u: u.has_perm(perm),
                                     realm, *args, **kwargs)
        return wrapper
    return view_decorator

