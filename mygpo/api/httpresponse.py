import json

from django.http import HttpResponse


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
