from django.shortcuts import render_to_response
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

def login_user(request):
       podcasts = Podcast.objects.count()
       try:
              username = request.POST['user']
              password = request.POST['pwd']
       except:
              return render_to_response('home.html', {
                     'error': True,
                     'error_message': 'No user or pwd entered',
                     'podcast_count': podcasts
              })

       user = authenticate(username=username, password=password)
       if user is not None:
              login(request, user)
              return render_to_response('home.html', {
                     'authenticated': True,
                     'change_password': user.generated_id,
                     'login_message': username,
                     'podcast_count': podcasts
              })
       else:
              return render_to_response('home.html', {
                     'error': True,
                     'error_message': 'User not known or wrong password',
                     'podcast_count': podcasts
              })
      


def logout_user(request):
       podcasts = Podcast.objects.count()
       logout(request)
       return render_to_response('home.html', {
             'podcast_count': podcasts
       })