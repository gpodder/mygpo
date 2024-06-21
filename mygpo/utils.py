# -*- coding: utf-8 -*-

import json
import functools
import types
import subprocess
import os
import operator
import sys
import re
import collections
import itertools
from datetime import datetime, timedelta, date
import time
import hashlib
import urllib.parse
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import zlib
import shlex

from django.db import transaction, IntegrityError
from django.conf import settings
from django.urls import reverse

import logging

logger = logging.getLogger(__name__)


def daterange(from_date, to_date=None, leap=timedelta(days=1)):
    """
    >>> from_d = datetime(2010, 1, 1)
    >>> to_d = datetime(2010, 1, 5)
    >>> list(daterange(from_d, to_d))
    [datetime.datetime(2010, 1, 1, 0, 0), datetime.datetime(2010, 1, 2, 0, 0), datetime.datetime(2010, 1, 3, 0, 0), datetime.datetime(2010, 1, 4, 0, 0), datetime.datetime(2010, 1, 5, 0, 0)]
    """

    if to_date is None:
        if isinstance(from_date, datetime):
            to_date = datetime.utcnow()
        else:
            to_date = date.today()

    while from_date <= to_date:
        yield from_date
        from_date = from_date + leap
    return


def format_time(value):
    """Format an offset (in seconds) to a string

    The offset should be an integer or float value.

    >>> format_time(0)
    '00:00'
    >>> format_time(20)
    '00:20'
    >>> format_time(3600)
    '01:00:00'
    >>> format_time(10921)
    '03:02:01'
    """
    try:
        dt = datetime.utcfromtimestamp(value)
    except (ValueError, TypeError):
        return ""

    if dt.hour == 0:
        return dt.strftime("%M:%S")
    else:
        return dt.strftime("%H:%M:%S")


def parse_time(value):
    """
    >>> parse_time(10)
    10

    >>> parse_time('05:10') #5*60+10
    310

    >>> parse_time('1:05:10') #60*60+5*60+10
    3910
    """
    if value is None:
        raise ValueError("None value in parse_time")

    if isinstance(value, int):
        # Don't need to parse already-converted time value
        return value

    if value == "":
        raise ValueError("Empty valueing in parse_time")

    for format in ("%H:%M:%S", "%M:%S"):
        try:
            t = time.strptime(value, format)
            return t.tm_hour * 60 * 60 + t.tm_min * 60 + t.tm_sec
        except ValueError as e:
            continue

    return int(value)


def parse_bool(val):
    """
    >>> parse_bool('True')
    True

    >>> parse_bool('true')
    True

    >>> parse_bool('')
    False
    """
    if isinstance(val, bool):
        return val
    if val.lower() == "true":
        return True
    return False


def progress(val, max_val, status_str="", max_width=50, stream=sys.stdout):

    factor = float(val) / max_val if max_val > 0 else 0

    # progress as percentage
    percentage_str = "{val:.2%}".format(val=factor)

    # progress bar filled with #s
    factor = min(int(factor * max_width), max_width)
    progress_str = "#" * factor + " " * (max_width - factor)

    # insert percentage into bar
    percentage_start = int((max_width - len(percentage_str)) / 2)
    progress_str = (
        progress_str[:percentage_start]
        + percentage_str
        + progress_str[percentage_start + len(percentage_str) :]
    )

    print("\r", end=" ", file=stream)
    print(
        "[ %s ] %s / %s | %s" % (progress_str, val, max_val, status_str),
        end=" ",
        file=stream,
    )
    stream.flush()


def intersect(a, b):
    return list(set(a) & set(b))


def parse_range(s, min, max, default=None):
    """
    Parses the string and returns its value. If the value is outside the given
    range, its closest number within the range is returned

    >>> parse_range('5', 0, 10)
    5

    >>> parse_range('0', 5.0, 10)
    5.0

    >>> parse_range('15',0, 10)
    10

    >>> parse_range('x', 0., 20)
    10.0

    >>> parse_range('x', 0, 20, 20)
    20
    """
    out_type = type(min)

    try:
        val = int(s)
        if val < min:
            return min
        if val > max:
            return max
        return val

    except (ValueError, TypeError):
        return default if default is not None else out_type((max - min) / 2)


