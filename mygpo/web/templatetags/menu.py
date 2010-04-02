from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

register = template.Library()

HIDDEN_URIS = (
        '/podcast/',
        '/device/',
        '/user/subscriptions/',
)

MENU_STRUCTURE = (
        ('gpodder.net', (
            ('/', _('Home')),
            ('/login/', _('Login')),
            ('/register/', _('Register')),
            ('/logout/', _('Logout')),
        )),
        (_('My Podcasts'), (
            ('/subscriptions/', _('Subscriptions')),
            ('/history/', _('History')),
            ('/suggestions/', _('Suggestions')),
        )),
        (_('My Devices'), (
            ('/devices/', _('Overview')),
            ('/device/', _('Device')),
        )),
        (_('Podcast Directory'), (
            ('/toplist/', _('Toplist')),
            ('/search/', _('Search')),
            ('/toplist/episodes', _('Episodes')),
            ('/podcast/', _('Podcast')),
            ('/user/subscriptions/', _('User subscriptions')),
        )),
        (_('Settings'), (
            ('/account/', _('Account')),
        )),
)

@register.filter
def main_menu(selected):
    links = []
    for label, items in MENU_STRUCTURE:
        links.append((items[0][0], label, [uri for uri, caption in items]))

    items = []
    for uri, caption, subpages in links:
        if selected in subpages:
            items.append('<li class="selected"><a href="%s">%s</a></li>' % \
                    (uri, caption))
        else:
            items.append('<li><a href="%s">%s</a></li>' % (uri, caption))

    s = '<ul class="menu primary">%s</ul>' % ('\n'.join(items),)
    return mark_safe(s)

def get_section_items(selected):
    for label, items in MENU_STRUCTURE:
        if selected in (uri for uri, caption in items):
            return items

@register.filter
def section_menu(selected, title=None):
    items = []
    for uri, caption in get_section_items(selected):
        if uri == selected:
            if title is not None:
                caption = title
            if uri in HIDDEN_URIS:
                items.append('<li class="selected">%s</li>' % caption)
            else:
                items.append('<li class="selected"><a href="%s">%s</a></li>' % \
                        (uri, caption))
        elif uri not in HIDDEN_URIS:
            items.append('<li><a href="%s">%s</a></li>' % (uri, caption))

    s = '<ul class="menu secondary">%s</ul>' % ('\n'.join(items),)
    return mark_safe(s)

