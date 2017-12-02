from collections import namedtuple


WellKnownSetting = namedtuple('WellKnownSetting', 'name default')

## Well-known settings
# this should be documented at
# https://gpoddernet.readthedocs.io/en/latest/api//Settings#Known_Settings

# Flag to allow storing of user-agents
STORE_UA = WellKnownSetting('store_user_agent', True)

# Flag to mark a subscription as public
PUBLIC_SUB_PODCAST = WellKnownSetting('public_subscription', True)

# Default public-flag value (stored in the podcast)
PUBLIC_SUB_USER = WellKnownSetting('public_subscriptions', True)

# Flag to mark an episode as favorite
FAV_FLAG = WellKnownSetting('is_favorite', False)
