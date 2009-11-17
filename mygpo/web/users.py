from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from mygpo.api.models import Podcast, UserAccount


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
              if user.generated_id:
                     return render_to_response('migrate.html', {
                           'authenticated': True,
                           'login_message': username,
                           'username': user
                     })
              else:
                     return render_to_response('home.html', {
                           'authenticated': True,
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


def migrate_user(request):
      podcasts = Podcast.objects.count()
      oldusername = request.POST.get('oldusername', None)
      newusername = request.POST.get('newusername', None)
      leave = request.POST.get('leave', None)
      submit = request.POST.get('submit', None)
      if leave:
            user = request.user
            user.generated_id = 0
            user.save()
            return render_to_response('home.html', {
                 'authenticated': True,
                 'login_message': request.user,
                 'podcast_count': podcasts
            })
      else:
            if newusername == '':
                 return render_to_response('migrate.html', {
                      'error': True,
                      'error_message': 'You have to fill in a new username in order to change',
                      'authenticated': True,
                      'login_message': request.user,
                      'username': request.user
                 })
            else:
                 tempuser = UserAccount.objects.get(username__exact=newusername)
                 if tempuser == '':
                      user = request.user
                      user.username = newusername
                      user.generated_id = 0
                      user.save()
                      return render_to_response('home.html', {
                           'authenticated': True,
                           'login_message': user,
                           'podcast_count': podcasts
                      })
                 else:
                      return render_to_response('migrate.html', {
                           'error': True,
                           'error_message': 'Username exists',
                           'authenticated': True,
                           'login_message': request.user,
                           'username': request.user
                      })