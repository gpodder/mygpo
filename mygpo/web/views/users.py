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

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.template.defaultfilters import slugify
from django.template import RequestContext
from django.contrib import messages
from mygpo.web.forms import RestorePasswordForm
from django.contrib.sites.models import RequestSite
from django.conf import settings
from mygpo.decorators import allowed_methods
from django.utils.translation import ugettext as _
import string
import random


from mygpo.users.models import User
from mygpo.web.forms import ResendActivationForm
from mygpo.constants import DEFAULT_LOGIN_REDIRECT

def login_user(request):
    # Do not show login page for already-logged-in users
    if request.user.is_authenticated():
        return HttpResponseRedirect(DEFAULT_LOGIN_REDIRECT)

    if 'user' not in request.POST or 'pwd' not in request.POST:
        if request.GET.get('restore_password', False):
            form = RestorePasswordForm()
        else:
            form = None

        return render_to_response('login.html', {
            'url': RequestSite(request),
            'next': request.GET.get('next', ''),
            'restore_password_form': form,
        }, context_instance=RequestContext(request))

    username = request.POST['user']
    password = request.POST['pwd']
    user = authenticate(username=username, password=password)

    if user is None:

        messages.error(request, _('Wrong username or password.'))

        return render_to_response('login.html', {
            'next': request.POST.get('next', ''),
        }, context_instance=RequestContext(request))

    if not user.is_active:

        if user.deleted:

            messages.error(request, _('You have deleted your account, '
                    'but you can register again'))

            return render_to_response('login.html', {
                }, context_instance=RequestContext(request))

        else:

            messages.error(request, _('Please activate your account first.'))

            return render_to_response('login.html', {
                'activation_needed': True,
            }, context_instance=RequestContext(request))

    login(request, user)

    if 'next' in request.POST and request.POST['next'] and request.POST['next'] != '/login/':
        return HttpResponseRedirect(request.POST['next'])

    return HttpResponseRedirect(DEFAULT_LOGIN_REDIRECT)


def get_user(username, email):
    if username:
        return User.get_user(username)

    elif email:
        return User.get_user_by_email(email)

    return None


@allowed_methods(['POST'])
def restore_password(request):
    form = RestorePasswordForm(request.POST)
    if not form.is_valid():
        return HttpResponseRedirect('/login/')

    user = get_user(form.cleaned_data['username'], form.cleaned_data['email'])

    if not user:
        messages.error(request, _('User does not exist.'))

        return render_to_response('password_reset_failed.html', {
        }, context_instance=RequestContext(request))

    site = RequestSite(request)
    pwd = "".join(random.sample(string.letters+string.digits, 8))
    subject = _('Reset password for your account on %s') % site
    message = _('Here is your new password for your account %(username)s on %(site)s: %(password)s') % {'username': user.username, 'site': site, 'password': pwd}
    user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
    user.set_password(pwd)
    user.save()
    return render_to_response('password_reset.html', context_instance=RequestContext(request))


@allowed_methods(['GET', 'POST'])
def resend_activation(request):

    if request.method == 'GET':
        form = ResendActivationForm()
        return render_to_response('registration/resend_activation.html', {
            'form': form,
        }, context_instance=RequestContext(request))

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

        if user.activation_key == User.ACTIVATED:
            user.is_active = True
            user.save()
            raise ValueError(_('Your account already has been activated. Go ahead and log in.'))

        elif user.activation_key_expired():
            raise ValueError(_('Your activation key has expired. Please try another username, or retry with the same one tomorrow.'))

    except ValueError, e:
        messages.error(request, str(e))

        return render_to_response('registration/resend_activation.html', {
           'form': form,
        }, context_instance=RequestContext(request))


    try:
        user.send_activation_email(site)

    except AttributeError:
        user.send_activation_email(site)

    return render_to_response('registration/resent_activation.html', context_instance=RequestContext(request))

