from django.db import models
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from mygpo.core.models import UpdateInfoModel, OrderedModel, UUIDModel
from mygpo.podcasts.models import Podcast
from mygpo.flattr import FlattrThing
from mygpo.votes.models import VoteMixin
from mygpo.utils import set_ordered_entries


class PodcastList(UUIDModel, VoteMixin, UpdateInfoModel):
    """ A user-curated collection of podcasts """

    # the user that created (and owns) the list
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    # the user-assigned title of the list
    title = models.CharField(max_length=512)

    # the slug (unique for the user) that is derived from the title
    slug = models.SlugField(max_length=128)

    class Meta:
        unique_together = [
            # a slug is unique for a user
            ('user', 'slug'),
        ]

    @property
    def max_order(self):
        return max([-1] + [e.order for e in self.entries.all()])

    @property
    def num_entries(self):
        return self.entries.count()

    def add_entry(self, obj):
        entry, created = PodcastListEntry.objects.get_or_create(
            podcastlist=self,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.id,
            defaults={
                'order': self.max_order + 1,
            },
        )

    def get_flattr_thing(self, domain, username):
        """ Returns a "Thing" which can be flattred by other Flattr users """
        return FlattrThing(
                url = reverse('list-show', args=[username, self.slug]),
                title = self.title,
                description = 'A collection of podcasts about "%s" by %s user %s' % (self.title, domain, username),
                category = 'audio',
                hidden = None,
                tags = None,
                language = None,
            )

    def set_entries(self, podcasts):
        """ Updates the list to include the given podcast, removes others """

        existing = {e.content_object: e for e in self.entries.all()}
        set_ordered_entries(self, podcasts, existing, PodcastListEntry,
                            'content_object', 'podcastlist')


class PodcastListEntry(UpdateInfoModel, OrderedModel):
    """ An entry in a Podcast List """

    # the list that the entry belongs to
    podcastlist = models.ForeignKey(PodcastList,
                                    related_name='entries',
                                    on_delete=models.CASCADE,
                                   )

    # the object (Podcast or PodcastGroup) that is in the list
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.UUIDField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta(OrderedModel.Meta):
        unique_together = [
            ('podcastlist', 'order'),
            ('podcastlist', 'content_type', 'object_id'),
        ]
