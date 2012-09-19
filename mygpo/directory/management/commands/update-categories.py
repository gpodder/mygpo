from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings

from mygpo.core.models import Podcast
from mygpo.directory.models import Category, CategoryEntry
from mygpo.directory.tags import Tag
from mygpo import utils
from mygpo.db.couchdb.podcast import podcasts_by_id


class Command(BaseCommand):

    def handle(self, *args, **options):

        # couchdbkit doesn't preserve microseconds
        start_time = datetime.utcnow().replace(microsecond=0)

        excluded_tags = settings.DIRECTORY_EXCLUDED_TAGS

        tags = args or Tag.all()

        for n, tag in enumerate(tags):

            if not isinstance(tag, basestring):
                tag = str(tag)

            label = utils.remove_control_chars(tag.strip())
            if not label:
                continue

            tag_obj = Tag(tag)
            podcast_ids, weights = utils.unzip(list(tag_obj.get_podcasts()))
            podcast_objs = podcasts_by_id(podcast_ids)
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

            utils.progress(n % 1000, 1000, category.label)
