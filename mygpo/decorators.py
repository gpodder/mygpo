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

from django.shortcuts import render_to_response
from django.template import RequestContext
from mygpo.web.models import SecurityToken
from django.contrib.auth.models import User
from django.http import Http404, HttpResponseForbidden
import random
import string
import gc

def requires_token(object, action, denied_template=None):
    """
    returns a decorator that checks if the security token in the 'token' GET
    parameter matches the requires token for the resource. The resource is indicated by
    * the username parameter passed to the decorated function
    * object and action passed to this method

    The decorated method is returned, if
    * no token is required for the resource
    * the token in the 'token' GET parameter matches the required token

    If the passed token does not match
    * the denied_template is rendered and returned if given
    * HttpResponseForbidden is returned, if denied_template is not given
    """
    def decorator(fn):
        def tmp(request, username, *args, **kwargs):

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return lambda: Http404

            token, c = SecurityToken.objects.get_or_create(user=user, object=object, action=action,
                        defaults = {'token': "".join(random.sample(string.letters+string.digits, 32))})

            u_token = request.GET.get('token', '')

            if token.token == '' or token.token == u_token:
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


def manual_gc(view):
    def tmp(*args, **kwargs):
        res = view(*args, **kwargs)
        gc.collect()
        return res

    return tmp

