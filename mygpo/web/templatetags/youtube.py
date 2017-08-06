from django import template

from mygpo.data import youtube


register = template.Library()

@register.filter
def is_youtube_video(url):
    return youtube.is_video_link(url)

@register.filter
def get_youtube_id(url):
    return youtube.get_youtube_id(url)

@register.simple_tag
def embed_youtube_video(podcast, episode, user):
    s = """embedYoutubeVideo("%s", "%s", "%s", "%s");""" % \
         (youtube.get_youtube_id(episode.url), user.username, podcast.url, episode.url)

    return s