def get_timestamp(datetime_obj):
    """Returns the timestamp as an int for the given datetime object

    >>> get_timestamp(datetime(2011, 4, 7, 9, 30, 6))
    1302168606

    >>> get_timestamp(datetime(1970, 1, 1, 0, 0, 0))
    0
    """
    return int(time.mktime(datetime_obj.timetuple()))


re_url = re.compile("^https?://")


def is_url(string):
    """Returns true if a string looks like an URL

    >>> is_url('http://example.com/some-path/file.xml')
    True

    >>> is_url('something else')
    False
    """

    return bool(re_url.match(string))


# from http://stackoverflow.com/questions/2892931/longest-common-substring-from-more-than-two-strings-python
# this does not increase asymptotical complexity
# but can still waste more time than it saves.
def shortest_of(strings):
    return min(strings, key=len)


def longest_substr(strings):
    """
    Returns the longest common substring of the given strings
    """

    substr = ""
    if not strings:
        return substr
    reference = shortest_of(strings)
    length = len(reference)
    # find a suitable slice i:j
    for i in range(length):
        # only consider strings long at least len(substr) + 1
        for j in range(i + len(substr) + 1, length):
            candidate = reference[i:j]
            if all(candidate in text for text in strings):
                substr = candidate
    return substr


def file_hash(f, h=hashlib.md5, block_size=2**20):
    """returns the hash of the contents of a file"""
    f_hash = h()
    while True:
        buf = f.read(block_size)
        if not buf:
            break
        f_hash.update(buf)

    return f_hash


def url_add_authentication(url, username, password):
    """
    Adds authentication data (username, password) to a given
    URL in order to construct an authenticated URL.

    >>> url_add_authentication('https://host.com/', '', None)
    'https://host.com/'
    >>> url_add_authentication('http://example.org/', None, None)
    'http://example.org/'
    >>> url_add_authentication('telnet://host.com/', 'foo', 'bar')
    'telnet://foo:bar@host.com/'
    >>> url_add_authentication('ftp://example.org', 'billy', None)
    'ftp://billy@example.org'
    >>> url_add_authentication('ftp://example.org', 'billy', '')
    'ftp://billy:@example.org'
    >>> url_add_authentication('http://localhost/x', 'aa', 'bc')
    'http://aa:bc@localhost/x'
    >>> url_add_authentication('http://blubb.lan/u.html', 'i/o', 'P@ss:')
    'http://i%2Fo:P@ss:@blubb.lan/u.html'
    >>> url_add_authentication('http://a:b@x.org/', 'c', 'd')
    'http://c:d@x.org/'
    >>> url_add_authentication('http://i%2F:P%40%3A@cx.lan', 'P@x', 'i/')
    'http://P@x:i%2F@cx.lan'
    >>> url_add_authentication('http://x.org/', 'a b', 'c d')
    'http://a%20b:c%20d@x.org/'
    """
    if username is None or username == "":
        return url

    # Relaxations of the strict quoting rules (bug 1521):
    # 1. Accept '@' in username and password
    # 2. Acecpt ':' in password only
    username = urllib.parse.quote(username, safe="@")

    if password is not None:
        password = urllib.parse.quote(password, safe="@:")
        auth_string = ":".join((username, password))
    else:
        auth_string = username

    url = url_strip_authentication(url)

    url_parts = list(urllib.parse.urlsplit(url))
    # url_parts[1] is the HOST part of the URL
    url_parts[1] = "@".join((auth_string, url_parts[1]))

    return urllib.parse.urlunsplit(url_parts)


def urlopen(url, headers=None, data=None):
    """
    An URL opener with the User-agent set to gPodder (with version)
    """
    username, password = username_password_from_url(url)
    if username is not None or password is not None:
        url = url_strip_authentication(url)
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url, username, password)
        handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
        opener = urllib.request.build_opener(handler)
    else:
        opener = urllib.request.build_opener()

    if headers is None:
        headers = {}
    else:
        headers = dict(headers)

    headers.update({"User-agent": settings.USER_AGENT})
    request = urllib.request.Request(url, data=data, headers=headers)
    return opener.open(request)


