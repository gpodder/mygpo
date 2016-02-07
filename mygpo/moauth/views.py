import requests
from requests.auth import HTTPBasicAuth

import urllib.parse

from django.db import IntegrityError
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.views.generic.base import RedirectView
from django.views.generic.base import View
from django.http import HttpResponseRedirect
from django.contrib.sites.requests import RequestSite
from django.contrib.auth import login, get_user_model, authenticate
from django.conf import settings

from mygpo.utils import random_token
from . import models

import logging
logger = logging.getLogger(__name__)


AVAILABLE_SCOPES = [
    'subscriptions',
    'suggestions',
    'account',
    'favorites',
    'podcastlists',
    'apps:get',
    'apps:sync',
    'actions:get',
    'actions:add',
]

class InitiateOAuthLogin(RedirectView):

    def get_redirect_url(self):

        client_id = settings.MYGPO_AUTH_CLIENT_ID
        redir_uri = self._get_callback_url()
        state = random_token()
        response_type = 'code'

        models.AuthRequest.objects.create(
            scopes = AVAILABLE_SCOPES,
            state = state,
        )
        logger.info('Initiated new new auth request "%s"', state)

        scopes = AVAILABLE_SCOPES
        qs = self._get_qs(client_id, redir_uri, scopes, state, response_type)
        return _get_authorize_url('/authorize', qs)

    def _get_qs(self, client_id, redirect_uri, scopes, state, response_type):
        return urllib.parse.urlencode([
            ('client_id', client_id),
            ('redirect_uri', redirect_uri),
            ('scope', ' '.join(scopes)),
            ('state', state),
            ('response_type', response_type),
        ])

    def _get_callback_url(self):
        protocol = 'https' if self.request.is_secure() else 'http'
        site = RequestSite(self.request)
        domain = site.domain
        view = reverse('oauth-callback')
        return '{0}://{1}{2}'.format(protocol, domain, view)


class OAuthCallback(View):
    """ OAuth 2 callback handler

    Gets and verifies token, logs in user """

    def get(self, request):

        if 'error' in self.request.GET:
            # handle error
            # error=server_error&error_description=An+unknown+error+occured
            return

        code = self.request.GET.get('code', None)
        state = self.request.GET.get('state', None)

        try:
            authreq = models.AuthRequest.objects.get(state=state)
        except models.AuthRequest.DoesNotExist:
            # handle
            return

        access_token, token_info_url = self._get_access_token(code)

        user = authenticate(token_info_url=token_info_url)
        login(self.request, user)

        return HttpResponseRedirect(reverse('home'))

    def _get_access_token(self, code):
        payload = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': settings.MYGPO_AUTH_CLIENT_ID,
        }
        auth = HTTPBasicAuth(settings.MYGPO_AUTH_CLIENT_ID,
                             settings.MYGPO_AUTH_CLIENT_SECRET)

        qs = self._get_qs(AVAILABLE_SCOPES)
        token_url = _get_authorize_url('/token', qs)
        r = requests.post(token_url, data=payload, auth=auth)
        if r.status_code != 200:
            return # handle error

        resp = r.json()
        access_token = resp['access_token']
        expires_in = resp['expires_in']
        token_type = resp['token_type']
        scopes = resp['scope'].split(' ')
        #{
        #    'expires_in': 3599.995724,
        #    'access_token': 'a46de116972b46e88481e7a082db60ca',
        #    'token_type': 'Bearer',
        #    'scope': 'podcastlists subscriptions suggestions apps:get actions:get account actions:add apps:sync favorites'
        #}
        logger.info(
            'Received %s token "%s" for scopes "%s", expires in %f',
            token_type, access_token, ' '.join(scopes), expires_in
        )

        token_info = r.links['https://gpodder.net/relation/token-info']['url']

        # Reference Resolution
        # https://tools.ietf.org/html/rfc3986#section-5
        token_info_url = urllib.parse.urljoin(settings.MYGPO_AUTH_URL,
                                              token_info)

        return access_token, token_info_url

        login(self.request, user)


    def _get_qs(self, scopes):
        return urllib.parse.urlencode([
            ('scope', ' '.join(scopes)),
        ])


def _get_authorize_url(endpoint, qs):
    r = urllib.parse.urlsplit(settings.MYGPO_AUTH_URL)
    path = r.path
    if path.endswith('/'):
        path = path[:-1]

    path = path + endpoint
    parts = (r.scheme, r.netloc, path, qs, r.fragment)
    return urllib.parse.urlunsplit(parts)
