from datetime import date, timedelta

from mygpo.core.models import Episode
from mygpo.utils import daterange


class EpisodeToplist(object):
    """ Retrieves the episode toplist for a certain time period """

    def __init__(self, startdate=None):
        """ Set the covered period of the toplist

        The covered period starts at startdate and reaches back for
        the time given by timespan """

        self.date = startdate or date.today()


    def _query(self, skip, limit):
        """ Queries the database and returns the episodes

        The Episodes are sorted in descreasing order of listeners """

        date_str = self.date.strftime('%Y-%m-%d')

        r = Episode.view('directory/episode_toplist',
                startkey     = [date_str, {}],
                endkey       = [date_str, None],
                include_docs = True,
                descending   = True,
                limit        = limit,
                skip         = skip,
            )

        return list(r)


    def __getitem__(self, key):
        if isinstance(key, slice):
            start = key.start or 0
            length = key.stop - start
        else:
            start = key
            length = 1

        return self._query(start, length)
