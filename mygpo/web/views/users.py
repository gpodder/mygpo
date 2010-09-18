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
from mygpo.api.models import UserProfile
from mygpo.web.forms import RestorePasswordForm
from django.contrib.sites.models import Site
from django.conf import settings
from mygpo.decorators import manual_gc, allowed_methods
from django.utils.translation import ugettext as _
import string
import random

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
            'url': Site.objects.get_current(),
            'next': request.GET.get('next', ''),
            'restore_password_form': form,
        }, context_instance=RequestContext(request))

    username = request.POST['user']
    password = request.POST['pwd']
    user = authenticate(username=username, password=password)

    if user is None:
        return render_to_response('login.html', {
            'error_message': _('Wrong username or password.'),
            'next': request.POST.get('next', ''),
        }, context_instance=RequestContext(request))

    if not user.is_active:

        p, c = UserProfile.objects.get_or_create(user=user)

        if p.deleted:
            return render_to_response('login.html', {
                'error_message': _('You have deleted your account, but you can register again')
                }, context_instance=RequestContext(request))

        else:
            return render_to_response('login.html', {
                'error_message': _('Please activate your account first.'),
                'activation_needed': True,
            }, context_instance=RequestContext(request))

    login(request, user)

    try:
         if user.get_profile().generated_id:
             site = Site.objects.get_current()
             return render_to_response('migrate.html', {
                  'url': site,
                  'username': user
             }, context_instance=RequestContext(request))

    except UserProfile.DoesNotExist:
         profile, c = UserProfile.objects.get_or_create(user=user)

    if 'next' in request.POST and request.POST['next'] and request.POST['next'] != '/login/':
        return HttpResponseRedirect(request.POST['next'])

    return HttpResponseRedirect(DEFAULT_LOGIN_REDIRECT)

@login_required
def migrate_user(request):
    user = request.user
    username = request.POST.get('username', user.username)

    if username == '':
        username = user.username

    if user.username != username:
        current_site = Site.objects.get_current()
        if User.objects.filter(username__exact=username).count() > 0:
            return render_to_response('migrate.html', {
                'error_message': '%s is already taken' % username,
                'url': current_site,
                'username': user.username
                }, context_instance=RequestContext(request))

        if slugify(username) != username.lower():
            return render_to_response('migrate.html', {
                'error_message': '%s is not a valid username. Please use characters, numbers, underscore and dash only.' % username,
                'url': current_site,
                'username': user.username
                }, context_instance=RequestContext(request))

        else:
            user.username = username
            user.save()

    user.get_profile().generated_id = 0
    user.get_profile().save()

    return HttpResponseRedirect('/')

def get_user(username, email):
    if username:
        return User.objects.get(username=username)
    elif email:
        return User.objects.get(email=email)
    else:
        raise User.DoesNotExist('neither username nor email provided')


@allowed_methods(['POST'])
def restore_password(request):
    form = RestorePasswordForm(request.POST)
    if not form.is_valid():
        return HttpResponseRedirect('/login/')

    try:
        user = get_user(form.cleaned_data['username'], form.cleaned_data['email'])

    except User.DoesNotExist:
        error_message = _('User does not exist.')
        return render_to_response('password_reset_failed.html', {
            'error_message': error_message
        }, context_instance=RequestContext(request))

    site = Site.objects.get_current()
    pwd = "".join(random.sample(string.letters+string.digits, 8))
    subject = _('Reset password for your account on %s') % site
    message = _('Here is your new password for your account %(username)s on %(site)s: %(password)s') % {'username': user.username, 'site': site, 'password': pwd}
    user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
    user.set_password(pwd)
    user.save()
    return render_to_response('password_reset.html', context_instance=RequestContext(request))


@manual_gc
@allowed_methods(['GET', 'POST'])
def resend_activation(request):
    error_message = ''

    if request.method == 'GET':
        form = ResendActivationForm()
        return render_to_response('registration/resend_activation.html', {
            'form': form,
        }, context_instance=RequestContext(request))

    site = Site.objects.get_current()
    form = ResendActivationForm(request.POST)

    try:
        if not form.is_valid():
            raise ValueError(_('Invalid Username entered'))

        try:
            user = get_user(form.cleaned_data['username'], form.cleaned_data['email'])
        except User.DoesNotExist:
            raise ValueError(_('User does not exist.'))

        p, c = UserProfile.objects.get_or_create(user=user)
        if p.deleted:
            raise ValueError(_('You have deleted your account, but you can regster again.'))

        try:
            profile = RegistrationProfile.objects.get(user=user)
        except RegistrationProfile.DoesNotExist:
            profile = RegistrationProfile.objects.create_profile(user)

        if profile.activation_key == RegistrationProfile.ACTIVATED:
            user.is_active = True
            user.save()
            raise ValueError(_('Your account already has been activated. Go ahead and log in.'))

        elif profile.activation_key_expired():
            raise ValueError(_('Your activation key has expired. Please try another username, or retry with the same one tomorrow.'))

    except ValueError, e:
        return render_to_response('registration/resend_activation.html', {
           'form': form,
           'error_message' : e
        }, context_instance=RequestContext(request))


    try:
        profile.send_activation_email(site)

    except AttributeError:
        #old versions of django-registration send registration mails from RegistrationManager
        RegistrationProfile.objects.send_activation_email(profile, site)

    return render_to_response('registration/resent_activation.html', context_instance=RequestContext(request))

