import os.path

from django.core.urlresolvers import resolve
from django.contrib.auth.models import AnonymousUser
from django.test.client import RequestFactory


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
