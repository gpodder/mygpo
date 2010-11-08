from datetime import datetime
from couchdbkit.ext.django.schema import *

class Podcast(Document):
    oldid = IntegerProperty()
    related_podcasts = StringListProperty()

    @classmethod
    def for_oldid(cls, oldid):
        r = cls.view('core/podcasts_by_oldid', key=long(oldid))
        return r.first() if r else None


    def get_id(self):
        return getattr(self, 'id', None) or self._id

    def get_old_obj(self):
        if self.oldid:
            from mygpo.api.models import Podcast
            return Podcast.objects.get(id=self.oldid)
        return None


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


class Rating(DocumentSchema):
    rating = IntegerProperty()
    timestamp = DateTimeProperty(default=datetime.utcnow)


class Suggestions(Document):
    user = StringProperty()
    user_oldid = IntegerProperty()
    podcasts = StringListProperty()
    blacklist = StringListProperty()
    ratings = SchemaListProperty(Rating)

    @classmethod
    def for_user_oldid(cls, oldid):
        r = cls.view('core/suggestions_by_user_oldid', key=oldid)
        if r:
            return r.first()
        else:
            s = Suggestions()
            s.user_oldid = oldid
            return s


    def get_podcasts(self):
        from mygpo.api.models import Subscription
        subscriptions = [x.podcast for x in Subscription.objects.filter(user__id=self.user_oldid)]
        subscriptions = [Podcast.for_oldid(x.id) for x in subscriptions]
        subscriptions = [x._id for x in subscriptions if x]

        for p in self.podcasts:
            if not p in self.blacklist and not p in subscriptions:
                podcast = Podcast.get(p)
                if podcast:
                    yield podcast


    def __repr__(self):
        if not self._id:
            return super(Podcast, self).__repr__()
        else:
            return '%d Suggestions for %s (%s)' % \
                (len(self.podcasts),
                 self.user[:10] if self.user else self.user_oldid,
                 self._id[:10])
