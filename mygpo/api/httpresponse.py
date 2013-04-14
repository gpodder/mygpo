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

from django.http import HttpResponse

from mygpo.core.json import json


class JsonResponse(HttpResponse):
    def __init__(self, object, jsonp_padding=None):
        content = json.dumps(object, ensure_ascii=True)

        if jsonp_padding:
            content = '%(func)s(%(obj)s)' % \
                {'func': jsonp_padding, 'obj': content}
            content_type = 'application/json-p'

        else:
            content_type = 'application/json'

        super(JsonResponse, self).__init__(
            content, content_type=content_type)
