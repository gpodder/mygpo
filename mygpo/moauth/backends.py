import requests

from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

import logging
logger = logging.getLogger(__name__)


class OAuth2Backend(ModelBackend):
    """ OAuth2 authentication backend

    Authenticates based on token info URL; Uses Users from the ModelBackend """

    def authenticate(self, token_info_url=None):
        logger.info('Authenticating user from "%s"', token_info_url)
        if token_info_url is None:
            return

        token = self._get_token_info(token_info_url)
        username = token['user']['login']
        return self._get_user(username)

    def _get_token_info(self, token_info_url):
        """ Retrieves token info and returns the username """

        headers = {
            'Accept': 'application/json'
        }

        r = requests.get(token_info_url, headers=headers)
        token = r.json()
        #{
        #    'token': '62b6a03b16a5453f810cf6d32ac975f8',
        #    'app': {
        #        'url': None,
        #        'name': 'gpodder.net',
        #        'client_id': 'Nb0QLDW2psFSXfGwmCvJ1ElhITu9P3Kg'
        #    },
        #    'created_at': '2016-02-07T12:42:14.140Z',
        #    'user': {
        #        'login': 'stefan'
        #    },
        #    'scopes': [
        #        'actions:add',
        #        'podcastlists'
        #    ]
        #}
        return token

    def _get_user(self, username):
        """ Get user based on username """
        User = get_user_model()
        try:
            return User.objects.create(username=username)
        except IntegrityError as ie:
            return User.objects.get(username__iexact=username)
