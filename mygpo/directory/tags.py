from random import choice

from django.db import IntegrityError
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
        categories = list(
            Category.objects.filter(num_entries__gt=0)
            .filter(tags__isnull=False)
            .order_by('-modified')[: self.total]
            .prefetch_related('tags')
        )
        self._categories = categories[: self.num_cat]
        self._tagcloud = sorted(
            categories[self.num_cat :], key=lambda x: x.title.lower()
        )

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

    random_tag = choice(all_tags).strip()

    try:
        category, created = Category.objects.get_or_create(
            tags__tag=slugify(random_tag), defaults={'title': random_tag}
        )

    except IntegrityError as ie:
        # check if category with this title already exists
        # the exception message should be like:
        # IntegrityError: duplicate key value violates unique
        # constraint "categories_category_title_key"
        if 'categories_category_title_key' not in str(ie):
            raise

        category = Category.objects.get(title=random_tag)
        created = False

    if not created:
        # update modified timestamp
        category.save()

    # add podcast to the category as newest entry
    entry, created = CategoryEntry.objects.get_or_create(
        category=category, podcast=podcast
    )

    if not created:
        # update modified timestamp
        entry.save()
