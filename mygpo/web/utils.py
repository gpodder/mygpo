
from django.db.models import Sum

from mygpo.api.models import Podcast, EpisodeAction
from mygpo.data.models import Listener
from mygpo.web.models import Advertisement
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


def get_played_parts(user, episode):
    """
    return a list of length of alternating unplayed, played parts of the given
    episode for the given user and the resulting duration of the episode

    If no information is available, None and the stored duration of the episode
    are returned
    """
    actions = EpisodeAction.objects.filter(episode=episode, user=user, action='play', playmark__isnull=False, started__isnull=False)

    if actions.count() == 0:
        return None, episode.duration

    lengths = [x.total for x in actions]
    median_length = lengths[len(lengths)/2]

    # flatten (merge) all play-parts
    played_parts = flatten_intervals(actions)

    # if end of last played part exceeds median length, extend episode
    if played_parts:
        length = max(median_length, played_parts[len(played_parts)-1]['end'])
    else:
        return None, episode.duration

    #split up the played parts in alternating 'unplayed' and 'played'
    #sections, starting with an unplayed
    sections = []

    lastpos = 0
    for played_part in played_parts:
        sections.append(played_part['start'] - lastpos)
        sections.append(played_part['end'] - played_part['start'])
        lastpos = played_part['end']

    intsections = [int(s) for s in sections]

    return intsections, length


def flatten_intervals(actions):
    """
    takes a list of EpisodeActions and returns a sorted
    list of hashtables with start end elements of the flattened
    play intervals.
    """
    actions = filter(lambda x: x.started != None and x.playmark != None, actions)
    actions.sort(key=lambda x: x.started)
    played_parts = []
    if len(actions) == 0:
        return []

    first = actions[0]
    flat_date = {'start': first.started, 'end': first.playmark}
    for action in actions:
        if action.started <= flat_date['end'] and action.playmark >= flat_date['end']:
            flat_date['end'] = action.playmark
        elif action.started >= flat_date['start'] and action.playmark <= flat_date['end']:
            # part already contained
            continue
        else:
            played_parts.append(flat_date)
            flat_date = {'start': action.started, 'end': action.playmark}
    played_parts.append(flat_date)
    return played_parts


def get_sponsored_podcast(when=datetime.now):
    adv = Advertisement.objects.filter(start__lte=when, end__gte=when)

    if not adv.exists():
        return None
    else:
        return adv[0]


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


def get_hours_listened():
    seconds = Listener.objects.all().aggregate(hours=Sum('episode__duration'))['hours']
    if seconds == None:
        return 0
    else:
        return seconds / (60 * 60)
