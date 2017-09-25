import uuid
from datetime import datetime
from collections import defaultdict

from django.db import models, transaction
from django.contrib.postgres.fields import JSONField

from mygpo.core.models import UUIDModel
from mygpo.podcasts.models import Podcast
from mygpo.maintenance.merge import merge_model_objects

import logging
logger = logging.getLogger(__name__)

DEFAULT_RELEASE = datetime(1970, 1, 1)
_SORT_KEY = lambda ep: ep.released or DEFAULT_RELEASE


class MergeTaskManager(models.Manager):

    @transaction.atomic
    def create_from_podcasts(self, podcasts):
        task = self.create(id=uuid.uuid4())

        for podcast in podcasts:
            mte = MergeTaskEntry.objects.create(
                id=uuid.uuid4(),
                podcast=podcast,
                task=task,
            )

        get_features = lambda episode: (episode.url, episode.title)

        # update groups within MergeTask
        task.set_groups(get_features)
        task.save()

        return task


class MergeTask(UUIDModel):
    """ A Group of podcasts that could be merged """

    objects = MergeTaskManager()

    groups = JSONField(default=dict)

    @property
    def podcasts(self):
        """ Returns the podcasts of the task, sorted by subscribers """
        podcasts = [entry.podcast for entry in self.entries.all()]
        podcasts = sorted(podcasts,
                          key=lambda p: p.subscribers, reverse=True)
        return podcasts


    def set_groups(self, get_features):
        """ Groups the episodes by features extracted using ``get_features``

        get_features is a callable that expects an episode as parameter, and
        returns a value representing the extracted feature(s).
        """

        episodes = self.episodes

        episode_groups = defaultdict(list)

        for episode in episodes.values():
            features = get_features(episode)
            episode_groups[features].append(episode.pk.hex)

        groups = sorted(episode_groups.values())#, key=_SORT_KEY)
        self.groups = list(groups)

    @property
    def episodes(self):
        episodes = {}
        for podcast in self.podcasts:
            episodes.update(dict((e.id.hex, e) for e in podcast.episode_set.all()))

        return episodes

    def episode_groups(self):
        """ Return a list of episode lists

        podcasts = [p1, p2, p3]

        Returns
        groups = [
            [ep1 of p1, ep1 of p2, None],
            [ep2 of p2, None, ep2 of p3],
        ]
        """

        episodes = self.episodes
        podcasts = self.podcasts
        groups = []
        print(episodes)
        print(podcasts)
        print(self.groups)

        for episode_ids in self.groups:
            line = []
            # go through the podcasts in order
            for podcast in podcasts:
                for episode_id in episode_ids:
                    episode = episodes.get(episode_id, None)
                    if episode is None:
                        continue

                    if episode.podcast == podcast:
                        line.append(episode)
                        break
                else:
                    # if nothing was found, add None
                    line.append(None)

            groups.append(line)
        print(groups)
        return groups

    def merge(self):
        """ Carries out the actual merging """

        logger.info('Start merging of podcasts: %r', self.podcasts)

        podcasts = self.podcasts
        podcast1 = podcasts.pop(0)
        logger.info('Merge target: %r', podcast1)

        self.merge_episodes()
        merge_model_objects(podcast1, podcasts)

        return podcast1

    def merge_episodes(self):
        """ Merges the episodes according to the groups """

        for episodes in self.episode_groups():
            print('Episodes')
            print(episodes)

            if not episodes:
                continue

            episode = episodes.pop(0)

            if not episode:
                continue

            # the list can contain Nones
            episodes = list(filter(None, episodes))

            logger.info('Merging %d episodes', len(episodes))
            merge_model_objects(episode, episodes)


class MergeTaskEntry(UUIDModel):
    """ An entry in a MergeTask """

    podcast = models.ForeignKey(Podcast, on_delete=models.CASCADE)

    task = models.ForeignKey(MergeTask,
                              on_delete=models.CASCADE,
                              related_name='entries',
                              related_query_name='entry')

    class Meta:
        unique_together = [
            ['podcast', ]  # a podcast can only belong to one task
        ]
