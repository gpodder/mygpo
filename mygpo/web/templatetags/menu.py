from django import template
from django.utils.safestring import mark_safe
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
        (_('Settings'), (
            ('/account/', _('Account')),
            ('/account/privacy', _('Privacy')),
        )),
)

def get_section_items(selected):
    for label, items in MENU_STRUCTURE:
        if selected in (uri for uri, caption in items):
            return items

    # If we arrive here, we cannot find the page items, so return a faked one
    return list(MENU_STRUCTURE[0][1]) + [
            (selected, selected),
    ]

@register.filter()
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

    return mark_safe('\n'.join(items))
