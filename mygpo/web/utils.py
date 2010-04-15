from mygpo.api.models import Podcast
from babel import Locale, UnknownLocaleError
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
    ['de', 'en]
    """

    r = '^[a-zA-Z]{2}[-_]?.*$'
    return list(set([l[:2] for l in langs if l and re.match(r, l)]))


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

