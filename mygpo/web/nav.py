
import collections

from mygpo.subscriptions import get_subscribed_podcasts


NavEntry = collections.namedtuple('NavEntry', 'urlname label')

PRIMARY_NAV = [
    NavEntry('home', 'gpodder.net'),
    NavEntry('directory-home', 'Directory'),
    NavEntry('subscriptions', 'Subscriptions'),
    NavEntry('share', 'Community'),
    NavEntry('publisher', 'Publish'),
]

PRIMARY_NAV_AUTH = [
    NavEntry('account', 'Account'),
    NavEntry('logout', 'Logout'),
]

PRIMARY_NAV_ANON = [
    NavEntry('login', 'Login'),
    NavEntry('register', 'Register'),
]


# context processor for primary navigation
def primary_navigation(request):

    user = request.user

    if user.is_authenticated:
        nav = PRIMARY_NAV + PRIMARY_NAV_AUTH
    else:
        nav = PRIMARY_NAV + PRIMARY_NAV_ANON

    if user.is_authenticated:
        subscriptions = get_subscribed_podcasts(user)
    else:
        subscriptions = []

    return {
        'primary_nav': nav,
        'subscriptions': subscriptions,
    }
