""" This module contains abstract models that are used in multiple apps """

from __future__ import absolute_import, unicode_literals

import json

from uuidfield import UUIDField

from django.db import models, connection

import logging
logger = logging.getLogger(__name__)


class UUIDModel(models.Model):
    """ Models that have an UUID as primary key """

    id = UUIDField(primary_key=True)

    class Meta:
        abstract = True

    def get_id(self):
        """ String representation of the ID """
        return self.id.hex


class TwitterModel(models.Model):
    """ A model that has a twitter handle """

    twitter = models.CharField(max_length=15, null=True, blank=False)

    class Meta:
        abstract = True


class SettingsModel(models.Model):
    """ A model that can store arbitrary settings as JSON """

    settings = models.TextField(null=False, default='{}')

    class Meta:
        abstract = True

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


class GenericManager(models.Manager):
    """ Generic manager methods """

    def count_fast(self):
        """ Fast approximate count of all model instances

        PostgreSQL is slow when counting records without an index. This is a
        workaround which only gives approximate results. see:
        http://wiki.postgresql.org/wiki/Slow_Counting """
        cursor = connection.cursor()
        cursor.execute("select reltuples from pg_class where relname='%s';" %
                       self.model._meta.db_table)
        row = cursor.fetchone()
        return int(row[0])


class UpdateInfoModel(models.Model):
    """ Model that keeps track of when it was created and updated """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DeleteableModel(models.Model):
    """ A model that can be marked as deleted """

    # indicates that the object has been deleted
    deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True


class OrderedModel(models.Model):
    """ A model that can be ordered

    The implementing Model must make sure that 'order' is sufficiently unique
    """

    order = models.PositiveSmallIntegerField()

    class Meta:
        abstract = True
        ordering = ['order']
