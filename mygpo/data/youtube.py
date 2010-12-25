#!/usr/bin/python
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

# taken from gPodder :)

import re
import urllib

def is_video_link(url):
    return (get_youtube_id(url) is not None)

def get_youtube_id(url):
    r = re.compile('http://(?:[a-z]+\.)?youtube\.com/v/(.*)\.swf', re.IGNORECASE).match(url)
    if r is not None:
        return r.group(1)

    r = re.compile('http://(?:[a-z]+\.)?youtube\.com/watch\?v=([^&]*)', re.IGNORECASE).match(url)
    if r is not None:
        return r.group(1)

    return None


def get_real_cover(url):
    rs = [re.compile('http://www\\.youtube\\.com/rss/user/([^/]+)/videos\\.rss',  re.IGNORECASE),
          re.compile('http://www\\.youtube\\.com/profile_videos\\?user=([^\&]+)', re.IGNORECASE)]

    for r in rs:
        m = r.match(url)
        if m is None:
            continue
        username = m.group(1)
        api_url = 'http://gdata.youtube.com/feeds/api/users/%s?v=2' % username
        data = urllib.urlopen(api_url).read()
        match = re.search('<media:thumbnail url=[\'"]([^\'"]+)[\'"]/>', data)
        if match is not None:
            return match.group(1)

    return None