def username_password_from_url(url):
    r"""
    Returns a tuple (username,password) containing authentication
    data from the specified URL or (None,None) if no authentication
    data can be found in the URL.

    See Section 3.1 of RFC 1738 (http://www.ietf.org/rfc/rfc1738.txt)

    >>> username_password_from_url('https://@host.com/')
    ('', None)
    >>> username_password_from_url('telnet://host.com/')
    (None, None)
    >>> username_password_from_url('ftp://foo:@host.com/')
    ('foo', '')
    >>> username_password_from_url('http://a:b@host.com/')
    ('a', 'b')
    >>> username_password_from_url(1)
    Traceback (most recent call last):
      ...
    ValueError: URL has to be a string or unicode object.
    >>> username_password_from_url(None)
    Traceback (most recent call last):
      ...
    ValueError: URL has to be a string or unicode object.
    >>> username_password_from_url('http://a@b:c@host.com/')
    ('a@b', 'c')
    >>> username_password_from_url('ftp://a:b:c@host.com/')
    ('a', 'b:c')
    >>> username_password_from_url('http://i%2Fo:P%40ss%3A@host.com/')
    ('i/o', 'P@ss:')
    >>> username_password_from_url('ftp://%C3%B6sterreich@host.com/')
    ('österreich', None)
    >>> username_password_from_url('http://w%20x:y%20z@example.org/')
    ('w x', 'y z')
    >>> username_password_from_url('http://example.com/x@y:z@test.com/')
    (None, None)
    """
    if type(url) not in (str, str):
        raise ValueError("URL has to be a string or unicode object.")

    (username, password) = (None, None)

    (scheme, netloc, path, params, query, fragment) = urllib.parse.urlparse(url)

    if "@" in netloc:
        (authentication, netloc) = netloc.rsplit("@", 1)
        if ":" in authentication:
            (username, password) = authentication.split(":", 1)

            # RFC1738 dictates that we should not allow ['/', '@', ':']
            # characters in the username and password field (Section 3.1):
            #
            # 1. The "/" can't be in there at this point because of the way
            #    urlparse (which we use above) works.
            # 2. Due to gPodder bug 1521, we allow "@" in the username and
            #    password field. We use netloc.rsplit('@', 1), which will
            #    make sure that we split it at the last '@' in netloc.
            # 3. The colon must be excluded (RFC2617, Section 2) in the
            #    username, but is apparently allowed in the password. This
            #    is handled by the authentication.split(':', 1) above, and
            #    will cause any extraneous ':'s to be part of the password.

            username = urllib.parse.unquote(username)
            password = urllib.parse.unquote(password)
        else:
            username = urllib.parse.unquote(authentication)

    return (username, password)


def url_strip_authentication(url):
    """
    Strips authentication data from an URL. Returns the URL with
    the authentication data removed from it.

    >>> url_strip_authentication('https://host.com/')
    'https://host.com/'
    >>> url_strip_authentication('telnet://foo:bar@host.com/')
    'telnet://host.com/'
    >>> url_strip_authentication('ftp://billy@example.org')
    'ftp://example.org'
    >>> url_strip_authentication('ftp://billy:@example.org')
    'ftp://example.org'
    >>> url_strip_authentication('http://aa:bc@localhost/x')
    'http://localhost/x'
    >>> url_strip_authentication('http://i%2Fo:P%40ss%3A@blubb.lan/u.html')
    'http://blubb.lan/u.html'
    >>> url_strip_authentication('http://c:d@x.org/')
    'http://x.org/'
    >>> url_strip_authentication('http://P%40%3A:i%2F@cx.lan')
    'http://cx.lan'
    >>> url_strip_authentication('http://x@x.com:s3cret@example.com/')
    'http://example.com/'
    """
    url_parts = list(urllib.parse.urlsplit(url))
    # url_parts[1] is the HOST part of the URL

    # Remove existing authentication data
    if "@" in url_parts[1]:
        url_parts[1] = url_parts[1].rsplit("@", 1)[1]

    return urllib.parse.urlunsplit(url_parts)


# Native filesystem encoding detection
encoding = sys.getfilesystemencoding()


