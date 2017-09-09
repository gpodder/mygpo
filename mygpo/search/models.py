""" Wrappers for the results of a search """

import uuid


class PodcastResult(object):
    """ Wrapper for a Podcast search result """

    @classmethod
    def from_doc(cls, doc):
        """ Construct a PodcastResult from a search result """
        obj = cls()

        for key, val in doc['_source'].items():
            setattr(obj, key, val)

        obj.id = uuid.UUID(doc['_id']).hex
        return obj

    @property
    def slug(self):
        return next(iter(self.slugs), None)

    @property
    def url(self):
        return next(iter(self.urls), None)

    def get_id(self):
        return self.id

    @property
    def display_title(self):
        return self.title
