from django import template
from django.utils.safestring import mark_safe

from mygpo.data import flickr


register = template.Library()

@register.filter
def is_flickr_photo(url):
    return flickr.is_flickr_image(url)

@register.filter
def embed_flickr_photo(episode):
    img = flickr.get_display_photo(episode.url)
    s = '<a href="%s" title="%s"><img src="%s" alt="%s" /></a>' % (episode.link, episode.title, img, episode.title)
    return mark_safe(s)
