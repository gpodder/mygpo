from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings
from django.template.defaultfilters import slugify

from mygpo.core.models import Podcast
from mygpo.directory.models import Category, CategoryEntry
from mygpo.directory.tags import Tag
from mygpo.utils import remove_control_chars, progress, unzip, is_url


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        # couchdbkit doesn't preserve microseconds
        self.start_time = datetime.utcnow().replace(microsecond=0)

        self.excluded_tags = settings.DIRECTORY_EXCLUDED_TAGS


    def handle(self, *args, **options):

        tags = args or Tag.all()

        for n, tag in enumerate(tags):

            if not isinstance(tag, basestring):
                tag = str(tag)

            label = remove_control_chars(tag.strip())
            if not label:
                continue

            tag_obj = Tag(tag)
            self.handle_tag(label, tag_obj)

            progress(n % 1000, 1000, label)


    def handle_tag(self, label, tag_obj):

        category = self.get_category(label)
        if not category:
            return

        # delete if it has been excluded after it has been created
        if label in self.excluded_tags:
            category.delete()
            return

        # delete categories with 'invalid' labels
        if not slugify(label):
            category.delete()
            return

        if is_url(label):
            category.delete()
            return

        podcast_ids, weights = unzip(list(tag_obj.get_podcasts()))
        podcast_objs = Podcast.get_multi(podcast_ids)
        podcasts = []
        for podcast, weight in zip(podcast_objs, weights):
            e = CategoryEntry()
            e.podcast = podcast.get_id()
            e.weight = float(weight * podcast.subscriber_count())
            podcasts.append(e)

        # we overwrite previous data
        if category.updated != self.start_time:
            category.podcasts = []

        category.merge_podcasts(podcasts)
        category.updated = self.start_time

        category.save()


    def get_category(self, label):
        category = Category.for_tag(label)

        if category:
            return category

        if not label or label in self.excluded_tags:
            return None

        if not slugify(label):
            return None

        if is_url(label):
            return None

        category = Category()
        category.label = label
        category.spellings = []
        return category
