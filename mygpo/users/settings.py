from collections import namedtuple


WellKnownSetting = namedtuple('WellKnownSetting', 'name default')

## Well-known settings
# this should be documented at
# http://wiki.gpodder.org/wiki/Web_Services/API_2/Settings#Known_Settings

# Flag to allow storing of user-agents
STORE_UA = WellKnownSetting('store_user_agent', True)

# Flag to mark a subscription as public
PUBLIC_SUB_PODCAST = WellKnownSetting('public_subscription', True)

# Default public-flag value (stored in the podcast)
PUBLIC_SUB_USER = WellKnownSetting('public_subscriptions', True)

# Flattr authentication token, empty if not logged in
FLATTR_TOKEN = WellKnownSetting('flattr_token', '')

# enable auto-flattring
FLATTR_AUTO = WellKnownSetting('auto_flattr', False)

# auto-flattr mygpo
FLATTR_MYGPO = WellKnownSetting('flattr_mygpo', False)

# username for flattr buttons for own content
FLATTR_USERNAME = WellKnownSetting('flattr_username', '')

# Flag to mark an episode as favorite
FAV_FLAG = WellKnownSetting('is_favorite', False)
