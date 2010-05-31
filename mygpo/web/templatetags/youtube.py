from django import template
from django.utils.safestring import mark_safe
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

    s = """embedYoutubeVideo("%s", "%s", "%s", "%s");""" % \
         (youtube.get_youtube_id(episode.url), user.username, episode.podcast.url, episode.url)

    return mark_safe(s)

