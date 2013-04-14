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
import inspect

from couchdbkit import ResourceConflict

from django.http import Http404
from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponseNotAllowed


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
        @wraps(fn)
        def tmp(request, username, *args, **kwargs):

            from mygpo.users.models import User
            user = User.get_user(username)
            if not user:
                raise Http404

            token = user.get_token(token_name)
            u_token = request.GET.get('token', '')

            if token == '' or token == u_token:
                return fn(request, username, *args, **kwargs)

            else:
                if denied_template:
                    return render(request, denied_template, {
                        'other_user': user
                    })

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


class repeat_on_conflict(object):
    """ Repeats an update operation in case of a ResourceConflict

    In case of a CouchDB ResourceConflict, reloads the parameter with the given
    name and repeats the function call until it succeeds.  When calling the
    function, the parameter that should be reloaded must be given as a
    keyword-argument """

    ARGSPEC = '__repeat_argspec__'

    def __init__(self, obj_names=[], reload_f=None):
        self.obj_names = obj_names
        self.reload_f = reload_f or self.default_reload

    def default_reload(self, obj):
        return obj.__class__.get(obj._id)

    def build_locals(self, f, args, kwargs):
        argspec = getattr(f, self.ARGSPEC)
        if len(args) > len(argspec.args):
            varargs = args[len(args):]
            args = args[:len(args)]
        else:
            varargs = []
        locals = dict(zip(argspec.args, args))
        if argspec.varargs is not None:
            locals.update({argspec.varargs: varargs})
        if argspec.keywords is not None:
            locals.update({argspec.keywords: kwargs})
        locals.update(kwargs)
        return locals

    def __call__(self, f):

        if not hasattr(f, self.ARGSPEC):
            argspec = inspect.getargspec(f)
            setattr(f, self.ARGSPEC, argspec)

        @wraps(f)
        def wrapper(*args, **kwargs):
            all_args = before = self.build_locals(f, args, kwargs)

            # repeat until operation succeeds
            # TODO: adding an upper bound might make sense
            while True:
                try:
                    return f(**all_args)

                except ResourceConflict:
                    for obj_name in self.obj_names:
                        obj = all_args[obj_name]
                        all_args[obj_name] = self.reload_f(obj)

        return wrapper


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
