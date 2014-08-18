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

from datetime import datetime

from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from django.shortcuts import get_object_or_404

from mygpo.podcasts.models import Podcast
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.backend import get_device
from mygpo.utils import get_timestamp, \
    parse_request_body, normalize_feed_url, intersect
from mygpo.decorators import cors_origin
from mygpo.users.models import Client
from mygpo.core.json import JSONDecodeError
from mygpo.subscriptions import subscribe, unsubscribe, get_subscription_history, subscription_diff
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

        except Client.DoesNotExist as e:
            return HttpResponseNotFound(str(e))

        except RequestException as e:
            return HttpResponseBadRequest(str(e))

    def parsed_body(self, request):
        """ Returns the object parsed from the JSON request body """

        if not request.body:
            raise RequestException('POST data must not be empty')

        try:
            # TODO: implementation of parse_request_body can be moved here
            # after all views using it have been refactored
            return parse_request_body(request)
        except (JSONDecodeError, UnicodeDecodeError, ValueError) as e:
            msg = u'Could not decode request body for user {}: {}'.format(
                username, request.body.decode('ascii', errors='replace'))
            logger.warn(msg, exc_info=True)
            raise RequestException(msg)

    def get_since(self, request):
        """ Returns parsed "since" GET parameter """
        since_ = request.GET.get('since', None)

        if since_ is None:
            raise RequestException("parameter 'since' missing")

        try:
            since = datetime.fromtimestamp(int(since_))
        except ValueError:
            raise RequestException("'since' is not a valid timestamp")

        if since_ < 0:
            raise RequestException("'since' must be a non-negative number")

        return since


class SubscriptionsAPI(APIView):
    """ API for sending and retrieving podcast subscription updates """

    def get(self, request, version, username, device_uid):
        """ Client retrieves subscription updates """
        now = datetime.utcnow()
        user = request.user
        device = get_object_or_404(Client, user=user, uid=device_uid)
        since = self.get_since(request)
        add, rem, until = self.get_changes(user, device, since, now)
        return JsonResponse({
            'add': add,
            'remove': rem,
            'timestamp': until
        })

    def post(self, request, version, username, device_uid):
        """ Client sends subscription updates """
        now = get_timestamp(datetime.utcnow())

        d = get_device(request.user, device_uid,
                       request.META.get('HTTP_USER_AGENT', ''))

        actions = self.parsed_body(request)

        add = filter(None, actions.get('add', []))
        rem = filter(None, actions.get('remove', []))

        update_urls = self.update_subscriptions(request.user, d, add, rem)

        return JsonResponse({
            'timestamp': now,
            'update_urls': update_urls,
        })

    def update_subscriptions(self, user, device, add, remove):

        conflicts = intersect(add, remove)
        if conflicts:
            msg = "can not add and remove '{}' at the same time".format(
                str(conflicts))
            raise RequestException(msg)

        add_s = map(normalize_feed_url, add)
        rem_s = map(normalize_feed_url, remove)

        assert len(add) == len(add_s) and len(remove) == len(rem_s)

        pairs = zip(add + remove, add_s + rem_s)
        updated_urls = filter(lambda (a, b): a != b, pairs)

        add_s = filter(None, add_s)
        rem_s = filter(None, rem_s)

        # If two different URLs (in add and remove) have
        # been sanitized to the same, we ignore the removal
        rem_s = filter(lambda x: x not in add_s, rem_s)

        for add_url in add_s:
            podcast = Podcast.objects.get_or_create_for_url(add_url)
            subscribe(podcast, user, device, add_url)

        remove_podcasts = Podcast.objects.filter(urls__url__in=rem_s)
        for podcast in remove_podcasts:
            unsubscribe(podcast, user, device)

        return updated_urls

    def get_changes(self, user, device, since, until):
        """ Returns subscription changes for the given device """
        history = get_subscription_history(user, device, since, until)
        add, rem = subscription_diff(history)
        until_ = get_timestamp(until)

        # TODO: we'd need to get the ref_urls here somehow
        add_urls = [p.url for p in add]
        rem_urls = [p.url for p in rem]
        return (add_urls, rem_urls, until_)