def get_git_head():
    """returns the commit and message of the current git HEAD"""

    try:
        pr = subprocess.Popen(
            "/usr/bin/git log -n 1 --oneline".split(),
            cwd=settings.BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    except OSError:
        return None, None

    (out, err) = pr.communicate()
    if err:
        return None, None

    outs = [o.decode("utf-8") for o in out.split()]
    commit = outs[0]
    msg = " ".join(outs[1:])
    return commit, msg


def parse_request_body(request):
    """returns the parsed request body, handles gzip encoding"""

    raw_body = request.body
    content_enc = request.META.get("HTTP_CONTENT_ENCODING")

    if content_enc == "gzip":
        raw_body = zlib.decompress(raw_body)

    return json.loads(raw_body.decode("utf-8"))


def normalize_feed_url(url):
    """
    Converts any URL to http:// or ftp:// so that it can be
    used with "wget". If the URL cannot be converted (invalid
    or unknown scheme), "None" is returned.

    This will also normalize feed:// and itpc:// to http://.

    >>> normalize_feed_url('itpc://example.org/podcast.rss')
    'http://example.org/podcast.rss'

    If no URL scheme is defined (e.g. "curry.com"), we will
    simply assume the user intends to add a http:// feed.

    >>> normalize_feed_url('curry.com')
    'http://curry.com/'

    There are even some more shortcuts for advanced users
    and lazy typists (see the source for details).

    >>> normalize_feed_url('fb:43FPodcast')
    'http://feeds.feedburner.com/43FPodcast'

    It will also take care of converting the domain name to
    all-lowercase (because domains are not case sensitive):

    >>> normalize_feed_url('http://Example.COM/')
    'http://example.com/'

    Some other minimalistic changes are also taken care of,
    e.g. a ? with an empty query is removed:

    >>> normalize_feed_url('http://example.org/test?')
    'http://example.org/test'

    Leading and trailing whitespace is removed

    >>> normalize_feed_url(' http://example.com/podcast.rss ')
    'http://example.com/podcast.rss'

    HTTP Authentication is removed to protect users' privacy

    >>> normalize_feed_url('http://a@b:c@host.com/')
    'http://host.com/'
    >>> normalize_feed_url('ftp://a:b:c@host.com/')
    'ftp://host.com/'
    >>> normalize_feed_url('http://i%2Fo:P%40ss%3A@host.com/')
    'http://host.com/'
    >>> normalize_feed_url('ftp://%C3%B6sterreich@host.com/')
    'ftp://host.com/'
    >>> normalize_feed_url('http://w%20x:y%20z@example.org/')
    'http://example.org/'
    >>> normalize_feed_url('http://example.com/x@y:z@test.com/')
    'http://example.com/x%40y%3Az%40test.com/'
    >>> normalize_feed_url('http://en.wikipedia.org/wiki/Ä')
    'http://en.wikipedia.org/wiki/%C3%84'
    >>> normalize_feed_url('http://en.wikipedia.org/w/index.php?title=Ä&action=edit')
    'http://en.wikipedia.org/w/index.php?title=%C3%84&action=edit'
    """
    url = url.strip()
    if not url or len(url) < 8:
        # Branch ID: 0
        coverage[0] = True
        return None

    # This is a list of prefixes that you can use to minimize the amount of
    # keystrokes that you have to use.
    # Feel free to suggest other useful prefixes, and I'll add them here.
    PREFIXES = {
        "fb:": "http://feeds.feedburner.com/%s",
        "yt:": "http://www.youtube.com/rss/user/%s/videos.rss",
        "sc:": "http://soundcloud.com/%s",
        "fm4od:": "http://onapp1.orf.at/webcam/fm4/fod/%s.xspf",
        # YouTube playlists. To get a list of playlists per-user, use:
        # https://gdata.youtube.com/feeds/api/users/<username>/playlists
        "ytpl:": "http://gdata.youtube.com/feeds/api/playlists/%s",
    }

    for prefix, expansion in PREFIXES.items():
        if url.startswith(prefix):
            # Branch ID: 1
            coverage[1] = True
            url = expansion % (url[len(prefix) :],)
            break
        else:
            # Branch ID: 2
            coverage[2] = True

    # Assume HTTP for URLs without scheme
    if not "://" in url:
        # Branch ID: 2
        coverage[3] = True
        url = "http://" + url
    else:
        # Branch ID: 3
        coverage[4] = True

    scheme, netloc, path, query, fragment = urllib.parse.urlsplit(url)

    # Schemes and domain names are case insensitive
    scheme, netloc = scheme.lower(), netloc.lower()

    # encode non-encoded characters
    path = urllib.parse.quote(path, "/%")
    query = urllib.parse.quote_plus(query, ":&=")

    # Remove authentication to protect users' privacy
    netloc = netloc.rsplit("@", 1)[-1]

    # Normalize empty paths to "/"
    if path == "":
        # Branch ID: 3
        coverage[5] = True
        path = "/"
    else:
        # Branch ID: 4
        coverage[6] = True

    # feed://, itpc:// and itms:// are really http://
    if scheme in ("feed", "itpc", "itms"):
        # Branch ID: 4
        coverage[7] = True
        scheme = "http"
    else:
        # Branch ID: 5
        coverage[8] = True

    if scheme not in ("http", "https", "ftp", "file"):
        # Branch ID: 5
        coverage[9] = True
        return None
    else:
        # Branch ID: 6
        coverage[10] = True

    # urlunsplit might return "a slighty different, but equivalent URL"
    return urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))


