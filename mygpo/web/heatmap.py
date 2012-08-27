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

from mygpo.couchdb import get_main_database


class EpisodeHeatmap(object):
    """ Information about how often certain parts of Episodes are played """

    def __init__(self, podcast_id, episode_id=None, user_id=None,
                 duration=None):
        """ Initialize a new Episode heatmap

        EpisodeHeatmap(podcast_id, [episode_id, [user_id]]) """

        self.podcast_id = podcast_id

        if episode_id is not None and podcast_id is None:
            raise ValueError('episode_id can only be used '
                    'if podcast_id is not None')

        self.episode_id = episode_id

        if user_id is not None and episode_id is None:
            raise ValueError('user_id can only be used '
                    'if episode_id is not None')

        self.user_id = user_id
        self.duration = duration
        self.heatmap = None
        self.borders = None


    def _query(self):
        """ Queries the database and stores the heatmap and its borders """

        db = get_main_database()

        group_level = len(filter(None, [self.podcast_id,
                    self.episode_id, self.user_id]))

        r = db.view('heatmap/by_episode',
                startkey    = [self.podcast_id, self.episode_id,
                                self.user_id],
                endkey      = [self.podcast_id, self.episode_id or {},
                                self.user_id or {}],
                reduce      = True,
                group       = True,
                group_level = group_level,
                stale       = 'update_after',
            )

        if not r:
            self.heatmap = []
            self.borders = []
        else:
            res = r.first()['value']
            self.heatmap = res['heatmap']
            self.borders = res['borders']

            # heatmap info doesn't reach until the end of the episode
            # so we extend it with 0 listeners
            if self.duration > self.borders[-1]:
                self.heatmap.append(0)
                self.borders.append(self.duration)


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

        return max(self.heatmap)


    @property
    @query_if_required()
    def sections(self):
        """ Returns an iterator that emits (from, to, play-counts) tuples

        Each tuple represents one part in the heatmap with a distinct
        play-count. from and to indicate the range of section in seconds."""

        for i in range(len(self.heatmap)):
            yield (self.borders[i], self.borders[i+1], self.heatmap[i])


    @query_if_required()
    def __nonzero__(self):
        return any(self.heatmap)
