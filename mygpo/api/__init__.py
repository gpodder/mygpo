from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.views import View

from mygpo.utils import parse_request_body
from mygpo.api.exceptions import ParameterMissing
from mygpo.decorators import cors_origin
from mygpo.api.basic_auth import require_valid_user, check_username


import logging

logger = logging.getLogger(__name__)


class RequestException(Exception):
    """ Raised if the request is malfored or otherwise invalid """


class APIView(View):
    @method_decorator(csrf_exempt)
    @method_decorator(require_valid_user)
    @method_decorator(check_username)
    @method_decorator(never_cache)
    @method_decorator(cors_origin())
    def dispatch(self, *args, **kwargs):
        """ Dispatches request and does generic error handling """
        try:
            return super(APIView, self).dispatch(*args, **kwargs)

        except ObjectDoesNotExist as e:
            return HttpResponseNotFound(str(e))

        except (RequestException, ParameterMissing) as e:
            return HttpResponseBadRequest(str(e))

    def parsed_body(self, request):
        """ Returns the object parsed from the JSON request body """

        if not request.body:
            raise RequestException('POST data must not be empty')

        try:
            # TODO: implementation of parse_request_body can be moved here
            # after all views using it have been refactored
            return parse_request_body(request)
        except (UnicodeDecodeError, ValueError) as e:
            msg = 'Could not decode request body for user {}: {}'.format(
                request.user.username, request.body.decode('ascii', errors='replace')
            )
            logger.warning(msg, exc_info=True)
            raise RequestException(msg)

    def get_since(self, request):
        """ Returns parsed "since" GET parameter """
        since_ = request.GET.get('since', None)

        if since_ is None:
            raise RequestException("parameter 'since' missing")

        try:
            since_ = int(since_)
            since = datetime.fromtimestamp(since_)
        except ValueError:
            raise RequestException("'since' is not a valid timestamp")

        if since_ < 0:
            raise RequestException("'since' must be a non-negative number")

        return since
