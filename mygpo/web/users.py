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
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.template.defaultfilters import slugify
from registration.forms import RegistrationForm
from registration.views import activate, register
from registration.models import RegistrationProfile
from mygpo.api.models import UserProfile
from django.contrib.sites.models import Site
from django.conf import settings

def login_user(request):
       try:
              username = request.POST['user']
              password = request.POST['pwd']
       except:
              return render_to_response('login.html')

       user = authenticate(username=username, password=password)
       if user is not None:
              login(request, user)
              current_site = Site.objects.get(id=settings.SITE_ID)

              try:
                  if user.get_profile().generated_id:
                      return render_to_response('migrate.html', {
                           'url': current_site,
                           'username': user
                      })
              except UserProfile.DoesNotExist:
                  UserProfile.objects.create(user=user)
                  return HttpResponseRedirect('/')

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
        current_site = Site.objects.get(id=settings.SITE_ID)
        if User.objects.filter(username__exact=username).count() > 0:
            return render_to_response('migrate.html', {'error_message': '%s is already taken' % username, 'url': current_site, 'username': user.username})
        if slugify(username) != username:
            return render_to_response('migrate.html', {'error_message': '%s is not a valid username. Please use characters, numbers, underscore and dash only.' % username, 'url': current_site, 'username': user.username})
        else:
            user.username = username
            user.save()

    user.get_profile().generated_id = 0
    user.get_profile().save()

    return HttpResponseRedirect('/')

