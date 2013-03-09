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

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate
from django.contrib import messages
from django.contrib.sites.models import RequestSite
from django.conf import settings
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from django.views.generic.base import View
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.utils.http import is_safe_url

from mygpo.decorators import allowed_methods, repeat_on_conflict
from mygpo.web.forms import RestorePasswordForm
from mygpo.users.models import User
from mygpo.web.forms import ResendActivationForm
from mygpo.constants import DEFAULT_LOGIN_REDIRECT


@repeat_on_conflict(['user'])
def login(request, user):
    from django.contrib.auth import login
    login(request, user)


class LoginView(View):
    """ View to login a user """

    def get(self, request):
        """ Shows the login page """

        # Do not show login page for already-logged-in users
        if request.user.is_authenticated():
            return HttpResponseRedirect(DEFAULT_LOGIN_REDIRECT)

        return render(request, 'login.html', {
            'url': RequestSite(request),
            'next': request.GET.get('next', ''),
        })


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
            # if the user is not active, find the reason
            if user.deleted:
                messages.error(request, _('You have deleted your account, '
                        'but you can register again'))
                return HttpResponseRedirect(login_page)

            else:
                messages.error(request,
                        _('Please activate your account first.'))
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


def get_user(username, email, is_active=None):
    if username:
        return User.get_user(username, is_active=None)

    elif email:
        return User.get_user_by_email(email, is_active=None)

    return None


@never_cache
def restore_password(request):

    if request.method == 'GET':
        form = RestorePasswordForm()
        return render(request, 'restore_password.html', {
            'form': form,
        })


    form = RestorePasswordForm(request.POST)
    if not form.is_valid():
        return HttpResponseRedirect('/login/')

    user = get_user(form.cleaned_data['username'], form.cleaned_data['email'], is_active=None)

    if not user:
        messages.error(request, _('User does not exist.'))

        return render(request, 'password_reset_failed.html')

    site = RequestSite(request)
    pwd = "".join(random.sample(string.letters+string.digits, 8))
    subject = _('Reset password for your account on %s') % site
    message = _('Here is your new password for your account %(username)s on %(site)s: %(password)s') % {'username': user.username, 'site': site, 'password': pwd}
    user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
    _set_password(user, pwd)
    return render(request, 'password_reset.html')


@repeat_on_conflict(['user'])
def _set_password(user, password):
    user.set_password(password)
    user.save()


@repeat_on_conflict(['user'])
def _set_active(user, is_active=True):
    user.is_active = is_active
    user.save()


@never_cache
@allowed_methods(['GET', 'POST'])
def resend_activation(request):

    if request.method == 'GET':
        form = ResendActivationForm()
        return render(request, 'registration/resend_activation.html', {
            'form': form,
        })

    site = RequestSite(request)
    form = ResendActivationForm(request.POST)

    try:
        if not form.is_valid():
            raise ValueError(_('Invalid Username entered'))

        user = get_user(form.cleaned_data['username'], form.cleaned_data['email'], is_active=None)
        if not user:
            raise ValueError(_('User does not exist.'))

        if user.deleted:
            raise ValueError(_('You have deleted your account, but you can regster again.'))

        if user.activation_key == None:
            _set_active(user=user, is_active=True)
            raise ValueError(_('Your account already has been activated. Go ahead and log in.'))

        elif user.activation_key_expired():
            raise ValueError(_('Your activation key has expired. Please try another username, or retry with the same one tomorrow.'))

    except ValueError, e:
        messages.error(request, unicode(e))

        return render(request, 'registration/resend_activation.html', {
           'form': form,
        })


    try:
        user.send_activation_email(site)

    except AttributeError:
        user.send_activation_email(site)

    return render(request, 'registration/resent_activation.html')

