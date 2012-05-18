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

from django.http import HttpResponseBadRequest
from django.db import IntegrityError
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from mygpo.api.sanitizing import sanitize_urls
from mygpo.api.backend import get_device, BulkSubscribe, \
        get_subscription_change_urls
from mygpo.couchdb import BulkException
from mygpo.log import log
from mygpo.utils import get_timestamp
from mygpo.api.basic_auth import require_valid_user, check_username
from mygpo.api.advanced import AdvancedAPIEndpoint



class SubscriptionEndpoint(AdvancedAPIEndpoint):

    @method_decorator(require_valid_user)
    @method_decorator(check_username)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        super(SubscriptionEndpoint, self).dispatch(*args, **kwargs)


    def get(this, request, username, device_uid):

        now = datetime.now()
        now_ = get_timestamp(now)

        device = request.user.get_device_by_uid(device_uid)

        since_ = request.GET.get('since', None)
        if since_ == None:
            raise APIParameterException('parameter since missing')

        try:
            since = datetime.fromtimestamp(float(since_))
        except ValueError:
            raise APIParameterException('since-value is not a valid timestamp')

        add_urls, remove_urls = get_subscription_change_urls(device, since, now)

        until_ = get_timestamp(until)

        changes = {
            'add': add_urls,
            'remove': remove_urls,
            'timestamp': until_,
        }

        return changes


    def post(this, request, username, device_uid):

        now = datetime.now()
        now_ = get_timestamp(now)

        d = get_device(request.user, device_uid,
                request.META.get('HTTP_USER_AGENT', ''))

        actions = self.get_post_data(request)

        add = filter(None, actions.get('add', []))
        rem = filter(None, actions.get('remove', []))

        try:
            update_urls = self.update_subscriptions(request.user, d, add, rem)

        except IntegrityError, e:
            return HttpResponseBadRequest(e)

        return {
            'timestamp': now_,
            'update_urls': update_urls,
            }


    def update_subscriptions(self, user, device, add, remove):

        for a in add:
            if a in remove:
                # TODO: replace integrity error (from django.db)
                raise IntegrityError('can not add and remove %s at the same time' % a)

        add_s = list(sanitize_urls(add, 'podcast'))
        rem_s = list(sanitize_urls(remove, 'podcast'))

        assert len(add) == len(add_s) and len(remove) == len(rem_s)

        updated_urls = filter(lambda (a, b): a != b, zip(add + remove, add_s + rem_s))

        add_s = filter(None, add_s)
        rem_s = filter(None, rem_s)

        # If two different URLs (in add and remove) have
        # been sanitized to the same, we ignore the removal
        rem_s = filter(lambda x: x not in add_s, rem_s)

        subscriber = BulkSubscribe(user, device)

        for a in add_s:
            subscriber.add_action(a, 'subscribe')

        for r in rem_s:
            subscriber.add_action(r, 'unsubscribe')

        try:
            subscriber.execute()
        except BulkException as be:
            for err in be.errors:
                log('Advanced API: %(username)s: Updating subscription for '
                        '%(podcast_url)s on %(device_uid)s failed: '
                        '%(rerror)s (%(reason)s)'.format(username=user.username,
                            podcast_url=err.doc, device_uid=device.uid,
                            error=err.error, reason=err.reason)
                    )

        return updated_urls
