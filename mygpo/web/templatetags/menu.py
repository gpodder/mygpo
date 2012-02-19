from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext


register = template.Library()

HIDDEN_URIS = (
        '/login/',
        '/register/',
        '/podcast/',
        '/device/',
        '/user/subscriptions/',
        '/publisher/podcast/',
        '/share/me',
)

_ = lambda x: x
MENU_STRUCTURE = (
        ('gpodder.net', (
            ('/', _('Home')),
            ('/login/', _('Login')),
            ('/register/', _('Register')),
            ('/contribute/', _('Contribute')),
            ('/developer/', _('Development')),
            ('/online-help', _('Help')),
        )),
        (_('My Podcasts'), (
            ('/subscriptions/', _('Subscriptions')),
            ('/favorites/', _('Favorite Episodes')),
            ('/tags/', _('My Tags')),
            ('/devices/', _('Devices')),
            ('/device/', _('Device')),
            ('/history/', _('History')),
            ('/suggestions/', _('Suggestions')),
        )),
        (_('Share'), (
            ('/share/', _('Overview')),
            ('/share/me', _('My Userpage')),
            ('/user/subscriptions/', _('Subscriptions')),
            ('/share/lists/', _('Podcast Lists')),
        )),
        (_('Podcast Directory'), (
            ('/directory/', _('Directory')),
            ('/toplist/', _('Toplist')),
            ('/search/', _('Search')),
            ('/toplist/episodes', _('Episodes')),
            ('/lists/', _('Podcast Lists')),
            ('/podcast/', _('Podcast')),
        )),
        (_('Settings'), (
            ('/account/', _('Account')),
            ('/account/privacy', _('Privacy')),
        )),
        (_('Publisher'), (
            ('/publisher/', _('Home')),
            ('/publisher/advertise', _('Advertise')),
            ('/publisher/link/', _('Link to gpodder.net')),
            ('/publisher/podcast/', _('Podcast')),
        )),
)

@register.filter
def main_menu(selected):
    found_section = False
    links = []
    for label, items in MENU_STRUCTURE:
        uris = [uri for uri, caption in items]
        if selected in uris:
            found_section = True
        links.append((items[0][0], label, uris))

    items = []
    for uri, caption, subpages in links:
        if selected in subpages or ('/' in subpages and not found_section):
            items.append('<li class="selected"><a href="%s">%s</a></li>' % \
                    (uri, ugettext(caption)))
        else:
            items.append('<li><a href="%s">%s</a></li>' % (uri, ugettext(caption)))

    s = '<ul class="menu primary">%s</ul>' % ('\n'.join(items),)
    return mark_safe(s)

def get_section_items(selected):
    for label, items in MENU_STRUCTURE:
        if selected in (uri for uri, caption in items):
            return items

    # If we arrive here, we cannot find the page items, so return a faked one
    return list(MENU_STRUCTURE[0][1]) + [
            (selected, selected),
    ]

@register.filter
def section_menu(selected, title=None):
    items = []
    for uri, caption in get_section_items(selected):
        if uri == selected:
            if title is not None:
                if len(title) > 35:
                    title = title[:33] + '...'
                caption = title
            if uri in HIDDEN_URIS:
                items.append('<li class="selected">%s</li>' % ugettext(caption))
            else:
                items.append('<li class="selected"><a href="%s">%s</a></li>' % \
                        (uri, ugettext(caption)))
        elif uri not in HIDDEN_URIS:
            items.append('<li><a href="%s">%s</a></li>' % (uri, ugettext(caption)))

    s = '<ul class="menu secondary">%s</ul>' % ('\n'.join(items),)
    return mark_safe(s)

