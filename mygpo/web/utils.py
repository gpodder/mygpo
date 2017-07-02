import re
import math
import string
import collections
from datetime import datetime

from django.utils.translation import ungettext
from django.views.decorators.cache import never_cache
from django.utils.html import strip_tags
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.http import Http404

from babel import Locale, UnknownLocaleError

from mygpo.podcasts.models import Podcast


def get_accepted_lang(request):
    """ returns a list of language codes accepted by the HTTP request """

    lang_str = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    lang_str = ''.join([c for c in lang_str if c in string.ascii_letters+','])
    langs = lang_str.split(',')
    langs = [s[:2] for s in langs]
    langs = list(map(str.strip, langs))
    langs = [_f for _f in langs if _f]
    return list(set(langs))


RE_LANG = re.compile('^[a-zA-Z]{2}[-_]?.*$')


def sanitize_language_code(lang):
    return lang[:2].lower()


def sanitize_language_codes(ls):
    """
    expects a list of language codes and returns a unique lost of the first
    part of all items. obviously invalid entries are skipped

    >>> sanitize_language_codes(['de-at', 'de-ch'])
    ['de']

    >>> set(sanitize_language_codes(['de-at', 'en', 'en-gb', '(asdf', 'Deutsch'])) == {'de', 'en'}
    True
    """

    ls = [sanitize_language_code(l) for l in ls if l and RE_LANG.match(l)]
    return list(set(ls))


def get_language_names(lang):
    """
    Takes a list of language codes and returns a list of tuples
    with (code, name)
    """
    res = {}
    for l in lang:
        try:
            locale = Locale(l)
        except UnknownLocaleError:
            continue

        if locale.display_name:
            res[l] = locale.display_name

    return res


def get_page_list(start, total, cur, show_max):
    """
    returns a list of pages to be linked for navigation in a paginated view

    >>> get_page_list(1, 100, 1, 10)
    [1, 2, 3, 4, 5, 6, '...', 98, 99, 100]

    >>> get_page_list(1, 995/10, 1, 10)
    [1, 2, 3, 4, 5, 6, '...', 98, 99, 100]

    >>> get_page_list(1, 100, 50, 10)
    [1, '...', 48, 49, 50, 51, '...', 98, 99, 100]

    >>> get_page_list(1, 100, 99, 10)
    [1, '...', 97, 98, 99, 100]

    >>> get_page_list(1, 3, 2, 10)
    [1, 2, 3]
    """

    # if we get "total" as a float (eg from total_entries / entries_per_page)
    # we round up
    total = math.ceil(total)

    if show_max >= (total - start):
        return list(range(start, total+1))

    ps = []
    if (cur - start) > show_max / 2:
        ps.extend(list(range(start, int(show_max / 4))))
        ps.append('...')
        ps.extend(list(range(cur - int(show_max / 4), cur)))

    else:
        ps.extend(list(range(start, cur)))

    ps.append(cur)

    if (total - cur) > show_max / 2:
        # for the first pages, show more pages at the beginning
        add = math.ceil(show_max / 2 - len(ps))
        ps.extend(list(range(cur + 1, cur + int(show_max / 4) + add)))
        ps.append('...')
        ps.extend(list(range(total - int(show_max / 4), total + 1)))

    else:
        ps.extend(list(range(cur + 1, total + 1)))

    return ps


def process_lang_params(request):

    lang = request.GET.get('lang', None)

    if lang is None:
        langs = get_accepted_lang(request)
        lang = next(iter(langs), '')

    return sanitize_language_code(lang)


def symbian_opml_changes(podcast):
    podcast.description = podcast.display_title + '\n' + \
                         (podcast.description or '')
    return podcast


@never_cache
def maintenance(request, *args, **kwargs):
    resp = render(request, 'maintenance.html', {})
    resp.status_code = 503
    return resp


