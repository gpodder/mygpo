from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from mygpo.api.models import Podcast

def home(request):
       podcasts = Podcast.objects.count()
       if request.user.is_authenticated():
              return render_to_response('home.html', {
                    'authenticated': True,
                    'login_message': request.user,
                    'podcast_count': podcasts
              })
       else:
              return render_to_response('home.html', {
                    'podcast_count': podcasts
              })