def normalize_url(url, coverage): #used for testing above function
    """
    Converts any URL to http:// or ftp:// so that it can be
    used with "wget". If the URL cannot be converted (invalid
    or unknown scheme), "None" is returned.

    This will also normalize feed:// and itpc:// to http://.

    >>> normalize_feed_url('itpc://example.org/podcast.rss')
    'http://example.org/podcast.rss'

    If no URL scheme is defined (e.g. "curry.com"), we will
    simply assume the user intends to add a http:// feed.

    >>> normalize_feed_url('curry.com')
    'http://curry.com/'

    There are even some more shortcuts for advanced users
    and lazy typists (see the source for details).

    >>> normalize_feed_url('fb:43FPodcast')
    'http://feeds.feedburner.com/43FPodcast'

    It will also take care of converting the domain name to
    all-lowercase (because domains are not case sensitive):

    >>> normalize_feed_url('http://Example.COM/')
    'http://example.com/'

    Some other minimalistic changes are also taken care of,
    e.g. a ? with an empty query is removed:

    >>> normalize_feed_url('http://example.org/test?')
    'http://example.org/test'

    Leading and trailing whitespace is removed

    >>> normalize_feed_url(' http://example.com/podcast.rss ')
    'http://example.com/podcast.rss'

    HTTP Authentication is removed to protect users' privacy

    >>> normalize_feed_url('http://a@b:c@host.com/')
    'http://host.com/'
    >>> normalize_feed_url('ftp://a:b:c@host.com/')
    'ftp://host.com/'
    >>> normalize_feed_url('http://i%2Fo:P%40ss%3A@host.com/')
    'http://host.com/'
    >>> normalize_feed_url('ftp://%C3%B6sterreich@host.com/')
    'ftp://host.com/'
    >>> normalize_feed_url('http://w%20x:y%20z@example.org/')
    'http://example.org/'
    >>> normalize_feed_url('http://example.com/x@y:z@test.com/')
    'http://example.com/x%40y%3Az%40test.com/'
    >>> normalize_feed_url('http://en.wikipedia.org/wiki/Ä')
    'http://en.wikipedia.org/wiki/%C3%84'
    >>> normalize_feed_url('http://en.wikipedia.org/w/index.php?title=Ä&action=edit')
    'http://en.wikipedia.org/w/index.php?title=%C3%84&action=edit'
    """
    url = url.strip()
    if not url or len(url) < 8:
        # Branch ID: 0
        coverage[0] = True
        return None

    # This is a list of prefixes that you can use to minimize the amount of
    # keystrokes that you have to use.
    # Feel free to suggest other useful prefixes, and I'll add them here.
    PREFIXES = {
        "fb:": "http://feeds.feedburner.com/%s",
        "yt:": "http://www.youtube.com/rss/user/%s/videos.rss",
        "sc:": "http://soundcloud.com/%s",
        "fm4od:": "http://onapp1.orf.at/webcam/fm4/fod/%s.xspf",
        # YouTube playlists. To get a list of playlists per-user, use:
        # https://gdata.youtube.com/feeds/api/users/<username>/playlists
        "ytpl:": "http://gdata.youtube.com/feeds/api/playlists/%s",
    }

    for prefix, expansion in PREFIXES.items():
        if url.startswith(prefix):
            # Branch ID: 1
            coverage[1] = True
            url = expansion % (url[len(prefix) :],)
            break
        else:
            # Branch ID: 2
            coverage[2] = True

    # Assume HTTP for URLs without scheme
    if not "://" in url:
        # Branch ID: 2
        coverage[3] = True
        url = "http://" + url
    else:
        # Branch ID: 3
        coverage[4] = True

    scheme, netloc, path, query, fragment = urllib.parse.urlsplit(url)

    # Schemes and domain names are case insensitive
    scheme, netloc = scheme.lower(), netloc.lower()

    # encode non-encoded characters
    path = urllib.parse.quote(path, "/%")
    query = urllib.parse.quote_plus(query, ":&=")

    # Remove authentication to protect users' privacy
    netloc = netloc.rsplit("@", 1)[-1]

    # Normalize empty paths to "/"
    if path == "":
        # Branch ID: 3
        coverage[5] = True
        path = "/"
    else:
        # Branch ID: 4
        coverage[6] = True

    # feed://, itpc:// and itms:// are really http://
    if scheme in ("feed", "itpc", "itms"):
        # Branch ID: 4
        coverage[7] = True
        scheme = "http"
    else:
        # Branch ID: 5
        coverage[8] = True

    if scheme not in ("http", "https", "ftp", "file"):
        # Branch ID: 5
        coverage[9] = True
        return None
    else:
        # Branch ID: 6
        coverage[10] = True

    # urlunsplit might return "a slighty different, but equivalent URL"
    return urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))


