# -*- coding: utf-8 -*-
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
from django.template import RequestContext
from django.contrib.sites.models import RequestSite
from django.utils.translation import ugettext as _


def csrf_failure(request, reason=""):
    site = RequestSite(request)
    return render_to_response('csrf.html', {
        'site': site,
        'method': request.method,
        'referer': request.META.get('HTTP_REFERER', _('another site')),
        'path': request.path,
        'get': request.GET,
        'post': request.POST,
    }, context_instance=RequestContext(request))

