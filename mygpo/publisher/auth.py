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

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login
from mygpo.publisher.models import PodcastPublisher


def require_publisher(protected_view):
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated():
            return HttpResponseRedirect('/publisher')

        if request.user.is_staff:
            return protected_view(request, *args, **kwargs)

        if PodcastPublisher.objects.filter(user=request.user).count() > 0:
            return protected_view(request, *args, **kwargs)

        return HttpResponseRedirect('/')

    return wrapper


