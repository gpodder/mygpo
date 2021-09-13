from datetime import datetime

from mygpo.api import APIView, RequestException
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.exceptions import ParameterMissing
from mygpo.chapters.models import Chapter
from mygpo.utils import parse_time, normalize_feed_url, get_timestamp


class ChaptersAPI(APIView):
    def post(self, request, username):
        """Add / remove Chapters to/from an episode"""
        user = request.user
        now_ = get_timestamp(datetime.utcnow())

        body = self.parsed_body(request)

        podcast_url, episode_url, update_urls = self.get_urls(body)
        body["podcast"] = podcast_url
        body["episode"] = episode_url

        if not podcast_url or not episode_url:
            raise RequestException("Invalid Podcast or Episode URL")

        self.update_chapters(body, user)
        return JsonResponse({"update_url": update_urls, "timestamp": now_})

    def get(self, request, username):
        """Get chapters for an episode"""
        user = request.user
        now_ = get_timestamp(datetime.utcnow())

        podcast_url, episode_url, _update_urls = self.get_urls(request)

        episode = Episode.objects.filter(
            podcast__urls__url=podcast_url, urls__url=episode_url
        ).get()

        chapters = Chapter.objects.filter(user=user, episode=episode)

        since = self.get_since(request)
        if since:
            chapters = chapters.filter(created__gte=since)

        chapters_json = map(self.chapter_to_json, chapters)

        return JsonResponse({"chapters": chapters_json, "timestamp": now_})

    def update_chapters(self, req, user):
        """Add / remove chapters according to the client's request"""
        podcast = Podcast.objects.get_or_create_for_url(podcast_url).object
        episode = Episode.objects.get_or_create_for_url(podcast, episode_url).object

        # add chapters
        for chapter_data in req.get("chapters_add", []):
            chapter = self.parse_new(user, chapter_data)
            chapter.save()

        # remove chapters
        for chapter_data in req.get("chapters_remove", []):
            start, end = self.parse_rem(chapter_data)
            Chapter.objects.filter(
                user=user, episode=episode, start=start, end=end
            ).delete()

    def parse_new(self, user, chapter_data):
        """Parse a chapter to be added"""
        chapter = Chapter()
        if not "start" in chapter_data:
            raise ParameterMissing("start parameter missing")
        chapter.start = parse_time(chapter_data["start"])

        if not "end" in chapter_data:
            raise ParameterMissing("end parameter missing")
        chapter.end = parse_time(chapter_data["end"])

        chapter.label = chapter_data.get("label", "")
        chapter.advertisement = chapter_data.get("advertisement", False)
        return chapter

    def parse_rem(self, chapter_data):
        """Parse a chapter to be removed"""
        if not "start" in chapter_data:
            raise ParameterMissing("start parameter missing")
        start = parse_time(chapter_data["start"])

        if not "end" in chapter_data:
            raise ParameterMissing("end parameter missing")
        end = parse_time(chapter_data["end"])

        return (start, end)

    def get_urls(self, body):
        """Parse and normalize the URLs from the request"""
        podcast_url = body.get("podcast", "")
        episode_url = body.get("episode", "")

        if not podcast_url:
            raise RequestException("Podcast URL missing")

        if not episode_url:
            raise RequestException("Episode URL missing")

        update_urls = []

        # podcast sanitizing
        s_podcast_url = normalize_feed_url(podcast_url)
        if s_podcast_url != podcast_url:
            update_urls.append((podcast_url, s_podcast_url or ""))

        # episode sanitizing
        s_episode_url = normalize_feed_url(episode_url, "episode")
        if s_episode_url != episode_url:
            update_urls.append((episode_url, s_episode_url or ""))

        return s_podcast_url, s_episode_url, update_urls

    def chapter_to_json(self, chapter):
        """JSON representation of Chapter for GET response"""
        return {
            "start": chapter.start,
            "end": chapter.end,
            "label": chapter.label,
            "advertisement": chapter.advertisement,
            "timestamp": chapter.created,
        }
