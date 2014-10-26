import os.path

from django.core.urlresolvers import resolve
from django.contrib.auth.models import AnonymousUser
from django.test.client import RequestFactory
from django.contrib.auth import get_user_model

from mygpo.utils import random_token


def create_auth_string(username, password):
    import base64
    credentials = base64.encodestring("%s:%s" % (username, password)).rstrip()
    auth_string = 'Basic %s' % credentials
    return auth_string


def anon_request(url):
    """ Emulates an anonymous request, returns the response

    """
    factory = RequestFactory()
    request = factory.get(url)
    request.user = AnonymousUser()
    view = resolve(url)

    response = view.func(request, *view.args, **view.kwargs)
    return response


def create_user():
    """ Create a user with random data """
    User = get_user_model()
    password = random_token(10)
    username = random_token(8)
    user = User(username=username, email=username + '@example.com')
    user.set_password(password)
    user.is_active = True
    user.save()
    return user, password
