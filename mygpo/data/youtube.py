#!/usr/bin/python
# -*- coding: utf-8 -*-

# taken from gPodder :)

import re
import urllib.request, urllib.parse, urllib.error

def is_video_link(url):
    return (get_youtube_id(url) is not None)

def get_youtube_id(url):
    if url is None:
        return None

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
        data = urllib.request.urlopen(api_url).read()
        match = re.search('<media:thumbnail url=[\'"]([^\'"]+)[\'"]/>', data)
        if match is not None:
            return match.group(1)

    return None
