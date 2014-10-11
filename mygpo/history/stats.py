from collections import Counter

from mygpo.history.models import EpisodeHistoryEntry


def played_episode_counts(user):
    """ number of played episodes per podcast for the given user """
    # retrieve list of unique episodes that the user has played.
    # for each episode only it's podcast is returned, because we don't care
    # about which episodes exactly have been played, only the number
    podcasts = EpisodeHistoryEntry.objects\
                                  .filter(user=user,
                                          action=EpisodeHistoryEntry.PLAY)\
                                  .order_by('episode__id')\
                                  .distinct('episode__id')\
                                  .values_list('episode__podcast', flat=True)
    return Counter(podcasts)
