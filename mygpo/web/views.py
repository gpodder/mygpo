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
from django.contrib.auth import authenticate, login, logout
from django.template import RequestContext
from mygpo.api.models import Podcast, UserProfile, Episode, Device, EpisodeAction, SubscriptionAction

def home(request):
       if request.user.is_authenticated():
              userid = UserProfile.objects.filter(user=request.user)[0].id
              device = Device.objects.filter(user=userid)
              device_ids = [d.id for d in device]
              sublog = SubscriptionAction.objects.filter(device__in=device_ids)
              sublog_podcastids = [s.podcast_id for s in sublog]
              podcast = Podcast.objects.filter(id__in=sublog_podcastids)
              podcast_titles = [p.title for p in podcast]
              podcast_logourls = [p.logo_url for p in podcast]
              podcast_ids = [p.id for p in podcast]
                       
              subscriptionlist = Ddict( dict )

              for listindex, title in enumerate(podcast_titles):
                    subscriptionlist[listindex]['logo'] = podcast_logourls[listindex]
                    subscriptionlist[listindex]['title'] = title                     
                    
                    sl = SubscriptionAction.objects.filter(podcast=podcast_ids[listindex])
                    sldev_ids = [s.device.id for s in sl]  
                    dev = Device.objects.filter(id__in=sldev_ids)
                    dev_names = [d.name for d in dev]
                    subscriptionlist[listindex]['device'] = dev_names                          

              return render_to_response('home-user.html', {
                    'subscriptionlist': subscriptionlist,
                    'test': subscriptionlist[0]['device']
              }, context_instance=RequestContext(request))

       else:
              podcasts = Podcast.objects.count()
              return render_to_response('home.html', {
                    'podcast_count': podcasts
              })

class Ddict(dict):
    def __init__(self, default=None):
        self.default = default

    def __getitem__(self, key):
        if not self.has_key(key):
            self[key] = self.default()
        return dict.__getitem__(self, key)

