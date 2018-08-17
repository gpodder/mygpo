""" This module contains abstract models that are used in multiple apps """


from django.db import models, connection


class UUIDModel(models.Model):
    """ Models that have an UUID as primary key """

    id = models.UUIDField(primary_key=True)

    class Meta:
        abstract = True

    def get_id(self):
        """ String representation of the ID """
        return self.id


class TwitterModel(models.Model):
    """ A model that has a twitter handle """

    twitter = models.CharField(max_length=15, null=True, blank=False)

    class Meta:
        abstract = True


class GenericManager(models.Manager):
    """ Generic manager methods """

    def count_fast(self):
        """ Fast approximate count of all model instances

        PostgreSQL is slow when counting records without an index. This is a
        workaround which only gives approximate results. see:
        http://wiki.postgresql.org/wiki/Slow_Counting """
        cursor = connection.cursor()
        cursor.execute(
            "select reltuples from pg_class where relname='%s';"
            % self.model._meta.db_table
        )
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


class OptionallyOrderedModel(models.Model):
    """ A model that can be ordered, w/ unknown order of individual objects

    The implementing Model must make sure that 'order' is sufficiently unique
    """

    order = models.BigIntegerField(null=True, default=None)

    class Meta:
        abstract = True
        ordering = ['order']
