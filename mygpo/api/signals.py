#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

from django.db.models.signals import pre_delete
from mygpo.api.models import Podcast, Episode, EpisodeToplistEntry
from mygpo.data.models import BackendSubscription, Listener


def setup_signals():
    print 'setup'
    pre_delete.connect(delete_podcast_references, sender=Podcast)
    pre_delete.connect(delete_episode_references, sender=Episode)


def delete_podcast_references(sender, **kwargs):
    """
    Subscription is a model with an underlying database view.
    When deleting a podcast, Django would try to delete all its
    Subscriptions but fails because it can't delete from a view.
    Therefor we delete all database entries can create entries
    in the view
    """
    podcast = kwargs['instance']
    BackendSubscription.objects.filter(podcast=podcast).delete()
    Subscription.objects.filter(podcast=podcast)


def delete_episode_references(sender, **kwargs):
    """
    ToplistEntry is a model with an underlying database view.
    When deleting an episode, Django would try to delete its
    ToplistEntry but fails because it can't delete from a view.
    Therefor we delete all Listener entries that cause the Episode
    to appear in the toplist
    """
    print 'test'
    episode = kwargs['instance']
    Listener.objects.filter(episode=episode).delete()
    print 'listeners deleted'
    print EpisodeToplistEntry.objects.filter(episode=episode).count()
    EpisodeToplistEntry.objects.filter(episode=episode).delete()
    print 'deleted'


setup_signals()

