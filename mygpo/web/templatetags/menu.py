from django import template
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _



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

MENU_STRUCTURE = (
        ('', (
            ('/', _('Home')),
            ('/login/', _('Login')),
            ('/register/', _('Register')),
            ('', _('Docs')),
            ('/contribute/', _('Contribute')),
            ('/developer/', _('Development')),
            ('/privacy/', _('Privacy Policy')),
            ('/online-help', _('Help')),
        )),
        (_('Discover'), (
            ('/directory/', _('Directory')),
            ('/podcast/', _('Podcast')),
            ('/search/', _('Search')),
            ('/missing/', _('Missing Podcast')),
            ('/lists/', _('Podcast Lists')),
            ('/user/subscriptions/', _('User subscriptions')),
            ('/suggestions/', _('Suggestions')),
            ('', _('Features')),
            ('/directory/+license', _('License')),
            ('', _('Toplists')),
            ('/toplist/', _('Podcasts')),
            ('/toplist/episodes', _('Episodes')),
        )),
        (_('Subscriptions'), (
            ('/subscriptions/', _('Subscriptions')),
            ('/favorites/', _('Favorite Episodes')),
            ('/tags/', _('My Tags')),
            ('/devices/', _('Devices')),
            ('/device/', _('Device')),
            ('/history/', _('History')),
        )),
        (_('Community'), (
            ('/share/', _('Overview')),
            ('/share/favorites', _('Favorite Episodes')),
            ('/share/me', _('My Userpage')),
            ('/user/subscriptions/', _('Subscriptions')),
            ('/share/lists/', _('Podcast Lists')),
        )),
        (_('Settings'), (
            ('/account/', _('Account')),
            ('/account/privacy', _('Privacy')),
        )),
        (_('Publish'), (
            ('/publisher/', _('Home')),
            ('/publisher/advertise', _('Advertise')),
            ('/publisher/link/', _('Link to gpodder.net')),
            ('/publisher/podcast/', _('Podcast')),
        )),
)

@register.filter(is_safe=True)
def main_menu(selected):
    found_section = False
    links = []
    for label, items in MENU_STRUCTURE[1:]:
        uris = [uri for uri, caption in items]
        if selected in uris:
            found_section = True
        links.append((items[0][0], label, uris))

    items = []
    for uri, caption, subpages in links:
        if selected in subpages or ('/' in subpages and not found_section):
            items.append('<li class="active"><a href="%s">%s</a></li>' % \
                    (uri, ugettext(caption)))
        else:
            items.append('<li><a href="%s">%s</a></li>' % (uri, ugettext(caption)))

    return '\n'.join(items)

def get_section_items(selected):
    for label, items in MENU_STRUCTURE:
        if selected in (uri for uri, caption in items):
            return items

    # If we arrive here, we cannot find the page items, so return a faked one
    return list(MENU_STRUCTURE[0][1]) + [
            (selected, selected),
    ]

@register.filter(is_safe=True)
def section_menu(selected, title=None):

    items = []
    for uri, caption in get_section_items(selected):
        if uri == selected:
            if title is not None:
                if len(title) > 35:
                    title = title[:33] + '...'
                caption = title
            if uri in HIDDEN_URIS:
                items.append('<li class="active"><a href="">%s</a></li>' % ugettext(caption))
            elif uri == '':
                items.append('<li class="disabled nav-header"><a href="">%s</a></li>' % ugettext(caption))
            else:
                items.append('<li class="active"><a href="%s">%s</a></li>' % \
                        (uri, ugettext(caption)))
        else:
            if uri in HIDDEN_URIS:
                continue

            if not uri:
                items.append('<li class="disabled nav-header"><a>%s</a></li>' % ugettext(caption))
            else:
                items.append('<li><a href="%s">%s</a></li>' % (uri, ugettext(caption)))

    return '\n'.join(items)
