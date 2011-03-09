from datetime import datetime

from django.core.management.base import BaseCommand

from mygpo import settings
from mygpo.core.models import Podcast
from mygpo.directory.models import Category, CategoryEntry
from mygpo.directory.tags import all_tags, podcasts_for_tag
from mygpo import utils


class Command(BaseCommand):

    def handle(self, *args, **options):

        start_time = datetime.utcnow()

        excluded_tags = getattr(settings, 'DIRECTORY_EXCLUDED_TAGS', [])

        tags = args or all_tags()

        for n, tag in enumerate(tags):

            if not isinstance(tag, basestring):
                tag = str(tag)

            label = utils.remove_control_chars(tag.strip())
            if not label:
                continue

            podcast_ids, weights = utils.unzip(list(podcasts_for_tag(tag)))
            podcast_objs = Podcast.get_multi(podcast_ids)
            podcasts = []
            for podcast, weight in zip(podcast_objs, weights):
                e = CategoryEntry()
                e.podcast = podcast.get_id()
                e.weight = float(weight * podcast.subscriber_count())
                podcasts.append(e)

            category = Category.for_tag(label)

            if not category:
                if not label or label in excluded_tags:
                    continue

                category = Category()
                category.label = label
                category.spellings = []

            # delete if it has been excluded after it has been created
            if label in excluded_tags:
                category.delete()
                continue

            # we overwrite previous data
            if category.updated != start_time:
                category.podcasts = []

            category.merge_podcasts(podcasts)

            category.updated = start_time

            if 'weight' in category:
                del category['weight']

            category.save()

            try:
                utils.progress(n % 1000, 1000, category.label.encode('utf-8'))
            except:
                pass
