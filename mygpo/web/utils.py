import re
import string
from datetime import datetime

from django.views.decorators.cache import never_cache
from django.utils.html import strip_tags
from django.core.urlresolvers import reverse
from django.shortcuts import render

from babel import Locale, UnknownLocaleError

from mygpo.core.models import Podcast
from mygpo.core.proxy import proxy_object
from mygpo.db.couchdb.podcast import podcast_by_id, podcasts_to_dict


def get_accepted_lang(request):
    """ returns a list of language codes accepted by the HTTP request """

    lang_str = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    lang_str = filter(lambda c: c in string.letters+',', lang_str)
    langs = lang_str.split(',')
    langs = [s[:2] for s in langs]
    langs = map(str.strip, langs)
    langs = filter(None, langs)
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

    >>> sanitize_language_codes(['de-at', 'en', 'en-gb', '(asdf', 'Deutsch'])
    ['de', 'en']
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

    >>> get_page_list(1, 100, 50, 10)
    [1, '...', 48, 49, 50, 51, '...', 98, 99, 100]

    >>> get_page_list(1, 100, 99, 10)
    [1, '...', 97, 98, 99, 100]

    >>> get_page_list(1, 3, 2, 10)
    [1, 2, 3]
    """

    if show_max >= (total - start):
        return range(start, total+1)

    ps = []
    if (cur - start) > show_max / 2:
        ps.extend(range(start, show_max / 4))
        ps.append('...')
        ps.extend(range(cur - show_max / 4, cur))

    else:
        ps.extend(range(start, cur))

    ps.append(cur)

    if (total - cur) > show_max / 2:
        # for the first pages, show more pages at the beginning
        add = show_max / 2 - len(ps)
        ps.extend(range(cur + 1, cur + show_max / 4 + add))
        ps.append('...')
        ps.extend(range(total - show_max / 4, total + 1))

    else:
        ps.extend(range(cur + 1, total + 1))

    return ps


def process_lang_params(request):

    lang = request.GET.get('lang', None)

    if lang is None:
        langs = get_accepted_lang(request)
        lang = next(iter(langs), '')

    return sanitize_language_code(lang)


def symbian_opml_changes(podcast):
    podcast.description = (podcast.title or '') + '\n' + \
                          (podcast.description or '')
    return podcast


@never_cache
def maintenance(request, *args, **kwargs):
    resp = render(request, 'maintenance.html', {})
    resp.status_code = 503
    return resp


def get_podcast_link_target(podcast, view_name='podcast', add_args=[]):
    """ Returns the link-target for a Podcast, preferring slugs over Ids

    automatically distringuishes between relational Podcast objects and
    CouchDB-based Podcasts """

    from mygpo.core.models import Podcast

    # we prefer slugs
    if podcast.slug:
        args = [podcast.slug]
        view_name = '%s-slug-id' % view_name

    # as a fallback we use CouchDB-IDs
    else:
        args = [podcast.get_id()]
        view_name = '%s-slug-id' % view_name

    return reverse(view_name, args=args + add_args)


def get_podcast_group_link_target(group, view_name, add_args=[]):
    """ Returns the link-target for a Podcast group, preferring slugs over Ids

    automatically distringuishes between relational Podcast objects and
    CouchDB-based Podcasts """

    from mygpo.core.models import PodcastGroup

    # we prefer slugs
    if group.slug:
        args = [group.slug]
        view_name = '%s-slug-id' % view_name

    # to keep URLs short, we use use oldids
    elif group.oldid:
        args = [group.oldid]

    # as a fallback we use CouchDB-IDs
    else:
        args = [group._id]
        view_name = '%s-slug-id' % view_name

    return reverse(view_name, args=args + add_args)


def get_episode_link_target(episode, podcast, view_name='episode',
                            add_args=[]):
    """ Returns the link-target for an Episode, preferring slugs over Ids

    automatically distringuishes between relational Episode objects and
    CouchDB-based Episodes """

    from mygpo.core.models import Podcast

    # prefer slugs
    if episode.slug:
        args = [podcast.slug or podcast.get_id(), episode.slug]
        view_name = '%s-slug-id' % view_name

    # for short URLs, prefer oldids over CouchDB-IDs
    elif episode.oldid:
        args = [episode.oldid]

    # fallback: CouchDB-IDs
    else:
        if not podcast:
            if isinstance(episode.podcast, Podcast):
                podcast = episode.podcast
            elif isinstance(episode.podcast, basestring):
                podcast = podcast_by_id(episode.podcast)

        args = [podcast.slug or podcast.get_id(), episode._id]
        view_name = '%s-slug-id' % view_name

    return strip_tags(reverse(view_name, args=args + add_args))


def fetch_episode_data(episodes, podcasts={}):

    if not podcasts:
        podcast_ids = [episode.podcast for episode in episodes]
        podcasts = podcasts_to_dict(podcast_ids)

    def set_podcast(episode):
        episode = proxy_object(episode)
        episode.podcast = podcasts.get(episode.podcast, None)
        return episode

    return map(set_podcast, episodes)


# doesn't include the '@' because it's not stored as part of a twitter handle
TWITTER_CHARS = string.ascii_letters + string.digits + '_'


def normalize_twitter(s):
    """ normalize user input that is supposed to be a Twitter handle """
    return "".join(i for i in s if i in TWITTER_CHARS)
