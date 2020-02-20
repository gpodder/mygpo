# Set _ to no-op, because we just want to mark the strings as
# translatable and will use gettext on these strings later on

from django.utils.translation import gettext_lazy as _


EPISODE_ACTION_TYPES = (
    ('download', _('downloaded')),
    ('play', _('played')),
    ('delete', _('deleted')),
    ('new', _('marked as new')),
    ('flattr', _('flattr\'d')),
)


SUBSCRIBE_ACTION = 1
UNSUBSCRIBE_ACTION = -1

SUBSCRIPTION_ACTION_TYPES = (
    (SUBSCRIBE_ACTION, _('subscribed')),
    (UNSUBSCRIBE_ACTION, _('unsubscribed')),
)
