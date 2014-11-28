from collections import defaultdict, namedtuple, Counter
from operator import itemgetter
from datetime import datetime
from random import choice
from itertools import chain

from django.utils.text import slugify

from mygpo.decorators import query_if_required
from mygpo.categories.models import Category, CategoryEntry


class Topics(object):

    def __init__(self, total=100, num_cat=10, podcasts_per_cat=10):
        self.total = total
        self.num_cat = num_cat
        self.podcasts_per_cat = podcasts_per_cat
        self._categories = None
        self._tagcloud = None

    def _needs_query(self):
        return self._categories is None

    def _query(self):
        categories = list(Category.objects.filter(num_entries__gt=0)
                                          .order_by('-modified')[:self.total])
        self._categories = categories[:self.num_cat]
        self._tagcloud = sorted(categories[self.num_cat:],
                                key=lambda x: x.title.lower())

    @property
    @query_if_required()
    def tagcloud(self):
        return self._tagcloud

    @query_if_required()
    def max_entries(self):
        return max([e.num_entries for e in self.tagcloud] + [0])

    @query_if_required()
    def min_entries(self):
        return min([e.num_entries for e in self.tagcloud] + [0])

    @property
    @query_if_required()
    def categories(self):
        return self._categories


def update_category(podcast):
    all_tags = list(t.tag for t in podcast.tags.all())

    if not all_tags:
        return

    random_tag = choice(all_tags)

    category, created = Category.objects.get_or_create(
        tags__tag=slugify(random_tag.strip()),
        defaults={
            'title': random_tag,
        }
    )

    if not created:
        # update modified timestamp
        category.save()

    # add podcast to the category as newest entry
    entry, created = CategoryEntry.objects.get_or_create(
        category=category,
        podcast=podcast,
    )

    if not created:
        # update modified timestamp
        entry.save()
