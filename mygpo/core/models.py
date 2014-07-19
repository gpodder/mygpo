""" This module contains abstract models that are used in multiple apps """

from __future__ import absolute_import

import json

from uuidfield import UUIDField

from django.db import models


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
        settings = json.loads(self.settings)
        return settings.get(setting.name, setting.default)

    def get_setting(self, name, default):
        settings = json.loads(self.settings)
        return settings.get(name, default)


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