def edit_link(obj):
    """Return the link to the Django Admin Edit page"""
    return reverse(
        "admin:%s_%s_change" % (obj._meta.app_label, obj._meta.model_name),
        args=(obj.pk,),
    )


def random_token(length=32):
    import random
    import string

    return "".join(random.sample(string.ascii_letters + string.digits, length))


def to_maxlength(cls, field, val):
    """Cut val to the maximum length of cls's field"""
    if val is None:
        return None

    max_length = cls._meta.get_field(field).max_length
    orig_length = len(val)
    if orig_length > max_length:
        val = val[:max_length]
        logger.warning(
            "%s.%s length reduced from %d to %d",
            cls.__name__,
            field,
            orig_length,
            max_length,
        )

    return val


def get_domain(url):
    """Returns the domain name of a URL

    >>> get_domain('http://example.com')
    'example.com'

    >>> get_domain('https://example.com:80/my-podcast/feed.rss')
    'example.com'
    """
    netloc = urllib.parse.urlparse(url).netloc
    try:
        port_idx = netloc.index(":")
        return netloc[:port_idx]

    except ValueError:
        return netloc


def set_ordered_entries(
    obj, new_entries, existing, EntryClass, value_name, parent_name
):
    """Update the object's entries to the given list

    'new_entries' should be a list of objects that are later wrapped in
    EntryClass instances. 'value_name' is the name of the EntryClass property
    that contains the values; 'parent_name' is the one that references obj.

    Entries that do not exist are created. Existing entries that are not in
    'new_entries' are deleted."""

    logger.info("%d existing entries", len(existing))

    logger.info("%d new entries", len(new_entries))

    with transaction.atomic():
        max_order = max([s.order for s in existing.values()] + [len(new_entries)])
        logger.info("Renumbering entries starting from %d", max_order + 1)
        for n, entry in enumerate(existing.values(), max_order + 1):
            entry.order = n
            entry.save()

    logger.info("%d existing entries", len(existing))

    for n, entry in enumerate(new_entries):
        try:
            e = existing.pop(entry)
            logger.info("Updating existing entry %d: %s", n, entry)
            e.order = n
            e.save()
        except KeyError:
            logger.info("Creating new entry %d: %s", n, entry)
            try:
                links = {value_name: entry, parent_name: obj}
                from mygpo.podcasts.models import ScopedModel

                if issubclass(EntryClass, ScopedModel):
                    links["scope"] = obj.scope

                EntryClass.objects.create(order=n, **links)
            except IntegrityError as ie:
                logger.warning("Could not create enry for %s: %s", obj, ie)

    with transaction.atomic():
        delete = [s.pk for s in existing.values()]
        logger.info("Deleting %d entries", len(delete))
        EntryClass.objects.filter(id__in=delete).delete()
