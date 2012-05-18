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


from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View

from mygpo.json import json, JSONDecodeError
from mygpo.users.models import DeviceDoesNotExist
from mygpo.api.exceptions import APIParameterException



class APIEndpoint(View):

    @csrf_exempt
    def dispatch(self, *args, **kwargs):

        try:
            return super(APIEndpoint, self).dispatch(*args, **kwargs)

        except APIParameterException as ex:
            return HttpResponseBadRequest(str(ex))

        except DeviceDoesNotExist as ex:
            return HttpResponseNotFound(str(e))


    def get_post_data(self, request):
        """ parses body data """

        if not request.raw_post_data:
            raise APIParameterException('POST data must not be empty')

        try:
            return json.loads(request.raw_post_data)

        except (JSONDecodeError, UnicodeDecodeError) as ex:
            msg = 'could not decode POST data: {ex}'.format(ex=ex)
            raise APIParameterException(msg)
