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
from mygpo.web.forms import UserAccountForm
from django.forms import ValidationError
from django.utils.translation import ugettext as _
from mygpo.decorators import manual_gc, allowed_methods, repeat_on_conflict
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import RequestSite
from mygpo.core.models import Podcast
from mygpo import migrate
from mygpo.utils import get_to_dict


@manual_gc
@login_required
@allowed_methods(['GET', 'POST'])
def account(request):
    success = False
    error_message = ''

    user = migrate.get_or_migrate_user(request.user)

    if request.method == 'GET':

       form = UserAccountForm({
            'email': request.user.email,
            'public': user.settings.get('public_subscriptions', True)
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

    site = RequestSite(request)
    user = migrate.get_or_migrate_user(request.user)

    @repeat_on_conflict(['state'])
    def set_privacy_settings(state, is_public):
        state.settings['public_subscriptions'] = is_public
        state.save()

    if 'private_subscriptions' in request.GET:
        set_privacy_settings(state=user, is_public=False)

    elif 'public_subscriptions' in request.GET:
        set_privacy_settings(state=user, is_public=True)

    if 'exclude' in request.GET:
        id = request.GET['exclude']
        podcast = Podcast.get(id)
        state = podcast.get_user_state(request.user)
        set_privacy_settings(state=state, is_public=False)

    if 'include' in request.GET:
        id = request.GET['include']
        podcast = Podcast.get(id)
        state = podcast.get_user_state(request.user)
        set_privacy_settings(state=state, is_public=True)

    user = migrate.get_or_migrate_user(request.user)
    subscriptions = user.get_subscriptions()
    podcasts = get_to_dict(Podcast, [x[1] for x in subscriptions], get_id=Podcast.get_id)

    included_subscriptions = set([podcasts[x[1]] for x in subscriptions if x[0] == True])
    excluded_subscriptions = set([podcasts[x[1]] for x in subscriptions if x[0] == False])

    return render_to_response('privacy.html', {
        'public_subscriptions': user.settings.get('public_subscriptions', True),
        'included_subscriptions': included_subscriptions,
        'excluded_subscriptions': excluded_subscriptions,
        'domain': site.domain,
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