def get_podcast_link_target(podcast, view_name='podcast', add_args=[]):
    """ Returns the link-target for a Podcast, preferring slugs over Ids """

    # we prefer slugs
    if podcast.slug:
        args = [podcast.slug]
        view_name = '%s-slug' % view_name

    # as a fallback we use UUIDs
    else:
        args = [podcast.get_id()]
        view_name = '%s-id' % view_name

    return reverse(view_name, args=args + add_args)


def get_podcast_group_link_target(group, view_name, add_args=[]):
    """ the link-target for a Podcast group, preferring slugs over Ids """
    args = [group.slug]
    view_name = '%s-slug-id' % view_name
    return reverse(view_name, args=args + add_args)


def get_episode_link_target(episode, podcast, view_name='episode',
                            add_args=[]):
    """ Returns the link-target for an Episode, preferring slugs over Ids """

    # prefer slugs
    if episode.slug:
        args = [podcast.slug, episode.slug]
        view_name = '%s-slug' % view_name

    # fallback: UUIDs
    else:
        podcast = podcast or episode.podcast
        args = [podcast.get_id(), episode.get_id()]
        view_name = '%s-id' % view_name

    return strip_tags(reverse(view_name, args=args + add_args))


# doesn't include the '@' because it's not stored as part of a twitter handle
TWITTER_CHARS = string.ascii_letters + string.digits + '_'


def normalize_twitter(s):
    """ normalize user input that is supposed to be a Twitter handle """
    return "".join(i for i in s if i in TWITTER_CHARS)


CCLICENSE = re.compile(r'http://(www\.)?creativecommons.org/licenses/([a-z-]+)/([0-9.]+)?/?')
CCPUBLICDOMAIN = re.compile(r'http://(www\.)?creativecommons.org/licenses/publicdomain/?')
LicenseInfo = collections.namedtuple('LicenseInfo', 'name version url')

def license_info(license_url):
    """ Extracts license information from the license URL

    >>> i = license_info('http://creativecommons.org/licenses/by/3.0/')
    >>> i.name
    'CC BY'
    >>> i.version
    '3.0'
    >>> i.url
    'http://creativecommons.org/licenses/by/3.0/'

    >>> iwww = license_info('http://www.creativecommons.org/licenses/by/3.0/')
    >>> i.name == iwww.name and i.version == iwww.version
    True

    >>> i = license_info('http://www.creativecommons.org/licenses/publicdomain')
    >>> i.name
    'Public Domain'
    >>> i.version is None
    True

    >>> i = license_info('http://example.com/my-own-license')
    >>> i.name is None
    True
    >>> i.version is None
    True
    >>> i.url
    'http://example.com/my-own-license'
    """
    m = CCLICENSE.match(license_url)
    if m:
        _, name, version = m.groups()
        return LicenseInfo('CC %s' % name.upper(), version, license_url)

    m = CCPUBLICDOMAIN.match(license_url)
    if m:
        return LicenseInfo('Public Domain', None, license_url)

    return LicenseInfo(None, None, license_url)


def check_restrictions(obj):
    """ checks for known restrictions of the object """

    restrictions = obj.restrictions.split(',')
    if "hide" in restrictions:
        raise Http404

    if "hide-author" in restrictions:
        obj.author = None

    return obj


def hours_to_str(hours_total):
    """ returns a human-readable string representation of some hours

    >>> hours_to_str(1)
    '1 hour'

    >>> hours_to_str(5)
    '5 hours'

    >>> hours_to_str(100)
    '4 days, 4 hours'

    >>> hours_to_str(960)
    '5 weeks, 5 days'

    >>> hours_to_str(961)
    '5 weeks, 5 days, 1 hour'
    """

    weeks = int(hours_total / 24 / 7)
    days = int(hours_total / 24) % 7
    hours = hours_total % 24

    strs = []

    if weeks:
        strs.append(ungettext('%(weeks)d week', '%(weeks)d weeks', weeks) %
            { 'weeks': weeks})

    if days:
        strs.append(ungettext('%(days)d day', '%(days)d days', days) %
            { 'days': days})

    if hours:
        strs.append(ungettext('%(hours)d hour', '%(hours)d hours', hours) %
            { 'hours': hours})

    return ', '.join(strs)
