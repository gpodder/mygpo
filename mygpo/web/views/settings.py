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
from django.contrib.auth import logout
from django.template import RequestContext
from mygpo.api.models import Podcast, Subscription, SubscriptionMeta
from mygpo.web.forms import UserAccountForm
from django.forms import ValidationError
from django.utils.translation import ugettext as _
from mygpo.decorators import manual_gc, allowed_methods
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import RequestSite
from mygpo import migrate


@manual_gc
@login_required
@allowed_methods(['GET', 'POST'])
def account(request):
    success = False
    error_message = ''

    if request.method == 'GET':

       form = UserAccountForm({
            'email': request.user.email,
            'public': request.user.get_profile().public_profile
            })

       return render_to_response('account.html', {
            'form': form,
            }, context_instance=RequestContext(request))

    try:
        form = UserAccountForm(request.POST)

        if not form.is_valid():
            raise ValueError(_('Oops! Something went wrong. Please double-check the data you entered.'))

        if form.cleaned_data['password_current']:
            if not request.user.check_password(form.cleaned_data['password_current']):
                raise ValueError('Current password is incorrect')

            request.user.set_password(form.cleaned_data['password1'])

        request.user.email = form.cleaned_data['email']
        request.user.save()
        request.user.get_profile().save()

        success = True

    except ValueError, e:
        success = False
        error_message = e

    except ValidationError, e:
        success = False
        error_message = e

    return render_to_response('account.html', {
        'form': form,
        'success': success,
        'error_message': error_message
    }, context_instance=RequestContext(request))


@manual_gc
@login_required
@allowed_methods(['GET', 'POST'])
def delete_account(request):

    if request.method == 'GET':
        return render_to_response('delete_account.html', context_instance=RequestContext(request))

    profile = request.user.get_profile()
    profile.deleted = True
    profile.save()

    request.user.is_active = False
    request.user.save()
    logout(request)
    return render_to_response('delete_account.html', {
        'success': True
        }, context_instance=RequestContext(request))


@manual_gc
@login_required
@allowed_methods(['GET'])
def privacy(request):

    if 'private_subscriptions' in request.GET:
        request.user.get_profile().settings['public_profile'] = False
        request.user.get_profile().save()

    elif 'public_subscriptions' in request.GET:
        request.user.get_profile().settings['public_profile'] = True
        request.user.get_profile().save()

    if 'exclude' in request.GET:
        id = request.GET['exclude']
        try:
            podcast = Podcast.objects.get(pk=id)
            sm, c = SubscriptionMeta.objects.get_or_create(user=request.user, podcast=podcast, defaults={'public': False})

            if not c:
                sm.settings['public_subscription'] = False
                sm.save()

        except Podcast.DoesNotExist:
            pass

    if 'include' in request.GET:
        id = request.GET['include']
        try:
            podcast = Podcast.objects.get(pk=id)
            sm, c = SubscriptionMeta.objects.get_or_create(user=request.user, podcast=podcast, defaults={'public': True})

            if not c:
                sm.settings['public_subscription'] = True
                sm.save()

        except Podcast.DoesNotExist:
            pass

    subscriptions = [s for s in Subscription.objects.filter(user=request.user)]
    included_subscriptions = set([s.podcast for s in subscriptions if s.get_meta().public])
    excluded_subscriptions = set([s.podcast for s in subscriptions if not s.get_meta().public])

    return render_to_response('privacy.html', {
        'public_subscriptions': request.user.get_profile().public_profile,
        'included_subscriptions': included_subscriptions,
        'excluded_subscriptions': excluded_subscriptions,
        }, context_instance=RequestContext(request))


@manual_gc
@login_required
def share(request):
    site = RequestSite(request)
    user = migrate.get_or_migrate_user(request.user)

    if 'public_subscriptions' in request.GET:
        user.subscriptions_token = ''
        user.save()

    elif 'private_subscriptions' in request.GET:
        user.create_new_token('subscriptions_token')
        user.save()

    token = user.subscriptions_token

    return render_to_response('share.html', {
        'site': site,
        'token': token,
        }, context_instance=RequestContext(request))
