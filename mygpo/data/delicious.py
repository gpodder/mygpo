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


import hashlib
import urllib.request, urllib.parse, urllib.error
import urllib.parse

from mygpo.core.json import json


def get_tags(url):
    """
    queries the public API of delicious.com and retrieves a dictionary of all
    tags that have been used for the url, with the number of users that have
    used each tag
    """

    split = urllib.parse.urlsplit(url)
    if split.path == '':
        split = urllib.parse.SplitResult(split.scheme, split.netloc, '/', split.query, split.fragment)
    url = split.geturl()

    m = hashlib.md5()
    m.update(url.encode('ascii'))

    url_md5 = m.hexdigest()
    req = 'http://feeds.delicious.com/v2/json/urlinfo/%s' % url_md5

    resp = urllib.request.urlopen(req).read()
    try:
        resp_obj = json.loads(resp)
    except ValueError:
        return {}

    tags = {}
    for o in resp_obj:
        if (not 'top_tags' in o) or (not o['top_tags']):
            return {}
        for tag, count in o['top_tags'].items():
            tags[tag] = count


    return tags
