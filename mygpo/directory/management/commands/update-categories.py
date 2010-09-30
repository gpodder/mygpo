from datetime import datetime

from django.core.management.base import BaseCommand

from mygpo import settings
from mygpo.directory.models import Category
from mygpo.data.models import DirectoryEntry


class Command(BaseCommand):

    def handle(self, *args, **options):

        start_time = datetime.utcnow()

        excluded_tags = getattr(settings, 'DIRECTORY_EXCLUDED_TAGS', [])

        top_tags = DirectoryEntry.objects.top_tags(None)
        for tag in top_tags:
            #print tag.tag

            category = Category.for_tag(tag.tag)
            if category:

                # delete if it has been excluded after it has been created
                if tag.tag in excluded_tags:
                    category.delete()
                    continue

                if category.updated < start_time:
                    category.weight = tag.entries
                else:
                    category.weight += tag.entries

            else:

                if tag.tag in excluded_tags:
                    continue

                category = Category()
                category.label = tag.tag
                category.spellings = []
                category.weight = tag.entries


            category.updated = start_time
            category.save()

