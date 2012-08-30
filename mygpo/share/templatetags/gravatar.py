import hashlib

from django import template

from mygpo.constants import PODCAST_LOGO_BIG_SIZE


register = template.Library()

GRAVATAR_IMG = 'https://secure.gravatar.com/avatar/{hash_str}?s={size}&d=mm'


@register.simple_tag
def gravatar_img(user):
    return '<img src="{url}" alt="{username}" />'.format(
            url=gravatar_url(user),
            username=user.username)


@register.simple_tag
def gravatar_url(user, size=PODCAST_LOGO_BIG_SIZE):
    email = user.email.strip().lower()
    m = hashlib.md5()
    m.update(email)
    gravatar_hash = m.hexdigest()
    return GRAVATAR_IMG.format(hash_str=gravatar_hash, size=size)
