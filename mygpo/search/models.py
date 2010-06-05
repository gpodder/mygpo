from django.db import models

class SearchEntry(models.Model):
    text = models.TextField(db_index=True)
    obj_type = models.CharField(max_length=20, db_index=True)
    obj_id = models.IntegerField(db_index=True)
    tags = models.CharField(max_length=200, db_index=True)
    priority = models.IntegerField(db_index=True)

    def __repr__(self):
        return "<%s '%s'>" % (self.__class__.__name__, self.text[:20])

