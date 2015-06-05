#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

from functools import wraps

from mygpo.history.models import EpisodeHistoryEntry


class EpisodeHeatmap(object):
    """ Information about how often certain parts of Episodes are played """

    def __init__(self, podcast, episode=None, user=None, duration=None):
        """ Initialize a new Episode heatmap """
        self.duration = duration
        self.heatmap = None
        self.borders = None

        history = EpisodeHistoryEntry.objects.filter(episode__podcast=podcast)

        if episode:
            history = history.filter(episode=episode)

        if user:
            history = history.filter(user=user)

        self.history = history

    @staticmethod
    def _raw_heatmap(events):
        """ Returns the detailled (exact) heatmap

        >>> _raw_heatmap([(70, 200), (0, 100), (0, 50)])
        ([2, 1, 2, 1], [0, 50, 70, 100, 200])
        """

        # get a list of all borders that occur in events
        borders = set()
        for start, end in events:
            borders.add(start)
            borders.add(end)
        borders = sorted(borders)

        # this contains the value for the spaces within the borders
        # therefore we need one field less then we have borders
        counts = [0] * (len(borders)-1)

        for start, end in events:
            # for each event we calculate its range
            start_idx = borders.index(start)
            end_idx = borders.index(end)

            # and increase the play-count within the range by 1
            for inc in range(start_idx, end_idx):
                counts[inc] = counts[inc] + 1

        return counts, borders

        # we return the heatmap as (start, stop, playcount) tuples
        # for i in range(len(counts)):
        #    yield (borders[i], borders[i+1], counts[i])

    def _query(self):
        self.heatmap, self.borders = self._raw_heatmap(
            self.history.values_list('started', 'stopped'))

    def query_if_required():
        """ If required, queries the database before calling the function """
        def decorator(f):
            @wraps(f)
            def tmp(self, *args, **kwargs):
                if None in (self.heatmap, self.borders):
                    self._query()

                return f(self, *args, **kwargs)
            return tmp
        return decorator

    @property
    @query_if_required()
    def max_plays(self):
        """ Returns the highest number of plays of all sections """

        return max(self.heatmap, default=0)

    @property
    @query_if_required()
    def sections(self):
        """ Returns an iterator that emits (from, to, play-counts) tuples

        Each tuple represents one part in the heatmap with a distinct
        play-count. from and to indicate the range of section in seconds."""

        # this could be written as "yield from"
        for x in self._sections(self.heatmap, self.borders):
            yield x

    @staticmethod
    def _sections(heatmap, borders):
        """ Merges heatmap-counts and borders into a list of 3-tuples

        Each tuple contains (start-border, end-border, play-count)

        >>> list(_sections([2, 1, 2, 1], [0, 50, 70, 100, 200]))
        [(0, 50, 2), (50, 70, 1), (70, 100, 2), (100, 200, 1)]
        """
        for i in range(len(heatmap)):
            yield (borders[i], borders[i+1], heatmap[i])

    @query_if_required()
    def __nonzero__(self):
        return any(self.heatmap)
