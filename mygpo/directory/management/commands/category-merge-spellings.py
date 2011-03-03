from datetime import datetime

from django.core.management.base import BaseCommand

from mygpo.directory.models import Category


class Command(BaseCommand):

    def handle(self, *args, **options):

        if len(args) < 2:
            print """
Merges multiple categories into one by listing them as alternative spellings

Usage:
  ./manage.py category-merge-spellings <category> <spelling1> [<spelling2> ...]
"""
            return

        start_time = datetime.utcnow()
        cat_name = args[0]
        spellings = args[1:]

        print "Adding new spellings for %s ..." % cat_name
        category = Category.for_tag(cat_name)

        if not category:
            print " creating new category %s" % cat_name
            category = Category()
            category.label = cat_name

        for spelling in spellings:
            new_cat = Category.for_tag(spelling)

            if spelling == cat_name or (spelling in category.spellings):
                print " skipped %s: already in category" % spelling
                continue

            if not new_cat:
                #merged category doesn't yet exist
                category.spellings.append(spelling)

            elif new_cat and category._id == new_cat._id:
                print " set %s as new label" % cat_name
                category.spellings = list(set([x for x in category.spellings + [category.label] if x != cat_name]))
                category.label = cat_name

            else:
                print " add spelling %s" % spelling
                category.spellings = list(set(category.spellings + [new_cat.label] + new_cat.spellings))
                category.merge_podcasts(new_cat.podcasts)
                new_cat.delete()

            category.updated = start_time
            category.save()

