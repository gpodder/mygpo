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
from django.contrib import messages
from django.forms import ValidationError
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import RequestSite

from mygpo.decorators import allowed_methods, repeat_on_conflict
from mygpo.web.forms import UserAccountForm
from mygpo.core.models import Podcast
from mygpo.utils import get_to_dict


@login_required
@allowed_methods(['GET', 'POST'])
def account(request):

    if request.method == 'GET':

       form = UserAccountForm({
            'email': request.user.email,
            'public': request.user.settings.get('public_subscriptions', True)
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

        messages.success(request, 'Account updated')

    except (ValueError, ValidationError) as e:
        messages.error(request, str(e))

    return render_to_response('account.html', {
        'form': form,
    }, context_instance=RequestContext(request))


@login_required
@allowed_methods(['GET', 'POST'])
def delete_account(request):

    if request.method == 'GET':
        return render_to_response('delete_account.html',
                context_instance=RequestContext(request))

    request.user.is_active = False
    request.user.deleted = True
    request.user.save()
    logout(request)

    return render_to_response('deleted_account.html', {
        }, context_instance=RequestContext(request))


@login_required
@allowed_methods(['GET'])
def privacy(request):

    site = RequestSite(request)

    @repeat_on_conflict(['state'])
    def set_privacy_settings(state, is_public):
        state.settings['public_subscriptions'] = is_public
        state.save()

    if 'private_subscriptions' in request.GET:
        set_privacy_settings(state=request.user, is_public=False)

    elif 'public_subscriptions' in request.GET:
        set_privacy_settings(state=request.user, is_public=True)

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

    subscriptions = request.user.get_subscriptions()
    podcasts = get_to_dict(Podcast, [x[1] for x in subscriptions], get_id=Podcast.get_id)

    included_subscriptions = set(filter(None, [podcasts.get(x[1], None) for x in subscriptions if x[0] == True]))
    excluded_subscriptions = set(filter(None, [podcasts.get(x[1], None) for x in subscriptions if x[0] == False]))

    return render_to_response('privacy.html', {
        'public_subscriptions': request.user.settings.get('public_subscriptions', True),
        'included_subscriptions': included_subscriptions,
        'excluded_subscriptions': excluded_subscriptions,
        'domain': site.domain,
        }, context_instance=RequestContext(request))
