from __future__ import unicode_literals

from django.contrib.contenttypes.admin import GenericTabularInline

from . import models


class VoteInline(GenericTabularInline):
    """ Inline Admin model for votes """
    model = models.Vote
    raw_id_fields = ('user', )
