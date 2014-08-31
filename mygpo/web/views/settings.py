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

from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.contrib import messages
from django.forms import ValidationError
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import RequestSite
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache, cache_control
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from django.utils.html import strip_tags

from mygpo.podcasts.models import Podcast
from mygpo.subscriptions.models import PodcastConfig
from mygpo.decorators import allowed_methods, repeat_on_conflict
from mygpo.web.forms import UserAccountForm, ProfileForm, FlattrForm
from mygpo.web.utils import normalize_twitter
from mygpo.flattr import Flattr
from mygpo.users.settings import PUBLIC_SUB_USER, PUBLIC_SUB_PODCAST, \
         FLATTR_TOKEN, FLATTR_AUTO, FLATTR_MYGPO, FLATTR_USERNAME


@login_required
@vary_on_cookie
@cache_control(private=True)
@allowed_methods(['GET', 'POST'])
def account(request):

    if request.method == 'GET':

        site = RequestSite(request)
        flattr = Flattr(request.user, site.domain, request.is_secure())
        userpage_token = request.user.profile.get_token('userpage_token')

        profile_form = ProfileForm({
               'twitter': request.user.profile.twitter,
               'about':   request.user.profile.about,
            })

        form = UserAccountForm({
            'email': request.user.email,
            'public': request.user.profile.get_wksetting(PUBLIC_SUB_USER)
            })

        flattr_form = FlattrForm({
               'enable': request.user.profile.get_wksetting(FLATTR_AUTO),
               'token': request.user.profile.get_wksetting(FLATTR_TOKEN),
               'flattr_mygpo': request.user.profile.get_wksetting(FLATTR_MYGPO),
               'username': request.user.profile.get_wksetting(FLATTR_USERNAME),
            })

        return render(request, 'account.html', {
            'site': site,
            'form': form,
            'profile_form': profile_form,
            'flattr_form': flattr_form,
            'flattr': flattr,
            'userpage_token': userpage_token,
            })

    try:
        form = UserAccountForm(request.POST)

        if not form.is_valid():
            raise ValueError(_('Oops! Something went wrong. Please double-check the data you entered.'))

        if form.cleaned_data['password_current']:
            if not request.user.check_password(form.cleaned_data['password_current']):
                raise ValueError('Current password is incorrect')

            request.user.set_password(form.cleaned_data['password1'])

        request.user.email = form.cleaned_data['email']

        try:
            request.user.save()
        except Exception as ex:
            # TODO: which exception?
            messages.error(request, str(ex))

        messages.success(request, 'Account updated')

    except (ValueError, ValidationError) as e:
        messages.error(request, str(e))

    return render(request, 'account.html', {
        'form': form,
    })


class ProfileView(View):
    """ Updates the public profile and redirects back to the account view """

    def post(self, request):
        user = request.user

        form = ProfileForm(request.POST)

        if not form.is_valid():
            raise ValueError(_('Oops! Something went wrong. Please double-check the data you entered.'))

        request.user.twitter = normalize_twitter(form.cleaned_data['twitter'])
        request.user.about = strip_tags(form.cleaned_data['about'])

        request.user.save()
        messages.success(request, _('Data updated'))

        return HttpResponseRedirect(reverse('account') + '#profile')


class FlattrSettingsView(View):
    """ Updates Flattr settings and redirects back to the Account page """

    def post(self, request):
        user = request.user

        form = FlattrForm(request.POST)

        if not form.is_valid():
            raise ValueError('asdf')

        auto_flattr = form.cleaned_data.get('enable', False)
        flattr_mygpo = form.cleaned_data.get('flattr_mygpo', False)
        username = form.cleaned_data.get('username', '')

        user.profile.set_wksetting(FLATTR_AUTO, auto_flattr)
        user.profile.set_wksetting(FLATTR_MYGPO, flattr_mygpo)
        user.profile.set_wksetting(FLATTR_USERNAME, username)
        user.profile.save()

        return HttpResponseRedirect(reverse('account') + '#flattr')


class FlattrLogout(View):
    """ Removes Flattr authentication token """

    def get(self, request):
        user = request.user
        user.profile.set_wksetting(FLATTR_AUTO, False)
        user.profile.set_wksetting(FLATTR_TOKEN, False)
        user.profile.set_wksetting(FLATTR_MYGPO, False)
        user.profile.save()
        return HttpResponseRedirect(reverse('account') + '#flattr')


class FlattrTokenView(View):
    """ Callback for the Flattr authentication

    Updates the user's Flattr token and redirects back to the account page """

    def get(self, request):

        user = request.user
        site = RequestSite(request)
        flattr = Flattr(user, site.domain, request.is_secure())

        url = request.build_absolute_uri()
        token = flattr.process_retrieved_code(url)
        if token:
            messages.success(request, _('Authentication successful'))
            user.profile.set_wksetting(FLATTR_TOKEN, token)
            user.profile.save()

        else:
            messages.error(request, _('Authentication failed. Try again later'))

        return HttpResponseRedirect(reverse('account') + '#flattr')


class AccountRemoveGoogle(View):
    """ Removes the connected Google account """

    @method_decorator(login_required)
    def post(self, request):
        request.user.google_email = None
        request.user.save()
        messages.success(request, _('Your account has been disconnected'))
        return HttpResponseRedirect(reverse('account'))


@login_required
@never_cache
@allowed_methods(['GET', 'POST'])
def delete_account(request):

    if request.method == 'GET':
        return render(request, 'delete_account.html')

    @repeat_on_conflict(['user'])
    def do_delete(user):
        user.is_active = False
        user.deleted = True
        user.save()

    do_delete(user=request.user)
    logout(request)

    return render(request, 'deleted_account.html')



class DefaultPrivacySettings(View):

    public = True

    @method_decorator(login_required)
    @method_decorator(never_cache)
    def post(self, request):
        profile = request.user.profile
        profile.set_setting(PUBLIC_SUB_USER.name, self.public)
        profile.save()
        return HttpResponseRedirect(reverse('privacy'))


class PodcastPrivacySettings(View):

    public = True

    @method_decorator(login_required)
    @method_decorator(never_cache)
    def post(self, request, podcast_id):
        podcast = Podcast.objects.get(id=podcast_id)

        config, created = PodcastConfig.objects.get_or_create(
            user=request.user,
            podcast=podcast,
        )

        config.set_wksetting(PUBLIC_SUB_PODCAST, self.public)
        config.save()
        return HttpResponseRedirect(reverse('privacy'))


@login_required
@never_cache
def privacy(request):
    site = RequestSite(request)
    user = request.user

    podcasts = Podcast.objects.filter(subscription__user=user)\
                              .distinct('pk')
    private = PodcastConfig.objects.get_private_podcasts(user)

    subscriptions = []
    for podcast in podcasts:

        subscriptions.append( (podcast, podcast in private) )

    return render(request, 'privacy.html', {
        'private_subscriptions': not request.user.profile.get_wksetting(PUBLIC_SUB_USER),
        'subscriptions': subscriptions,
        'domain': site.domain,
        })


@vary_on_cookie
@cache_control(private=True)
@login_required
def share(request):
    site = RequestSite(request)

    user = request.user

    if 'public_subscriptions' in request.GET:
        user.profile.subscriptions_token = ''
        user.profile.save()

    elif 'private_subscriptions' in request.GET:
        user.profile.create_new_token('subscriptions_token')
        user.profile.save()

    token = user.profile.get_token('subscriptions_token')

    return render(request, 'share.html', {
        'site': site,
        'token': token,
        })
