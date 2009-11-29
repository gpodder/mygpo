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

from mygpo.api.basic_auth import require_valid_user
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, Http404
from mygpo.api.models import Device
from mygpo.api.json import JsonResponse
from django.core import serializers

@require_valid_user()
def subscriptions(request, username, device_uid):
    
    if request.user.username != username:
        return HttpResponseForbidden()


@require_valid_user()
def episodes(request, username):
    pass


@require_valid_user()
def device(request, username, device_uid):
    pass


@require_valid_user()
def devices(request, username):
    pass

