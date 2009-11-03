from django.shortcuts import render_to_response
from mygpo.api.models import Podcast

def home(request):
    podcasts = Podcast.objects.count()
    return render_to_response('home.html', {
            'podcast_count': podcasts
        })

