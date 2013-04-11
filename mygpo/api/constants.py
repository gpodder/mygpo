#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

# Set _ to no-op, because we just want to mark the strings as
# translatable and will use gettext on these strings later on

from django.utils.translation import ugettext_lazy as _


EPISODE_ACTION_TYPES = (
        ('download', _('downloaded')),
        ('play',     _('played')),
        ('delete',   _('deleted')),
        ('new',      _('marked as new')),
        ('flattr',   _('flattr\'d')),
)


DEVICE_TYPES = (
        ('desktop', _('Desktop')),
        ('laptop', _('Laptop')),
        ('mobile', _('Cell phone')),
        ('server', _('Server')),
        ('other', _('Other')),
)


SUBSCRIBE_ACTION = 1
UNSUBSCRIBE_ACTION = -1

SUBSCRIPTION_ACTION_TYPES = (
        (SUBSCRIBE_ACTION, _('subscribed')),
        (UNSUBSCRIBE_ACTION, _('unsubscribed')),
)
