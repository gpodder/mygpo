"""
psql -h 172.17.0.2 -p 5014 -U postgres mygpo  -X -A -w -t -c "select username from auth_user where last_login < '2024-01-01' and id > 201 order by id asc;" | xargs  -I '{}' envdir envs/dev python manage.py archive '{}' /tmp/'{}'.archive --archive '/run/media/elelay/HDD/mygpo/archive/{}.tar.zstd' 2>&1 | tee /run/media/elelay/HDD/mygpo/archive/archive.log
"""
import json
import os
import shutil
import subprocess
import sys

from datetime import datetime
from functools import wraps
from time import perf_counter
from uuid import UUID

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet

from mygpo.api.opml import Exporter
from mygpo.categories.models import CategoryEntry, CategoryTag
from mygpo.chapters.models import Chapter
from mygpo.episodestates.models import EpisodeState
from mygpo.favorites.models import FavoriteEpisode
from mygpo.history.models import EpisodeHistoryEntry, HistoryEntry
from mygpo.podcastlists.models import PodcastList
from mygpo.podcasts.models import Episode, Podcast, PodcastGroup, Tag
from mygpo.publisher.models import PublishedPodcast
from mygpo.suggestions.models import PodcastSuggestion
from mygpo.subscriptions import get_subscribed_podcasts
from mygpo.subscriptions.models import Subscription
from mygpo.users.models import Client, SyncGroup, UserProxy
from mygpo.usersettings.models import UserSettings
from mygpo.votes.models import Vote

class MyJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, UUID):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def timed(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        before = perf_counter()
        ret = f(*args, **kwds)
        print("D: run %s in %.1fs" % (f.__qualname__, (perf_counter() - before)))
    return wrapper

class Command(BaseCommand):
    """
    Create an archive of all user content.

    The user is specified by its user id.
    """

    def add_arguments(self, parser):
        parser.add_argument("username_or_id", type=str)
        parser.add_argument("output_dir", type=str)
        parser.add_argument("--archive", type=str)
        parser.add_argument("--is-username", type=bool, default=False)
        parser.add_argument("--keep-output-dir", type=bool, default=False)
        parser.add_argument("--and-delete", type=bool, default=False)

    @timed
    def handle(self, *args, username_or_id, is_username, output_dir, keep_output_dir, and_delete, **options):

        User = get_user_model()
        if is_username:
            user = User.objects.get(username=username_or_id)
        else:
            user = User.objects.get(id=int(username_or_id))
        if not user:
            raise CommandError("User %s does not exist" % username, returncode=-1)

        if options.get('archive'):
            archive = options["archive"]
        else:
            archive = os.path.join(settings.ARCHIVE_ROOT, "%s-%i.tar.xstd" % (user.username, user.id))

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        elif not os.path.exists(os.path.join(output_dir, "meta.json")):
            raise CommandError("output_dir exists and doesn't contain meta.json", returncode=1)

        print("archiving user %s (id=%i)" % (user.username, user.id))
        self.user = user
        self.output_dir = output_dir
        self.archive = archive

        data = {
            "date": datetime.now(),
            "version": "2024-12-23",
        }
        self.dump(data, "meta.json")
        self.export_opml()

        self.export_user()
        self.export_chapters()
        self.export_clients()
        self.export_subscriptions()
        self.export_podcastlist()
        self.export_publishedpodcast()
        self.export_favorite_episodes()
        self.export_suggestions()

        self.create_archive()
        if not keep_output_dir:
            shutil.rmtree(self.output_dir)

        if and_delete:
            self.mark_archived()
            self.remove_records()

    def mark_archived(self):
        self.user.is_active = False
        self.user.profile.archived_date = datetime.now()
        self.user.profile.archive_path = self.archive
        self.user.profile.save()
        self.user.save()


    def dump(self, data, filename):
        with open(os.path.join(self.output_dir, filename), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, cls=MyJSONEncoder)

    @timed
    def create_archive(self):
        if os.path.exists(self.archive):
            os.unlink(self.archive)
        cmd = ["tar", "-cvf", self.archive, "-C", self.output_dir, "-I", "zstd -19", "."]
        print("D: creating %s" % self.archive)
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print("E: Unable to create %s with %r: %r", self.archive, cmd, e)
            return 1

    @timed
    def export_user(self):
        """Here is data introspected via help(User):

        AbstractUser

        date_joined = <django.db.models.query_utils.DeferredAttribute object>
        email = <django.db.models.query_utils.DeferredAttribute object>
        first_name = <django.db.models.query_utils.DeferredAttribute object>
        is_staff = <django.db.models.query_utils.DeferredAttribute object>
        last_name = <django.db.models.query_utils.DeferredAttribute object>
        username = <django.db.models.query_utils.DeferredAttribute object>

        django.contrib.auth.base_user.AbstractBaseUser

         last_login = <django.db.models.query_utils.DeferredAttribute object>
         password = <django.db.models.query_utils.DeferredAttribute object>

        PermissionsMixin

         get_all_permissions(self, obj=None)
         is_superuser = <django.db.models.query_utils.DeferredAttribute object>
        """
        p = self.user.profile

        data = {
            "id": self.user.id,
            "date_joined": self.user.date_joined,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "is_staff": self.user.is_staff,
            "last_name": self.user.last_name,
            "username":  self.user.username,
            "last_login": self.user.last_login,
            # password (hash) not included ^^
            # get_all_permissions not interesting
            "is_superuser": self.user.is_superuser,
            # from UserProfile
            "about": p.about,
            "google_email": p.google_email,
            # tokens and keys not included
            "twitter": p.twitter,
            "settings": p.settings.settings,
        }

        self.dump(data, "user.json")

    @timed
    def export_chapters(self):
        data = []
        last_episode = None
        last_episode_id = None
        for c in Chapter.objects.filter(user=self.user.id).order_by('episode_id', 'start'):
            if last_episode_id and last_episode_id != c.episode_id:
                data.append(last_episode)
                last_episode_id = None
                last_episode = None
            if last_episode is None:
                last_episode_id = c.episode.id
                last_episode = {
                    "id": c.episode.id,
                    "podcast_id": c.episode.podcast_id,
                    "chapters": [],
                }
                if c.episode.guid:
                    last_episode["guid"] = c.episode.guid
            last_episode["chapters"].append({
                "start": c.start,
                "end": c.end,
                "label": c.label,
                "advertisement": c.advertisement,
            })
        if last_episode:
            data.append(last_episode)

        self.dump(data, "chapters.json")

    @timed
    def export_clients(self):
        data = {
            "groups": []
        }
        for g in UserProxy.objects.from_user(self.user).get_grouped_devices():
            group = {
                "is_synced": g.is_synced,
                "devices": [
                    {
                        "uid": c.uid,
                        "name": c.name,
                        "type": c.type,
                        "user_agent": c.user_agent,
                    } for c in g.devices
                ]
            }
            data["groups"].append(group)
        deleted_devices = Client.objects.filter(user=self.user, deleted=True)
        data["deleted"] = [
            { "uid": client.uid, "name": client.name} for client in deleted_devices
        ]
        self.dump(data, "clients.json")

    @timed
    def export_subscriptions(self, episodes_with_state_only=True):
        """change to episodes_with_state_only=False to export episodes even if they have no state for this user"""
        data = []
        podcast_type = ContentType.objects.get_for_model(Podcast)
        last_podcast = None
        last_podcast_id = None
        subscribed_podcast_ids = [s.podcast_id for s in Subscription.objects.filter(user=self.user)]
        episodes_by_podcast = {}
        if episodes_with_state_only:
            for st in EpisodeState.objects.filter(user=self.user):
                e = st.episode
                if e.podcast_id not in episodes_by_podcast:
                    episodes_by_podcast[e.podcast_id] = { e }
                else:
                    episodes_by_podcast[e.podcast_id].add(e)
            for h in EpisodeHistoryEntry.objects.filter(user=self.user).order_by("episode", "timestamp"):
                e = h.episode
                if e.podcast_id not in episodes_by_podcast:
                    episodes_by_podcast[e.podcast_id] = { e }
                else:
                    episodes_by_podcast[e.podcast_id].add(e)
        else:
            # grabbing all episodes at once is better than podcast by podcast
            for e in Episode.objects.filter(podcast_id__in=subscribed_podcast_ids).order_by("podcast_id", "order"):
                if e.podcast_id not in episodes_by_podcast:
                    episodes_by_podcast[e.podcast_id] = [e]
                else:
                    episodes_by_podcast[e.podcast_id].add(e)
        for s in Subscription.objects.filter(user=self.user).order_by("podcast_id", "client_id", "created"):
            if last_podcast_id and last_podcast_id != s.podcast_id:
                data.append(last_podcast)
                last_podcast = None
                last_podcast_id = None
            if last_podcast is None:
                p = s.podcast
                last_podcast_id = p.id
                last_podcast = {
                    "id": p.id,
                    "title": p.title,
                    "subtitle": p.subtitle,
                    "description": p.description,
                    "link": p.link,
                    "language": p.language,
                    # "last_update": p,
                    # "created": p.created,
                    # "modified": p.modified,
                    "license": p.license,
                    "flattr_url": p.flattr_url,
                    # TODO: content_types seems broken in the DB ("v,i,d,e,o" and the like )
                    "content_types": p.content_types,
                    # outdated not exported
                    "author": p.author,
                    "logo_url": p.logo_url,
                    "group_id": p.group_id,
                    # common_episode_title can be recomputed
                    "new_location": p.new_location,
                    # latest_episode_timestamp would be outdated by now
                    # episode_count can be recomputed
                    "hub": p.hub,
                    "twitter": p.twitter,
                    "restrictions": p.restrictions,
                    # max_episode_order not needed
                    # search_vector and search_index_uptodate not needed
                    # update_interval_factor not needed
                    "by_client": [],
                    # XXX: could output url when a single url?
                    "urls": [],
                    # XXX: could output slug when a single slug?
                    "slugs": [],
                    "tags": {},
                    "episodes": [],
                    "categories": [],
                }
                if p.group_id:
                    last_podcast["group_title"] = p.group.title
                    last_podcast["group_member_name"] = p.group_member_name
                for u in p.urls.all() or []:
                    last_podcast["urls"].append(u.url)
                for slug in p.slugs.all() or []:
                    last_podcast["slugs"].append(slug.slug)
                for t in p.tags.all() or []:
                    if t.source != Tag.USER or t.user_id == self.user.id:
                        source = next(x[1] for x in Tag.SOURCE_CHOICES if x[0] == t.source)
                        if source not in last_podcast["tags"]:
                            last_podcast["tags"][source] = []
                        last_podcast["tags"][source].append(t.tag)
                for e in episodes_by_podcast.get(s.podcast_id, []):
                   ep = self.gen_episode(e, include_podcast_ref=False)
                   for st in EpisodeState.objects.filter(user=self.user, episode=e):
                      ep["state"] = {
                          "timestamp": st.timestamp,
                          "action": st.action,
                      }
                   ep["history"] = []
                   for h in EpisodeHistoryEntry.objects.filter(user=self.user, episode=e).order_by("timestamp"):
                       ep["history"].append({
                               "timestamp": h.timestamp,
                               "created": h.created,
                               "client": h.client_id,
                               "action": h.action,
                               "podcast_ref_url": h.podcast_ref_url,
                               "episode_ref_url": h.episode_ref_url,
                               "started": h.started,
                               "stopped": h.stopped,
                               "total": h.total,
                       })
                   last_podcast["episodes"].append(ep)
                user_settings = UserSettings.objects.filter(user=self.user, object_id=s.podcast_id, content_type=podcast_type)
                if user_settings:
                    last_podcast["settings"] = user_settings[0].settings
                for c in CategoryEntry.objects.filter(podcast_id=s.podcast_id):
                    category = {
                        "id": c.id,
                        "created": c.created,
                        "modified": c.modified,
                        "category_id": c.category.id,
                        "category_created": c.category.created,
                        "category_modified": c.category.modified,
                        "title": c.category.title,
                        "tags": [t.tag for t in c.category.tags.all()],
                    }
                    last_podcast["categories"].append(category)
                # FIXME: PodcastGroup, merged_uuids
            client = {
                "client_id": s.client_id,
                "ref_url": s.ref_url,
                "created": s.created,
                "modified": s.modified,
                "deleted": s.deleted,
                "history": []
            }
            for h in HistoryEntry.objects.filter(user_id=self.user.id, client_id=s.client_id, podcast_id=s.podcast_id):
                client["history"].append({
                    "timestamp": h.timestamp,
                    "action": h.action,
                })
            last_podcast["by_client"].append(client)
        if last_podcast:
            data.append(last_podcast)
        self.dump(data, "subscriptions.json")

    @timed
    def export_opml(self):
        podcasts = get_subscribed_podcasts(self.user)
        exporter = Exporter('')
        opml = exporter.generate(podcasts)
        with open(os.path.join(self.output_dir, "subscriptions.opml"), "wb") as f:
            f.write(opml)

    @timed
    def export_podcastlist(self):
        def gen_podcastlist(l):
            podcastlist = {
                "id": l.id,
                "title": l.title,
                "slug": l.slug,
                "created": l.created,
                "modified": l.modified,
                "podcastgroups": [],
                "podcasts": [],
            }
            for en in l.entries.all():
                entry = {
                    "id": en.content_object.id,
                    "title": en.content_object.title,
                    "created": en.created,
                    "modified": en.modified,
                    "slugs": [],
                }
                for slug in en.content_object.slugs.all() or []:
                    entry["slugs"].append(slug.slug)
                if isinstance(en.content_object, PodcastGroup):
                    entry["podcasts"] = []
                    for p in en.content_object.podcast_set.all():
                        entry["podcasts"].append(self.gen_podcast_ref(p))
                    podcastlist["podcastgroups"].append(entry)
                else:
                    entry["url"] = en.content_object.url
                    entry["link"] = en.content_object.link
                    podcastlist["podcasts"].append(entry)
            return podcastlist

        data = {
            "own": [],
            "votes": [],
        }
        seen_podcastlists = set()
        for l in PodcastList.objects.filter(user=self.user):
            seen_podcastlists.add(l.id)
            podcastlist = gen_podcastlist(l)
            data["own"].append(podcastlist)
        for v in Vote.objects.filter(user=self.user):
            if v.content_object.id not in seen_podcastlists:
                podcastlist = gen_podcastlist(v.content_object)
                podcastlist["user"] = v.content_object.user.username
                data["votes"].append({
                    "created": v.created,
                    "modified": v.modified,
                    "list": podcastlist,
                })
        self.dump(data, "podcastlist.json")

    @timed
    def export_publishedpodcast(self):
        data = []
        for pp in PublishedPodcast.objects.filter(publisher=self.user):
            data.append(self.gen_podcast_ref(pp.podcast))
        self.dump(data, "published.json")

    @timed
    def export_favorite_episodes(self):
        data = []
        for f in FavoriteEpisode.objects.filter(user=self.user):
            entry = {
                "id": f.id,
                "created": f.created,
                "modified": f.modified,
                "episode": self.gen_episode(f.episode)
            }
            data.append(entry)
        self.dump(data, "favorites.json")

    @timed
    def export_suggestions(self):
        data = []
        for s in PodcastSuggestion.objects.filter(suggested_to=self.user):
            data.append({
                "id": s.id,
                "created": s.created,
                "modified": s.modified,
                "deleted": s.deleted,
                "podcast": self.gen_podcast_ref(s.podcast),
            })
        self.dump(data, "suggestions.json")

    @staticmethod
    def gen_podcast_ref(p):
        return {
            "id": p.id,
            "title": p.title,
            "url": p.url,
            "link": p.link,
        }

    @classmethod
    def gen_episode(cls, e, include_podcast_ref=True):
        episode = {
            "id": e.id,
            "title": e.title,
            "subtitle": e.subtitle,
            "description": e.description,
            "link": e.link,
            "language": e.language,
            #"created": e.created,
            #"modified": e.modified,
            "license": e.license,
            "flattr_url": e.flattr_url,
            "content_types": e.content_types,
            # MergedIdsModel
            "author": e.author,
            "urls": [],
            "slugs": [],
            # MergedUUIDsMixin
            "guid": e.guid,
            "content": e.content,
            "released": e.released,
            "duration": e.duration,
            "filesize": e.filesize,
            "mimetypes": e.mimetypes,
            "listeners": e.listeners,
        }
        if include_podcast_ref:
            episode["podcast"] = cls.gen_podcast_ref(e.podcast)
        for slug in e.slugs.all() or []:
            episode["slugs"].append(slug.slug)
        for u in e.urls.all() or []:
            episode["urls"].append(u.url)
        return episode

    @timed
    def remove_records(self):
        self.remove(Chapter, user=self.user.id)
        self.remove(EpisodeHistoryEntry, user=self.user.id)
        self.remove(HistoryEntry, user_id=self.user.id)
        self.remove(EpisodeState, user=self.user.id)
        self.remove(Subscription, user=self.user.id)
        self.remove(Client, user=self.user.id)
        self.remove(SyncGroup, user=self.user.id)
        self.remove(UserSettings, user=self.user.id)
        self.remove(FavoriteEpisode, user=self.user.id)
        self.remove(PodcastList, user=self.user.id)
        self.remove(Vote, user=self.user.id)
        self.remove(PublishedPodcast, publisher=self.user.id)
        self.remove(PodcastSuggestion, suggested_to=self.user)

    @staticmethod
    def remove(model, **filters):
        before = perf_counter()
        res = model.objects.filter(**filters).delete()
        print("Deleted %04i %s in %.1fs" % (res[0], model.__name__, perf_counter() - before))
