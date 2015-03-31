# -*- coding: utf-8 -*-
#
# gPodder - A media aggregator and podcast client
# Copyright (c) 2005-2009 Thomas Perl and the gPodder Team
#
# gPodder is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# gPodder is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from functools import wraps

from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden, HttpResponseNotAllowed
from django.contrib.auth import get_user_model

import logging
logger = logging.getLogger(__name__)


def requires_token(token_name):
    """
    returns a decorator that checks if the security token in the 'token' GET
    parameter matches the requires token for the resource. The protected
    resource is indicated by
    * the username parameter passed to the decorated function
    * token_name passed to this method

    The decorated method is returned, if
    * no token is required for the resource
    * the token in the 'token' GET parameter matches the required token

    If the passed token does not match HttpResponseForbidden is returned
    """
    def decorator(fn):
        @wraps(fn)
        def tmp(request, username, *args, **kwargs):

            User = get_user_model()
            user = get_object_or_404(User, username=username)
            token = user.profile.get_token(token_name)
            u_token = request.GET.get('token', '')

            if token == '' or token == u_token:
                return fn(request, username, *args, **kwargs)

            else:
                return HttpResponseForbidden()

        return tmp
    return decorator


def allowed_methods(methods):
    def decorator(fn):
        @wraps(fn)
        def tmp(request, *args, **kwargs):
            if request.method in methods:
                return fn(request, *args, **kwargs)
            else:
                return HttpResponseNotAllowed(methods)

        return tmp

    return decorator


def query_if_required():
    """ If required, queries some resource before calling the function

    The decorated method is expected to be bound and its class is
    expected to have define the methods _needs_query() and _query().
    """

    def decorator(f):
        @wraps(f)
        def wrapper(self, *args, **kwargs):

            if self._needs_query():
                self._query()

            return f(self, *args, **kwargs)

        return wrapper
    return decorator


def cors_origin(allowed_origin='*'):
    """ Adds an Access-Control-Allow-Origin header to the response """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            resp = f(*args, **kwargs)
            resp['Access-Control-Allow-Origin'] = allowed_origin
            return resp

        return wrapper
    return decorator
