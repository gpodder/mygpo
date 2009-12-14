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
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.template import RequestContext
from mygpo.api.models import Podcast, UserProfile, Episode, Device, EpisodeAction, SubscriptionAction, ToplistEntry
from mygpo.web.forms import UserAccountForm
from mygpo.api.opml import Exporter
from django.utils.translation import ugettext as _

def home(request):
       if request.user.is_authenticated():
              subscriptionlist = create_subscriptionlist(request)              

              return render_to_response('home-user.html', {
                    'subscriptionlist': subscriptionlist
              }, context_instance=RequestContext(request))

       else:
              podcasts = Podcast.objects.count()
              return render_to_response('home.html', {
                    'podcast_count': podcasts
              })

def create_subscriptionlist(request):
      userid = UserProfile.objects.filter(user=request.user)[0].id
      device = Device.objects.filter(user__id=userid)
      device_ids = [d.id for d in device]
      sublog = SubscriptionAction.objects.filter(device__in=device_ids)
      sublog_podcastids = [s.podcast_id for s in sublog]

      podcast = Podcast.objects.filter(id__in=sublog_podcastids).order_by('title')
      subscriptionlist = [{'title': p.title, 'logo': p.logo_url, 'id': p.id} for p in podcast]

      for index, entry in enumerate(subscriptionlist):
            sublog_for_device = SubscriptionAction.objects.filter(podcast__id=subscriptionlist[index]['id'])
            sublog_devids = [s.device.id for s in sublog_for_device]
            dev = Device.objects.filter(id__in=sublog_devids, user__id=userid).values_list('name', flat=True)
            subscriptionlist[index]['device'] = ''
            for d in dev:
                 subscriptionlist[index]['device'] += d + ", "
            subscriptionlist[index]['episode'] = 'epi'
      return subscriptionlist


def account(request):
    success = False

    if request.method == 'POST':
        form = UserAccountForm(request.POST)

        if form.is_valid():
            request.user.email = form.cleaned_data['email']
            request.user.save()
            request.user.get_profile().public_profile = form.cleaned_data['public']
            request.user.get_profile().save()

            success = True

    else:
        form = UserAccountForm({
            'email': request.user.email,
            'public': request.user.get_profile().public_profile
            })

    return render_to_response('account.html', {
        'form': form,
        'success': success
    }, context_instance=RequestContext(request))

def toplist(request):
    len = 30
    entries = ToplistEntry.objects.all().order_by('-subscriptions')[:len]
    return render_to_response('toplist.html', {
        'count'  : len,
        'entries': entries,
    }, context_instance=RequestContext(request))


def toplist_opml(request, count):
    entries = ToplistEntry.objects.all().order_by('-subscriptions')[:count]
    exporter = Exporter(_('my.gpodder.org - Top %s') % count)

    opml = exporter.generate([e.podcast for e in entries])

    return HttpResponse(opml, mimetype='text/xml')
 

#sl = SubscriptionAction.objects.filter(podcast=podcast_ids[listindex])
#sldev_ids = [s.device.id for s in sl]  
#dev = Device.objects.filter(id__in=sldev_ids)
#dev_names = [d.name for d in dev]
