
from django.db.models import Sum
from django.views.decorators.cache import never_cache
from django.utils.html import strip_tags

from mygpo.api.models import Podcast, EpisodeAction
from babel import Locale, UnknownLocaleError
from datetime import datetime
import re

def get_accepted_lang(request):
    return list(set([s[:2] for s in request.META.get('HTTP_ACCEPT_LANGUAGE', '').split(',')]))

def get_podcast_languages():
    """
    Returns all 2-letter language codes that are used by podcasts.

    It filters obviously invalid strings, but does not check if any
    of these codes is contained in ISO 639.
    """

    langs = [x['language'] for x in Podcast.objects.values('language').distinct()]
    sane_lang = sanitize_language_codes(langs)

    sane_lang.sort()

    return sane_lang


def sanitize_language_codes(langs):
    """
    expects a list of language codes and returns a unique lost of the first
    part of all items. obviously invalid entries are skipped

    >>> sanitize_language_codes(['de-at', 'de-ch'])
    ['de']

    >>> sanitize_language_codes(['de-at', 'en', 'en-gb', '(asdf', 'Deutsch'])
    ['de', 'en']
    """

    r = '^[a-zA-Z]{2}[-_]?.*$'
    return list(set([l[:2].lower() for l in langs if l and re.match(r, l)]))


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


class UpdatedException(Exception):
    """Base exception with additional payload"""
    def __init__(self, data):
        Exception.__init__(self)
        self.data = data


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
        add = show_max / 2 - len(ps) # for the first pages, show more pages at the beginning
        ps.extend(range(cur + 1, cur + show_max / 4 + add))
        ps.append('...')
        ps.extend(range(total - show_max / 4, total + 1))

    else:
        ps.extend(range(cur + 1, total + 1))

    return ps


def process_lang_params(request, url):
    if 'lang' in request.GET:
        lang = list(set([x for x in request.GET.get('lang').split(',') if x]))

    if request.method == 'POST':
        if request.POST.get('lang'):
            lang = list(set(lang + [request.POST.get('lang')]))
        raise UpdatedException(lang)

    if not 'lang' in request.GET:
        lang = get_accepted_lang(request)

    return sanitize_language_codes(lang)


def symbian_opml_changes(podcast):
    podcast.description = (podcast.title or '') + '\n' \
                        + (podcast.description or '')
    return podcast


@never_cache
def maintenance(request, *args, **kwargs):
    from django.shortcuts import render_to_response
    from django.template import RequestContext

    resp = render_to_response('maintenance.html', {},
        context_instance=RequestContext(request))
    resp.status_code = 503
    return resp


def get_podcast_link_target(podcast, view_name='podcast', add_args=[]):
    """ Returns the link-target for a Podcast, preferring slugs over Ids

    automatically distringuishes between relational Podcast objects and
    CouchDB-based Podcasts """

    from mygpo.api.models import Podcast as OldPodcast
    from mygpo.core.models import Podcast
    from django.core.urlresolvers import reverse

    # for old-podcasts we link to its id
    if isinstance(podcast, OldPodcast):
        args = [podcast.id]

    # we prefer slugs
    elif podcast.slug:
        args = [podcast.slug]
        view_name = '%s-slug-id' % view_name

    # to keep URLs short, we use use oldids
    elif podcast.oldid:
        args = [podcast.oldid]

    # as a fallback we use CouchDB-IDs
    else:
        args = [podcast.get_id()]
        view_name = '%s-slug-id' % view_name

    return reverse(view_name, args=args + add_args)


def get_episode_link_target(episode, podcast=None, view_name='episode', add_args=[]):
    """ Returns the link-target for an Episode, preferring slugs over Ids

    automatically distringuishes between relational Episode objects and
    CouchDB-based Episodes """

    from mygpo.api.models import Episode as OldEpisode
    from mygpo.core.models import Episode
    from django.core.urlresolvers import reverse

    # for old-podcasts there is no choice, link to oldid
    if isinstance(episode, OldEpisode):
        args = [episode.id]

    # prefer slugs
    elif episode.slug:
        if not podcast:
            podcast = Podcast.get(episode.podcast)

        args = [podcast.slug or podcast.get_id(), episode.slug]
        view_name = '%s-slug-id' % view_name

    # for short URLs, prefer oldids over CouchDB-IDs
    elif episode.oldid:
        args = [episode.oldid]

    # fallback: CouchDB-IDs
    else:
        if not podcast:
            podcast = Podcast.get(episode.podcast)

        args = [podcast.slug or podcast.get_id(), episode._id]
        view_name = '%s-slug-id' % view_name

    return strip_tags(reverse(view_name, args=args + add_args))
