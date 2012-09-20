from mygpo.users.models import EpisodeUserState



def episode_state_for_user_episode(cls, user, episode):
    r = cls.view('episode_states/by_user_episode',
            key          = [user._id, episode._id],
            include_docs = True,
            limit        = 1,
        )

    if r:
        return r.first()

    else:
        podcast = podcast_by_id(episode.podcast)

        state = EpisodeUserState()
        state.episode = episode._id
        state.podcast = episode.podcast
        state.user = user._id
        state.ref_url = episode.url
        state.podcast_ref_url = podcast.url

        return state



def all_episode_states(episode):
    r =  EpisodeUserState.view('episode_states/by_podcast_episode',
            startkey     = [self.podcast, self._id, None],
            endkey       = [self.podcast, self._id, {}],
            include_docs = True,
        )
    return list(r)



def episode_listener_count(episode):
    """ returns the number of users that have listened to this podcast """

    r = EpisodeUserState.view('listeners/by_podcast',
            startkey    = [self.get_id(), None],
            endkey      = [self.get_id(), {}],
            group       = True,
            group_level = 1,
            reduce      = True,
        )
    return r.first()['value'] if r else 0


def listener_count_timespan(self, start=None, end={}):
    """ returns (date, listener-count) tuples for all days w/ listeners """

    if isinstance(start, datetime):
        start = start.isoformat()

    if isinstance(end, datetime):
        end = end.isoformat()

    from mygpo.users.models import EpisodeUserState
    r = EpisodeUserState.view('listeners/by_podcast',
            startkey    = [self.get_id(), start],
            endkey      = [self.get_id(), end],
            group       = True,
            group_level = 2,
            reduce      = True,
        )

    for res in r:
        date = parser.parse(res['key'][1]).date()
        listeners = res['value']
        yield (date, listeners)




def episode_listener_counts(self):
    """ (Episode-Id, listener-count) tuples for episodes w/ listeners """

    from mygpo.users.models import EpisodeUserState
    r = EpisodeUserState.view('listeners/by_podcast_episode',
            startkey    = [self.get_id(), None, None],
            endkey      = [self.get_id(), {},   {}],
            group       = True,
            group_level = 2,
            reduce      = True,
        )

    for res in r:
        episode   = res['key'][1]
        listeners = res['value']
        yield (episode, listeners)


def get_episode_states(self, user_id):
    """ Returns the latest episode actions for the podcast's episodes """

    from mygpo.users.models import EpisodeUserState
    db = get_main_database()

    res = db.view('episode_states/by_user_podcast',
            startkey = [user_id, self.get_id(), None],
            endkey   = [user_id, self.get_id(), {}],
        )

    for r in res:
        action = r['value']
        yield action



def listener_count(self, start=None, end={}):
    """ returns the number of users that have listened to this episode """

    from mygpo.users.models import EpisodeUserState
    r = EpisodeUserState.view('listeners/by_episode',
            startkey    = [self._id, start],
            endkey      = [self._id, end],
            reduce      = True,
            group       = True,
            group_level = 2
        )
    return r.first()['value'] if r else 0


def listener_count_timespan(self, start=None, end={}):
    """ returns (date, listener-count) tuples for all days w/ listeners """

    if isinstance(start, datetime):
        start = start.isoformat()

    if isinstance(end, datetime):
        end = end.isoformat()

    from mygpo.users.models import EpisodeUserState
    r = EpisodeUserState.view('listeners/by_episode',
            startkey    = [self._id, start],
            endkey      = [self._id, end],
            reduce      = True,
            group       = True,
            group_level = 3,
        )

    for res in r:
        date = parser.parse(res['key'][1]).date()
        listeners = res['value']
        yield (date, listeners)


