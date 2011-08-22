from django import template
from django.utils.safestring import mark_safe
from mygpo.core.models import Podcast
from mygpo.data import youtube

register = template.Library()

@register.filter
def is_youtube_video(url):
    return youtube.is_video_link(url)

@register.filter
def get_youtube_id(url):
    return youtube.get_youtube_id(url)

@register.filter
def embed_youtube_video(episode, user):
    #TODO: refactor to template tag and pass podcast as parameter
    podcast = Podcast.get(episode.podcast)
    s = """embedYoutubeVideo("%s", "%s", "%s", "%s");""" % \
         (youtube.get_youtube_id(episode.url), user.username, podcast.url, episode.url)

    return mark_safe(s)

