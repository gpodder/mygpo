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
from django.contrib.auth.decorators import login_required
from django.template.defaultfilters import slugify
from django.contrib import messages
from django.contrib.sites.models import RequestSite
from django.conf import settings
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache

from couchdbkit import ResourceConflict

from mygpo.decorators import allowed_methods, repeat_on_conflict
from mygpo.web.forms import RestorePasswordForm
from mygpo.users.models import User
from mygpo.web.forms import ResendActivationForm
from mygpo.constants import DEFAULT_LOGIN_REDIRECT


@repeat_on_conflict(['user'])
def login(request, user):
    from django.contrib.auth import login
    login(request, user)



@never_cache
def login_user(request):
    # Do not show login page for already-logged-in users
    if request.user.is_authenticated():
        return HttpResponseRedirect(DEFAULT_LOGIN_REDIRECT)

    if 'user' not in request.POST or 'pwd' not in request.POST:
        if request.GET.get('restore_password', False):
            form = RestorePasswordForm()
        else:
            form = None

        return render(request, 'login.html', {
            'url': RequestSite(request),
            'next': request.GET.get('next', ''),
            'restore_password_form': form,
        })

    username = request.POST['user']
    password = request.POST['pwd']
    user = authenticate(username=username, password=password)

    if user is None:

        messages.error(request, _('Wrong username or password.'))

        return render(request, 'login.html', {
            'next': request.POST.get('next', ''),
        })

    if not user.is_active:

        if user.deleted:

            messages.error(request, _('You have deleted your account, '
                    'but you can register again'))

            return render(request, 'login.html')

        else:

            messages.error(request, _('Please activate your account first.'))

            return render(request, 'login.html', {
                'activation_needed': True,
            })

    login(request=request, user=user)

    if 'next' in request.POST and request.POST['next'] and request.POST['next'] != '/login/':
        return HttpResponseRedirect(request.POST['next'])

    return HttpResponseRedirect(DEFAULT_LOGIN_REDIRECT)


def get_user(username, email):
    if username:
        return User.get_user(username)

    elif email:
        return User.get_user_by_email(email)

    return None


@never_cache
@allowed_methods(['POST'])
def restore_password(request):
    form = RestorePasswordForm(request.POST)
    if not form.is_valid():
        return HttpResponseRedirect('/login/')

    user = get_user(form.cleaned_data['username'], form.cleaned_data['email'])

    if not user:
        messages.error(request, _('User does not exist.'))

        return render(request, 'password_reset_failed.html')

    site = RequestSite(request)
    pwd = "".join(random.sample(string.letters+string.digits, 8))
    subject = _('Reset password for your account on %s') % site
    message = _('Here is your new password for your account %(username)s on %(site)s: %(password)s') % {'username': user.username, 'site': site, 'password': pwd}
    user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
    _set_password(user=user, password=pwd)
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

        user = get_user(form.cleaned_data['username'], form.cleaned_data['email'])
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
        messages.error(request, str(e))

        return render(request, 'registration/resend_activation.html', {
           'form': form,
        })


    try:
        user.send_activation_email(site)

    except AttributeError:
        user.send_activation_email(site)

    return render(request, 'registration/resent_activation.html')

