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

from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseForbidden, HttpResponseNotAllowed
import gc

def requires_token(token_name, denied_template=None):
    """
    returns a decorator that checks if the security token in the 'token' GET
    parameter matches the requires token for the resource. The protected
    resource is indicated by
    * the username parameter passed to the decorated function
    * token_name passed to this method

    The decorated method is returned, if
    * no token is required for the resource
    * the token in the 'token' GET parameter matches the required token

    If the passed token does not match
    * the denied_template is rendered and returned if given
    * HttpResponseForbidden is returned, if denied_template is not given
    """
    def decorator(fn):
        def tmp(request, username, *args, **kwargs):

            from mygpo.users.models import User
            user = User.get_user(username)
            if not user:
                raise Http404

            token = getattr(user, token_name, '')
            u_token = request.GET.get('token', '')

            if token == '' or token == u_token:
                return fn(request, username, *args, **kwargs)

            else:
                if denied_template:
                    return render_to_response(denied_template, {
                        'other_user': user
                        }, context_instance=RequestContext(request))

                else:
                    return HttpResponseForbidden()

        return tmp
    return decorator


def allowed_methods(methods):
    def decorator(fn):
        def tmp(request, *args, **kwargs):
            if request.method in methods:
                return fn(request, *args, **kwargs)
            else:
                return HttpResponseNotAllowed(methods)

        return tmp

    return decorator


def repeat_on_conflict(obj_names=[], reload_f=None):
    """
    In case of a CouchDB ResourceConflict, reloads the parameter with the
    given name and repeats the function call until it succeeds.
    When calling the function, the parameter that should be reloaded must be
    given as a keyword-argument
    """
    from couchdbkit import ResourceConflict

    def default_reload(obj):
        return obj.__class__.get(obj._id)

    reload_f = reload_f or default_reload

    def decorator(f):
        def tmp(*args, **kwargs):
            while True:
                try:
                    return f(*args, **kwargs)
                    break
                except ResourceConflict:
                    for obj_name in obj_names:
                        obj = kwargs[obj_name]
                        kwargs[obj_name] = reload_f(obj)

        return tmp

    return decorator


def query_if_required():
    """ If required, queries some resource before calling the function

    The decorated method is expected to be bound and its class is
    expected to have define the methods _needs_query() and _query().
    """

    def decorator(f):
        def wrapper(self, *args, **kwargs):

            if self._needs_query():
                self._query()

            return f(self, *args, **kwargs)

        return wrapper
    return decorator
