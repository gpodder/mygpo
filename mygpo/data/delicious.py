import json
import hashlib
import urllib.request, urllib.parse, urllib.error
import urllib.parse


def get_tags(url):
    """
    queries the public API of delicious.com and retrieves a dictionary of all
    tags that have been used for the url, with the number of users that have
    used each tag
    """

    split = urllib.parse.urlsplit(url)
    if split.path == '':
        split = urllib.parse.SplitResult(
            split.scheme, split.netloc, '/', split.query, split.fragment
        )
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
