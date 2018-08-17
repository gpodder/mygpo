from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from mygpo.categories.models import Category, CategoryTag


class Command(BaseCommand):
    def handle(self, *args, **options):

        if len(args) < 2:
            print(
                """
Merges multiple categories into one by listing them as alternative spellings

Usage:
  ./manage.py category-merge-spellings <category> <spelling1> [<spelling2> ...]
"""
            )
            return

        start_time = datetime.utcnow()
        cat_name = args[0]
        spellings = args[1:]

        print("Adding new spellings for %s ..." % cat_name)
        category, created = Category.objects.get_or_create(
            tags__tag=slugify(cat_name), defaults={'title': cat_name}
        )

        for spelling in spellings:

            tag, created = CategoryTag.objects.get_or_create(
                tag=spelling, defaults={'category': category}
            )

            if created:
                # we just created a new tag-assignedment -- nothing else to do
                continue

            oldcategory = tag.category

            for entry in oldcategory.entries:
                # todo: this might cause a constraint violation if the
                # podcast is already a entry of the new category
                entry.category = category
                entry.save()

            tag.category = category
            tag.save()
