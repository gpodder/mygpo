import json

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes import generic

from mygpo.users.settings import PUBLIC_SUB_PODCAST
from mygpo.podcasts.models import Podcast

import logging
logger = logging.getLogger(__name__)


class UserSettingsManager(models.Manager):
    """ Manager for PodcastConfig objects """

    def get_private_podcasts(self, user):
        """ Returns the podcasts that the user has marked as private """
        settings = self.filter(
            user=user,
            content_type=ContentType.objects.get_for_model(Podcast),
        )

        private = []
        for setting in settings:
            if not setting.get_wksetting(PUBLIC_SUB_PODCAST):
                private.append(setting.content_object)

        return private

    def get_for_scope(self, user, scope):
        """ Returns the settings object for the given user and scope obj

        If scope is None, the settings for the user are returned """
        if scope is None:
            content_type = None
            object_id = None
        else:
            content_type = ContentType.objects.get_for_model(scope)
            object_id = scope.pk

        try:
            return UserSettings.objects.get(
                user=user,
                content_type=content_type,
                object_id=object_id,
            )

        except UserSettings.DoesNotExist:
            # if it does not exist, return a new instance. It is up to the
            # caller to save the object if required
            return UserSettings(
                user=user,
                content_type=content_type,
                object_id=object_id,
            )


class UserSettings(models.Model):
    """ Stores settings for a podcast, episode, user or client """

    # the user for which the config is stored
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    # see https://docs.djangoproject.com/en/1.6/ref/contrib/contenttypes/#generic-relations
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    settings = models.TextField(null=False, default='{}')

    class Meta:
        unique_together = [
            ['user', 'content_type', 'object_id'],
        ]

        verbose_name_plural = 'User Settings'
        verbose_name = 'User Settings'

    objects = UserSettingsManager()

    def get_wksetting(self, setting):
        """ returns the value of a well-known setting """
        try:
            settings = json.loads(self.settings)
        except ValueError as ex:
            logger.warn('Decoding settings failed: {msg}'.format(msg=str(ex)))
            return None

        return settings.get(setting.name, setting.default)

    def set_wksetting(self, setting, value):
        try:
            settings = json.loads(self.settings)
        except ValueError as ex:
            logger.warn('Decoding settings failed: {msg}'.format(msg=str(ex)))
            settings = {}
        settings[setting.name] = value
        self.settings = json.dumps(settings)

    def get_setting(self, name, default):
        settings = json.loads(self.settings)
        return settings.get(name, default)

    def set_setting(self, name, value):
        settings = json.loads(self.settings)
        settings[name] = value
        self.settings = json.dumps(settings)

    def del_setting(self, name):
        settings = json.loads(self.settings)
        try:
            settings.pop(name)
        except KeyError:
            pass
        self.settings = json.dumps(settings)

    def as_dict(self):
        return json.loads(self.settings)
