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
from django.core.serializers import json, serialize
from django.db.models.query import QuerySet
from django.core.serializers.json import DjangoJSONEncoder
try:
    #try to import the JSON module (if we are on Python 2.6)
    import json
except ImportError:
    # No JSON module available - fallback to simplejson (Python < 2.6)
    import simplejson as json


def HttpResponseNotAuthorized():
    response =  HttpResponse(('You\'re not authorized to visit this area!'), mimetype="text/plain")
    response['WWW-Authenticate'] = 'Basic realm=""'
    response.status_code = 401
    return response

#from http://www.djangosnippets.org/snippets/154/
class JsonResponse(HttpResponse):
    def __init__(self, object):
        if isinstance(object, QuerySet):
            content = serialize('json', object)
        else:
            content = json.dumps(
                object, indent=2, cls=DjangoJSONEncoder,
                ensure_ascii=False)
        super(JsonResponse, self).__init__(
            content, content_type='application/json')

