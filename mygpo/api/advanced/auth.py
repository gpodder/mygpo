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

from django.contrib.auth.models import User
from mygpo.api.basic_auth import require_valid_user, check_username
from django.contrib import auth
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, Http404
from mygpo.api.httpresponse import JsonResponse
from mygpo.web.models import SecurityToken
from django.shortcuts import get_object_or_404
from mygpo.api.models import Device
from django.utils.translation import ugettext as _
from datetime import datetime, timedelta
from mygpo.log import log
import random
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_valid_user
@check_username
def login(request, username, device_uid):
    """
    authenticates the user with regular http basic auth
    the device is created if it doesn't already exist
    """

    d, created = Device.objects.get_or_create(user=request.user, uid=device_uid, defaults = {'type': 'other', 'name': _('New Device')})

    request.session['device'] = device_uid
    request.session.set_expiry(datetime.now()+timedelta(days=365))

    # the user has been logged in at this point already
    r = {'valid': True}
    return JsonResponse(r)


@csrf_exempt
@check_username
def logout(request, username, device_uid):
    """
    logs out the user. does nothing if he wasn't logged in
    """
    auth.logout(request)

    return HttpResponse()


@csrf_exempt
def validate(request, username, device_uid):
    """
    checks if the client has been authenticated for the given useru
    """
    if not request.user.is_authenticated():
        return JsonResponse({'valid': False, 'reason': 'Client not authenticated'})

    if request.user.username != username:
        return JsonResponse({'valid': False, 'reason': 'Client authenticated for different username: %s' % request.user.username})

    get_object_or_404(Device, user=request.user, uid=device_uid)

    # skip if client isn't authenticated for any device
    if request.session['device'] and (device_uid != request.session['device']):
        return JsonResponse({'valid': False, 'reason': 'Client authenticated for different device: %s' % request.session['device']})

    return JsonResponse({'valid': True})


