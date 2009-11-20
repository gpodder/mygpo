from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.template import RequestContext
from mygpo.api.models import Podcast

def home(request):
       if request.user.is_authenticated():
              return render_to_response('home-user.html', context_instance=RequestContext(request))

       else:
              podcasts = Podcast.objects.count()
              return render_to_response('home.html', {
                    'podcast_count': podcasts
              })

