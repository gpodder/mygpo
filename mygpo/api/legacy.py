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

from django.http import HttpResponse
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache

from mygpo.users.models import User
from mygpo.api.opml import Importer, Exporter
from mygpo.core.models import Podcast, SubscriptionException
from mygpo.api.backend import get_device
from mygpo.db.couchdb.podcast import podcast_for_url
from mygpo.utils import normalize_feed_url

import logging
logger = logging.getLogger(__name__)


LEGACY_DEVICE_NAME = 'Legacy Device'
LEGACY_DEVICE_UID  = 'legacy'

@never_cache
@csrf_exempt
def upload(request):
    try:
        emailaddr = request.POST['username']
        password  = request.POST['password']
        action    = request.POST['action']
        protocol  = request.POST['protocol']
        opml      = request.FILES['opml'].read()
    except MultiValueDictKeyError:
        return HttpResponse("@PROTOERROR", mimetype='text/plain')

    user = auth(emailaddr, password)
    if (not user):
        return HttpResponse('@AUTHFAIL', mimetype='text/plain')

    dev = get_device(user, LEGACY_DEVICE_UID,
            request.META.get('HTTP_USER_AGENT', ''))

    existing_urls = [x.url for x in dev.get_subscribed_podcasts()]

    i = Importer(opml)

    podcast_urls = [p['url'] for p in i.items]
    podcast_urls = map(normalize_feed_url, podcast_urls)
    podcast_urls = filter(None, podcast_urls)

    new = [u for u in podcast_urls if u not in existing_urls]
    rem = [u for e in existing_urls if u not in podcast_urls]

    #remove duplicates
    new = list(set(new))
    rem = list(set(rem))

    for n in new:
        p = podcast_for_url(n, create=True)

        try:
            p.subscribe(user, dev)
        except SubscriptionException as e:
            logger.exception('Legacy API: %(username)s: could not subscribe to podcast %(podcast_url)s on device %(device_id)s' %
                {'username': user.username, 'podcast_url': p.url, 'device_id': dev.id})

    for r in rem:
        p = podcast_for_url(r, create=True)
        try:
            p.unsubscribe(user, dev)
        except SubscriptionException as e:
            logger.exception('Legacy API: %(username): could not unsubscribe from podcast %(podcast_url) on device %(device_id)' %
                {'username': user.username, 'podcast_url': p.url, 'device_id': dev.id})

    return HttpResponse('@SUCCESS', mimetype='text/plain')

@never_cache
@csrf_exempt
def getlist(request):
    emailaddr = request.GET.get('username', None)
    password = request.GET.get('password', None)

    user = auth(emailaddr, password)
    if user is None:
        return HttpResponse('@AUTHFAIL', mimetype='text/plain')

    dev = get_device(user, LEGACY_DEVICE_UID,
            request.META.get('HTTP_USER_AGENT', ''),
            undelete=True)
    podcasts = dev.get_subscribed_podcasts()

    title = "{username}'s subscriptions".format(username=user.username)
    exporter = Exporter(title)

    opml = exporter.generate(podcasts)

    return HttpResponse(opml, mimetype='text/xml')


def auth(emailaddr, password):
    if emailaddr is None or password is None:
        return None

    user = User.get_user_by_email(emailaddr)
    if not user:
        return None

    if not user.check_password(password):
        return None

    if not user.is_active:
        return None

    return user
