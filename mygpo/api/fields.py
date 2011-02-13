from django.db import models
import json

class SeparatedValuesField(models.TextField):
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', ',')
        super(SeparatedValuesField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value: return
        if isinstance(value, list):
            return value
        return value.split(self.token)

    def get_prep_value(self, value):
        if not value: return
        assert(isinstance(value, list) or isinstance(value, tuple))
        return self.token.join([unicode(s) for s in value])

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)


# http://djangosnippets.org/snippets/1478/
class JSONField(models.TextField):
    """JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly

    The json spec claims you must use a collection type at the top level of
    the data structure.  However the simplesjon decoder and Firefox both encode
    and decode non collection types that do not exist inside a collection.
    The to_python method relies on the value being an instance of basestring
    to ensure that it is encoded.  If a string is the sole value at the
    point the field is instanced, to_python attempts to decode the sting because
    it is derived from basestring but cannot be encodeded and throws the
    exception ValueError: No JSON object could be decoded.
    """

    # Used so to_python() is called
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""
        if value == "":
            return None

        try:
            if isinstance(value, basestring):
                return json.loads(value)
        except ValueError:
            return value

        return value

    def get_db_prep_save(self, value, connection=None):
        """Convert our JSON object to a string before we save"""

        if value == "":
            return None

        return super(JSONField, self).get_db_prep_save(json.dumps(value), connection)

