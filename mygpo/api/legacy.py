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
from django.contrib.auth import get_user_model

from mygpo.podcasts.models import Podcast
from mygpo.api.opml import Importer, Exporter
from mygpo.users.models import SubscriptionException
from mygpo.api.backend import get_device
from mygpo.utils import normalize_feed_url
from mygpo.subscriptions import subscribe, unsubscribe

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
        return HttpResponse("@PROTOERROR", content_type='text/plain')

    user = auth(emailaddr, password)
    if (not user):
        return HttpResponse('@AUTHFAIL', content_type='text/plain')

    dev = get_device(user, LEGACY_DEVICE_UID,
            request.META.get('HTTP_USER_AGENT', ''))

    existing_urls = [x.url for x in dev.get_subscribed_podcasts()]

    i = Importer(opml)

    podcast_urls = [p['url'] for p in i.items]
    podcast_urls = map(normalize_feed_url, podcast_urls)
    podcast_urls = list(filter(None, podcast_urls))

    new = [u for u in podcast_urls if u not in existing_urls]
    rem = [u for u in existing_urls if u not in podcast_urls]

    #remove duplicates
    new = list(set(new))
    rem = list(set(rem))

    for n in new:
        p = Podcast.objects.get_or_create_for_url(n)
        subscribe(p, user, dev)

    for r in rem:
        p = Podcast.objects.get_or_create_for_url(r)
        unsubscribe(p, user, dev)

    return HttpResponse('@SUCCESS', content_type='text/plain')

@never_cache
@csrf_exempt
def getlist(request):
    emailaddr = request.GET.get('username', None)
    password = request.GET.get('password', None)

    user = auth(emailaddr, password)
    if user is None:
        return HttpResponse('@AUTHFAIL', content_type='text/plain')

    dev = get_device(user, LEGACY_DEVICE_UID,
            request.META.get('HTTP_USER_AGENT', ''),
            undelete=True)
    podcasts = dev.get_subscribed_podcasts()

    title = "{username}'s subscriptions".format(username=user.username)
    exporter = Exporter(title)

    opml = exporter.generate(podcasts)

    return HttpResponse(opml, content_type='text/xml')


def auth(emailaddr, password):
    if emailaddr is None or password is None:
        return None

    User = get_user_model()
    try:
        user = User.objects.get(email=emailaddr)
    except User.DoesNotExist:
        return None

    if not user.check_password(password):
        return None

    if not user.is_active:
        return None

    return user
