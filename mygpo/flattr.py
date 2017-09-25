# -*- coding: utf-8 -*-
#
#  Flattr integration
#  based on flattr.py from gPodder by Bernd Schlapsi <brot@gmx.info>
#

import json
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import urllib.parse
from collections import namedtuple

from django.conf import settings
from django.urls import reverse

from mygpo.users.settings import FLATTR_TOKEN, FLATTR_USERNAME
from mygpo import utils
from django.utils.translation import ugettext as _


class Flattr(object):
    """ a Flattr client """

    # OAuth URLs
    OAUTH_BASE = 'https://flattr.com/oauth'
    AUTH_URL_TEMPLATE = (OAUTH_BASE + '/authorize?scope=flattr&' +
            'response_type=code&client_id=%(client_id)s&' +
            'redirect_uri=%(redirect_uri)s')
    OAUTH_TOKEN_URL = OAUTH_BASE + '/token'

    # REST API URLs
    API_BASE = 'https://api.flattr.com/rest/v2'
    USER_INFO_URL = API_BASE + '/user'
    FLATTR_URL = API_BASE + '/flattr'
    THING_INFO_URL_TEMPLATE = API_BASE + '/things/lookup/?url=%(url)s'


    def __init__(self, user, domain, is_secure):
        self.user = user
        self.domain = domain
        self.is_secure = is_secure


    def _get_callback(self):
        return 'http{s}://{domain}{callback}'.format(
            s='s' if self.is_secure else '',
            domain=self.domain,
            callback=reverse('flattr-token'))


    def request(self, url, data=None):
        headers = {'Content-Type': 'application/json'}

        if url == self.OAUTH_TOKEN_URL:
            # Inject username and password into the request URL
            url = utils.url_add_authentication(url, settings.FLATTR_KEY,
                    settings.FLATTR_SECRET)
        elif self.user.profile.settings.get_setting('flattr_token', ''):
            headers['Authorization'] = 'Bearer ' + self.user.profile.settings.get_wksetting(FLATTR_TOKEN)

        if data is not None:
            data = json.dumps(data).encode('utf-8')

        try:
            response = utils.urlopen(url, headers, data)
        except urllib.error.HTTPError as error:
            return {'_gpodder_statuscode': error.getcode()}
        except urllib.error.URLError as error:
            return {'_gpodder_no_connection': False}

        if response.getcode() == 200:
            return json.loads(response.read().decode('utf-8'))

        return {'_gpodder_statuscode': response.getcode()}

    def get_auth_url(self):
        return self.AUTH_URL_TEMPLATE % {
                'client_id': settings.FLATTR_KEY,
                'redirect_uri': self._get_callback(),
        }

    def has_token(self):
        return bool(self.user.profile.settings.get_wksetting(FLATTR_TOKEN))

    def process_retrieved_code(self, url):
        url_parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(url_parsed.query)

        if 'code' in query:
            code = query['code'][0]
            token = self._request_access_token(code)
            return token

        return False

    def _request_access_token(self, code):
        request_url = 'https://flattr.com/oauth/token'

        params = {
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self._get_callback(),
        }

        content = self.request(self.OAUTH_TOKEN_URL, data=params)
        return content.get('access_token', '')


    def get_thing_info(self, payment_url):
        """Get information about a Thing on Flattr

        Return a tuple (flattrs, flattred):

            flattrs ... The number of Flattrs this thing received
            flattred ... True if this user already flattred this thing
        """
        if not self.user.profile.settings.get_wksetting(FLATTR_TOKEN):
            return (0, False)

        quote_url = urllib.parse.quote_plus(payment_url)
        url = self.THING_INFO_URL_TEMPLATE % {'url': quote_url}
        data = self.request(url)
        return (int(data.get('flattrs', 0)), bool(data.get('flattred', False)))


    def get_auth_username(self):
        if not self.user.profile.settings.get_wksetting(FLATTR_TOKEN):
            return ''

        data = self.request(self.USER_INFO_URL)
        return data.get('username', '')


    def flattr_url(self, payment_url):
        """Flattr an object given its Flattr payment URL

        Returns a tuple (success, message):

            success ... True if the item was Flattr'd
            message ... The success or error message
        """
        params = {
            'url': payment_url
        }

        content = self.request(self.FLATTR_URL, data=params)

        if '_gpodder_statuscode' in content:
            status_code = content['_gpodder_statuscode']
            if status_code == 401:
                return (False, _('Not enough means to flattr'))
            elif status_code == 404:
                return (False, _('Item does not exist on Flattr'))
            elif status_code == 403:
                return (False, _('Already flattred or own item'))
            else:
                return (False, _('Invalid request'))

        if '_gpodder_no_connection' in content:
            return (False, _('No internet connection'))

        return (True, content.get('description', _('No description')))


    def get_autosubmit_url(self, thing):
        """ returns the auto-submit URL for the given FlattrThing """

        publish_username = self.user.profile.settings.get_wksetting(FLATTR_USERNAME)

        if not publish_username:
            return None

        URL_TEMPLATE = 'https://flattr.com/submit/auto?user_id=%s' % (publish_username,)

        if not thing.url:
            raise ValueError('Thing must at least have an url')

        optional_args = set(thing._fields) - set(['url'])

        args = [('url', self.domain + thing.url)]
        args += [(arg, getattr(thing, arg, None)) for arg in optional_args]
        args = filter(lambda kv: kv[1], args)  # filter out empty arguments

        # TODO: check encoding
        args = [(k, v.encode('utf-8')) for (k, v) in args]

        args_str = urllib.parse.urlencode(args)

        autosubmit = URL_TEMPLATE + '&' + args_str

        return autosubmit


# A thing that can be flattred by other Flattr users
FlattrThing = namedtuple('FlattrThing', 'url title description language tags ' +
        'hidden category')
