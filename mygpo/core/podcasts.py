from mygpo.podcasts.models import Podcast, PodcastGroup


# the default sort order for podcasts
PODCAST_SORT=lambda p: p.display_title


def lazy_call(f, *args, **kwargs):
    for x in f(*args, **kwargs):
        yield x


def individual_podcasts(pg):
    """ returns individual podcasts for an iter of Podcast(Group) objects """

    for p in pg:
        if isinstance(p, Podcast):
            yield p

        elif isinstance(p, PodcastGroup):
            for x in p.podcast_set.all():
                yield x
