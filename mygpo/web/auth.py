from django.contrib.auth.backends import ModelBackend
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.sites.requests import RequestSite
from django.contrib.auth import get_user_model
from django.urls import reverse


class EmailAuthenticationBackend(ModelBackend):
    """ Auth backend to enable login with email address as username """

    def authenticate(self, request, username=None, password=None):
        try:
            validate_email(username)

            User = get_user_model()
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None

            return user if user.check_password(password) else None

        except ValidationError:
            return None


def get_google_oauth_flow(request):
    """ Prepare an OAuth 2.0 flow

    https://developers.google.com/api-client-library/python/guide/aaa_oauth """

    from oauth2client.client import OAuth2WebServerFlow

    site = RequestSite(request)

    callback = 'http{s}://{domain}{callback}'.format(
        s='s' if request.is_secure() else '',
        domain=site.domain,
        callback=reverse('login-google-callback'))

    flow = OAuth2WebServerFlow(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scope='https://www.googleapis.com/auth/userinfo.email',
        redirect_uri=callback)

    return flow
