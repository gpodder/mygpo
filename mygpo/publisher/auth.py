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

from functools import wraps

from django.http import HttpResponseRedirect


def require_publisher(protected_view):
    @wraps(protected_view)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated():
            return HttpResponseRedirect('/login/')

        if is_publisher(request.user):
            return protected_view(request, *args, **kwargs)

        return HttpResponseRedirect('/')

    return wrapper


def is_publisher(user):
    """
    checks if the given user has publisher rights,
    ie he is either set as the publisher of at least one podcast,
    or he has the staff flag set
    """

    if not user.is_authenticated():
        return False

    if user.is_staff:
        return True

    if user.published_objects:
        return True

    return False

