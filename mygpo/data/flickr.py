#
# This file is part of gpodder.net.
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


import re
import json
import urllib
from mygpo import settings

def get_photo_sizes(photo_id):
    api_key = settings.FLICKR_API_KEY
    request = 'http://api.flickr.com/services/rest/?method=flickr.photos.getSizes&api_key=%s&photo_id=%s&format=json' % (api_key, photo_id)

    resp = urllib.urlopen(request).read()

    extract_re = '^jsonFlickrApi\((.*)\)$'
    resp_content = re.match(extract_re, resp).group(1)

    resp_obj = json.loads(resp_content)

    return resp_obj['sizes']['size']

def get_photo_id(url):
    photo_id_re = 'http://.*flickr.com/[^/]+/([^_]+)_.*'
    return re.match(photo_id_re, url).group(1)


def is_flickr_image(url):
    return re.search('flickr\.com.*\.(jpg|jpeg|png|gif)', url)

def get_display_photo(url, label='Medium'):
    photo_id = get_photo_id(url)
    sizes = get_photo_sizes(photo_id)
    for s in sizes:
        if s['label'] == label:
            return s['source']

    return url

