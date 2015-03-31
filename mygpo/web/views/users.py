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

import string
import random

from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.sites.models import RequestSite
from django.conf import settings
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from django.template.loader import render_to_string
from django.views.generic.base import View, TemplateView
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.utils.http import is_safe_url

from oauth2client.client import FlowExchangeError

from mygpo.decorators import allowed_methods
from mygpo.web.forms import RestorePasswordForm
from mygpo.web.forms import ResendActivationForm
from mygpo.constants import DEFAULT_LOGIN_REDIRECT
from mygpo.web.auth import get_google_oauth_flow
from mygpo.users.models import UserProxy
from mygpo.users.views.registration import send_activation_email
from mygpo.utils import random_token
from mygpo.api import APIView

import logging
logger = logging.getLogger(__name__)


def login(request, user):
    from django.contrib.auth import login
    login(request, user)


class LoginView(View):
    """ View to login a user """

    @method_decorator(never_cache)
    def post(self, request):
        """ Carries out the login, redirects to get if it fails """

        # redirect target on successful login
        next_page = request.POST.get('next', '')

        # redirect target on failed login
        login_page = '{page}?next={next_page}'.format(page=reverse('login'),
                next_page=next_page)


        username = request.POST.get('user', None)
        if not username:
            messages.error(request, _('Username missing'))
            return HttpResponseRedirect(login_page)

        password = request.POST.get('pwd', None)
        if not password:
            messages.error(request, _('Password missing'))
            return HttpResponseRedirect(login_page)

        # find the user from the configured login systems, and verify pwd
        user = authenticate(username=username, password=password)

        if not user:
            messages.error(request, _('Wrong username or password.'))
            return HttpResponseRedirect(login_page)


        if not user.is_active:
            send_activation_email(user, request)
            messages.error(request, _('Please activate your account first. '
                'We have just re-sent your activation email'))
            return HttpResponseRedirect(login_page)

        # set up the user's session
        login(request, user)

        if next_page:
            if is_safe_url(next_page):
                return HttpResponseRedirect(next_page)

            else:
                # TODO: log a warning that next_page is not
                # considered a safe redirect target
                pass

        return HttpResponseRedirect(DEFAULT_LOGIN_REDIRECT)


class RestorePassword(APIView):

    def post(self, request):

        form = RestorePasswordForm(request.POST)
        if not form.is_valid():
            return HttpResponseRedirect('/login/')

        user = UserProxy.objects.all().by_username_or_email(
                form.cleaned_data['username'],
                form.cleaned_data['email']
            )

        if not user.is_active:
            send_activation_email(user, request)
            messages.error(request, _('Please activate your account first. '
                'We have just re-sent your activation email'))
            return HttpResponseRedirect(reverse('login'))

        site = RequestSite(request)
        pwd = random_token(length=16)
        user.set_password(pwd)
        user.save()
        subject = render_to_string('reset-pwd-subj.txt', {'site': site}).strip()
        message = render_to_string('reset-pwd-msg.txt', {
            'username': user.username,
            'site': site,
            'password': pwd,
        })
        user.email_user(subject, message)


class GoogleLogin(View):
    """ Redirects to Google Authentication page """

    def get(self, request):
        flow = get_google_oauth_flow(request)
        auth_uri = flow.step1_get_authorize_url()
        return HttpResponseRedirect(auth_uri)


class GoogleLoginCallback(TemplateView):
    """ Logs user in, or connects user to account """

    def get(self, request):

        if request.GET.get('error'):
            messages.error(request, _('Login failed.'))
            return HttpResponseRedirect(reverse('login'))

        code = request.GET.get('code')
        if not code:
            messages.error(request, _('Login failed.'))
            return HttpResponseRedirect(reverse('login'))

        flow = get_google_oauth_flow(request)

        try:
            credentials = flow.step2_exchange(code)
        except FlowExchangeError:
            messages.error(request, _('Login with Google is currently not possible.'))
            logger.exception('Login with Google failed')
            return HttpResponseRedirect(reverse('login'))

        email = credentials.token_response['id_token']['email']

        # Connect account
        if request.user.is_authenticated():
            request.user.google_email = email
            request.user.save()
            messages.success(request, _('Your account has been connected with '
                    '{google}. Open Settings to change this.'.format(
                        google=email)))
            return HttpResponseRedirect(DEFAULT_LOGIN_REDIRECT)

        # Check if Google account is connected
        User = get_user_model()
        try:
            user = User.objects.get(profile__google_email=email)

        except User.DoesNotExist:
            # Connect account
            messages.error(request, _('No account connected with your Google '
                        'account %s. Please log in to connect.' % email))
            return HttpResponseRedirect('{login}?next={connect}'.format(
                login=reverse('login'), connect=reverse('login-google')))

        # Log in user
        # TODO: this should probably be replaced with a call to authenticate()
        # http://stackoverflow.com/questions/6034763/django-attributeerror-user-object-has-no-attribute-backend-but-it-does
        user.backend='django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return HttpResponseRedirect(DEFAULT_LOGIN_REDIRECT)
