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

    r = '^[a-zA-Z]{2}[-_]?.*$'

    langs = [x['language'] for x in Podcast.objects.values('language').distinct()]
    sane_lang = list(set([l[:2] for l in langs if l and re.match(r, l)]))

    sane_lang.sort()

    return sane_lang

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

