from itertools import product

from datetime import date, timedelta

from mygpo.core.models import Episode, Podcast, PodcastGroup
from mygpo.data.mimetype import get_type, CONTENT_TYPES
from mygpo.utils import daterange


class Toplist(object):
    """ Base class for Episode and Podcast toplists """

    def __init__(self, cls, view, languages=[], types=[], view_args={}):
        self.cls       = cls
        self.languages = languages
        self.view      = view
        self.view_args = view_args

        if len(types) == len(CONTENT_TYPES):
            self.types = []
        else:
            self.types = types


    def _get_query_keys(self):
        """ Returns an iterator of query keys that are passed to the view """

        if not self.languages and not self.types:
            yield ["none"]

        elif self.languages and not self.types:
            for lang in self.languages:
                yield ["language", lang]

        elif not self.languages and self.types:
            for type in self.types:
                yield ["type", type]

        else:
            for typ, lang in product(self.types, self.languages):
                yield ["type-language", typ, lang]


    def _query(self, skip, limit):
        """ Queries the database and returns the sorted results """

        results = []
        for key in self._get_query_keys():
            r = self.cls.view(self.view,
                    startkey     = key + [{}],
                    endkey       = key + [None],
                    include_docs = True,
                    descending   = True,
                    limit        = limit + skip,
                    **self.view_args
                )
            results.extend(list(r))

        results = list(set(results))
        results = self._sort(results)
        return results[skip:skip+limit]


    def _sort(self, results):
        return results


    def __getitem__(self, key):
        if isinstance(key, slice):
            start = key.start or 0
            length = key.stop - start
        else:
            start = key
            length = 1

        return self._query(start, length)



class EpisodeToplist(Toplist):
    """ Retrieves the episode toplist for a certain date """

    def __init__(self, languages=[], types=[], startdate=None):
        super(EpisodeToplist, self).__init__(Episode,
                'directory/episode_toplist', languages, types)
        self.date = startdate or date.today()


    def _sort(self, results):
        results.sort(key=lambda episode: episode.listeners, reverse=True)
        return results


    def _get_query_keys(self):
        """ Returns the query keys based on instance variables """

        date_str = self.date.strftime('%Y-%m-%d')

        for criteria in super(EpisodeToplist, self)._get_query_keys():
            yield [date_str] + criteria



class PodcastToplist(Toplist):
    """ Podcast toplist based on number of subscribers """

    # FIXME: podcast and episode toplist are separated now, so we could
    # get rid of the type field
    TYPE = 'Podcast'

    def __init__(self, languages=[], types=[]):
        super(PodcastToplist, self).__init__(Podcast, 'directory/toplist',
                languages, types,
                view_args=dict(classes=[Podcast, PodcastGroup]))


    def _get_query_keys(self):
        for criteria in super(PodcastToplist, self)._get_query_keys():
            yield [self.TYPE] + criteria


    def _sort(self, results):
        # sort by subscriber_count and id to ensure same order when subscriber_count is equal
        cur  = sorted(results, key=lambda p: (p.subscriber_count(), p.get_id()),      reverse=True)
        prev = sorted(results, key=lambda p: (p.prev_subscriber_count(), p.get_id()), reverse=True)

        res = dict( (p, n) for n, p in enumerate(cur))

        for old, p in enumerate(prev):
            new = res.get(p, 0)
            res[p] = (new, old)

        return [(old+1, p) for p, (new, old) in sorted(res.items(), key=lambda i: i[1][0])]
