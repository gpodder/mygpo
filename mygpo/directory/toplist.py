from itertools import product

from datetime import date, timedelta

from mygpo.core.models import Episode
from mygpo.utils import daterange


class EpisodeToplist(object):
    """ Retrieves the episode toplist for a certain time period """

    def __init__(self, startdate=None, languages=[], types=[]):
        """ Set the covered period of the toplist

        The covered period starts at startdate and reaches back for
        the time given by timespan """

        self.date = startdate or date.today()
        self.languages = languages
        self.types = types


    def _query(self, skip, limit):
        """ Queries the database and returns the episodes

        The Episodes are sorted in descreasing order of listeners """

        date_str = self.date.strftime('%Y-%m-%d')

        episodes = []
        for key in self._get_query_keys():
            r = Episode.view('directory/episode_toplist',
                    startkey     = key + [{}],
                    endkey       = key + [None],
                    include_docs = True,
                    descending   = True,
                    limit        = limit,
                    skip         = skip,
                )
            episodes.extend(list(r))

        episodes.sort(key=lambda e: e.listeners, reverse=True)
        return episodes[:limit]


    def _get_query_keys(self):
        """ Returns the query keys based on instance variables """

        date_str = self.date.strftime('%Y-%m-%d')

        criteria = []

        if not self.languages and not self.types:
            criteria.append( [date_str, "none"] )

        elif self.languages and not self.types:
            for lang in self.languages:
                criteria.append( [date_str, "language", lang] )

        elif not self.languages and self.types:
            for type in self.types:
                criteria.append( [date_str, "type", type] )

        else:
            for typ, lang in product(self.types, self.languages):
                criteria.append( [date_str, "type-language", typ, lang] )

        return criteria


    def __getitem__(self, key):
        if isinstance(key, slice):
            start = key.start or 0
            length = key.stop - start
        else:
            start = key
            length = 1

        return self._query(start, length)
