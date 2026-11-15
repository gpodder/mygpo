from django.db import models

from mygpo.core.models import UpdateInfoModel
from mygpo.podcasts.models import Podcast


class Category(UpdateInfoModel):
    """A category of podcasts"""

    title = models.CharField(max_length=1000, null=False, blank=False, unique=True)

    num_entries = models.IntegerField()

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

        indexes = [models.Index(fields=["modified", "num_entries"])]

    def save(self, *args, **kwargs):
        self.num_entries = self.entries.count()
        if "update_fields" in kwargs and "num_entries" not in kwargs["update_fields"]:
            kwargs["update_fields"] = list(kwargs["update_fields"]) + ["num_entries"]
        super(Category, self).save(*args, **kwargs)

    @property
    def podcasts(self):
        return self.entries.prefetch_related("podcast", "podcast__slugs")

    @property
    def clean_title(self):
        return self.title.replace("\n", " ")

    @property
    def tag(self):
        return self.tags.first().tag


class CategoryEntry(UpdateInfoModel):
    """A podcast in a category"""

    category = models.ForeignKey(
        Category, related_name="entries", on_delete=models.CASCADE
    )

    podcast = models.ForeignKey(Podcast, on_delete=models.CASCADE)

    class Meta:
        unique_together = [("category", "podcast")]

        indexes = [models.Index(fields=["category", "modified"])]


class CategoryTag(models.Model):

    tag = models.SlugField(unique=True)

    category = models.ForeignKey(
        Category, related_name="tags", on_delete=models.CASCADE
    )
