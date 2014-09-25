from django.db import models

from mygpo.podcasts.models import Podcast


class Category(models.Model):
    """ A category of podcasts """

    title = models.CharField(max_length=1000, null=False, blank=False,
                             unique=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class CategoryEntry(models.Model):
    """ A podcast in a category """

    category = models.ForeignKey(Category, related_name='entries',
                                 on_delete=models.CASCADE)

    podcast = models.ForeignKey(Podcast,
                                on_delete=models.CASCADE)

    # this could be used from UpdateInfoModel, except for the index on modified
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)


    class Meta:
        unique_together = [
            ('category', 'podcast'),
        ]


class CategoryTag(models.Model):

    tag = models.SlugField(unique=True)

    category = models.ForeignKey(Category, related_name='tags',
                                 on_delete=models.CASCADE)
