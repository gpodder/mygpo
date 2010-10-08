from couchdbkit import Document, IntegerProperty, SchemaListProperty

class Podcast(Document):
    oldid = IntegerProperty()

    @classmethod
    def for_oldid(cls, oldid):
        r = cls.view('core/podcasts_by_oldid', key=oldid)
        return r.first() if r else None


    def get_id(self):
        return getattr(self, 'id', None) or self._id


    def __repr__(self):
        if not self._id:
            return super(Podcast, self).__repr__()
        elif self.oldid:
            return '%s %s (%s)' % (self.__class__.__name__, self._id[:10], self.oldid)
        else:
            return '%s %s' % (self.__class__.__name__, self._id[:10])


    def save(self):
        group = getattr(self, 'group', None)
        if group: #we are part of a PodcastGroup
            group = PodcastGroup.get(group)
            i = group.podcasts.index(self)
            group.podcasts[i] = self
            group.save()

        else:
            super(Podcast, self).save()


    def delete(self):
        group = getattr(self, 'group', None)
        if group:
            group = PodcastGroup.get(group)
            i = group.podcasts.index(self)
            del group.podcasts[i]
            group.save()

        else:
            super(Podcast, self).delete()


    def __eq__(self, other):
        if not self.get_id():
            return self == other

        if other == None:
            return False

        return self.get_id() == other.get_id()



class PodcastGroup(Document):
    podcasts = SchemaListProperty(Podcast)

    @classmethod
    def for_oldid(cls, oldid):
        r = cls.view('core/podcastgroups_by_oldid', key=oldid)
        return r.first() if r else None


    def add_podcast(self, podcast):
        podcast.id = podcast._id

        if not self._id:
            raise ValueError('group has to have an _id first')

        podcast.group = self._id
        self.podcasts.append(podcast)
        self.save()
        podcast.delete()


    def __repr__(self):
        if not self._id:
            return super(PodcastGroup, self).__repr__()
        elif self.oldid:
            return '%s %s (%s)' % (self.__class__.__name__, self._id[:10], self.oldid)
        else:
            return '%s %s' % (self.__class__.__name__, self._id[:10])
