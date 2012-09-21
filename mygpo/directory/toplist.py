from itertools import product

from datetime import date, timedelta

from django.core.cache import cache

from mygpo.core.models import Episode, Podcast, PodcastGroup
from mygpo.data.mimetype import get_type, CONTENT_TYPES
from mygpo.utils import daterange
from mygpo.db.couchdb.directory import toplist


CACHE_SECONDS = 60*60

class Toplist(object):
    """ Base class for Episode and Podcast toplists """

    def __init__(self, cls, view, language='', view_args={}):
        self.cls       = cls
        self.language  = language
        self.view      = view
        self.view_args = view_args


    def _get_query_keys(self):
        """ Returns an iterator of query keys that are passed to the view """
        return [self.language]


    def _query(self, limit):
        """ Queries the database and returns the sorted results """

        key = self._get_query_keys()
        results = self._cache_or_query(limit, key)
        results = self._sort(results)
        return results[:limit]


    def _cache_or_query(self, limit, key):
        return toplist(self.cls, self.view, key, limit, self.view_args)


    def _sort(self, results):
        return results


    def __getitem__(self, key):
        if isinstance(key, slice):
            start = key.start or 0
            length = key.stop - start
        else:
            start = key
            length = 1

        return self._query(length)



class EpisodeToplist(Toplist):
    """ Retrieves the episode toplist for a certain date """

    def __init__(self, language='', startdate=None):
        super(EpisodeToplist, self).__init__(Episode,
                'toplist/episodes', language)
        self.date = startdate or date.today()


    def _sort(self, results):
        results.sort(key=lambda episode: episode.listeners, reverse=True)
        return results


    def _get_query_keys(self):
        """ Returns the query keys based on instance variables """

        date_str = self.date.strftime('%Y-%m-%d')
        return [date_str] + super(EpisodeToplist, self)._get_query_keys()



class PodcastToplist(Toplist):
    """ Podcast toplist based on number of subscribers """

    def __init__(self, language=''):
        super(PodcastToplist, self).__init__(Podcast, 'toplist/podcasts',
                language,
                view_args=dict(classes=[Podcast, PodcastGroup]))


    def _sort(self, results):
        # sort by subscriber_count and id to ensure same order when subscriber_count is equal
        cur  = sorted(results, key=lambda p: (p.subscriber_count(), p.get_id()),      reverse=True)
        prev = sorted(results, key=lambda p: (p.prev_subscriber_count(), p.get_id()), reverse=True)

        res = dict( (p, n) for n, p in enumerate(cur))

        for old, p in enumerate(prev):
            new = res.get(p, 0)
            res[p] = (new, old)

        return [(old+1, p) for p, (new, old) in sorted(res.items(), key=lambda i: i[1][0])]


class TrendingPodcasts(Toplist):
    """ Trending podcasts based on current / previous subscribers ratio """

    def __init__(self, language=''):
        super(TrendingPodcasts, self).__init__(Podcast, 'trending/podcasts',
                language,
                view_args=dict(classes=[Podcast, PodcastGroup]))
