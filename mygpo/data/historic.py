from mygpo.api.models import Podcast, Episode, SubscriptionAction, EpisodeAction
from mygpo.data.models import HistoricPodcastData, HistoricEpisodeData
from mygpo.utils import daterange
from datetime import date, timedelta


def all_podcasts():
    for p in Podcast.objects.all().iterator():
        calc_podcast(p)


def calc_podcast(podcast):

    latest_historic = HistoricPodcastData.objects.filter(podcast=podcast).order_by('-date')
    if latest_historic.count() > 0:
        start = latest_historic[0].date + timedelta(days=1)
        prev = latest_historic[0].subscriber_count

    else:
        first = SubscriptionAction.objects.filter(podcast=podcast).order_by('timestamp')[0]
        start = first.timestamp.date()
        prev = 0

    for day in daterange(start, date.today() - timedelta(days=1)):
        nextday = day + timedelta(days=1)
        act = [x['action'] for x in SubscriptionAction.objects.filter(podcast=podcast, timestamp__range=(day, nextday)).values('action')]
        prev += sum(act)

        rec = HistoricPodcastData.objects.get_or_create(podcast=podcast, date=day, defaults={'subscriber_count': prev})


def calc_episode(episode):
    latest_historic = HistoricEpisodeData.objects.filter(episode=episode).order_by('-date')
    if latest_historic.count() > 0:
        start = latest_historic[0].date + timedelta(days=1)
    else:
        first = EpisodeAction.objects.filter(episode=episode).order_by('timestamp')[0]
        start = first.timestamp.date()

    for day in daterange(start, date.today() - timedelta(days=1)):
        nextday = day + timedelta(days=1)

        listeners = EpisodeAction.objects.filter(episode=episode, action='play').values('user').distinct().count()

        HistoricEpisodeData.objects.get_or_create(episode=episode, date=day, defaults={'listener_count': listeners})

