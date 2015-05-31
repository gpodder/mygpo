from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.fields import GenericRelation

from mygpo.core.models import UpdateInfoModel


class Vote(UpdateInfoModel):
    """ A vote by a user for some object """

    # the user who voted
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    # the object that was voted for
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    # this should suit UUID and integer primary keys
    object_id = models.UUIDField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = [
            # a user can only vote once per object
            ('user', 'content_type', 'object_id'),
        ]


class VoteMixin(models.Model):

    votes = GenericRelation('Vote', related_query_name='votes')

    class Meta:
        abstract = True

    def vote(self, user):
        """ Register a vote from the user for the current object """
        Vote.objects.get_or_create(
            user=user,
            content_type=ContentType.objects.get_for_model(self),
            object_id=obj.pk,
        )

    def vote_count(self):
        return self.votes.count()
