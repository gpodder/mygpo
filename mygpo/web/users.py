from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from registration.forms import RegistrationForm
from registration.views import activate, register
from registration.models import RegistrationProfile

def login_user(request):
       try:
              username = request.POST['user']
              password = request.POST['pwd']
       except:
              return render_to_response('login.html')

       user = authenticate(username=username, password=password)
       if user is not None:
              login(request, user)

              if user.get_profile().generated_id:
                     return render_to_response('migrate.html', {
                           'username': user
                     })
              else:
                  return HttpResponseRedirect('/')

       else:
              return render_to_response('login.html', {
                     'error_message': 'Unknown user or wrong password',
              })

@login_required
def migrate_user(request):
    user = request.user
    username = request.POST.get('username', user.username)

    if username == '':
        username = user.username

    if user.username != username:
        if User.objects.filter(username__exact=username).count() > 0:
            return render_to_response('migrate.html', {'error': True, 'error_message': '%s is already taken' % username, 'username': user.username})
        else:
            user.username = username
            user.save()

    user.get_profile().generated_id = 0
    user.get_profile().save()

    return HttpResponseRedirect('/')

