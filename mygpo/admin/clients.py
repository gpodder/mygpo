import re
from collections import namedtuple

from mygpo.users.models import User
from mygpo.counter import Counter


Client = namedtuple('Client', 'client client_version lib lib_version os os_version')


class UserAgentStats(object):
    """ Provides User-Agent statistics """

    def __init__(self):
        self._useragents = None


    def get_entries(self):
        if self._useragents is None:
            res = User.view('clients/by_ua_string',
                wrap_doc    = False,
                group_level = 1,
                stale       = 'update_after',
            )

            self._useragents = Counter(dict((r['key'], r['value']) for r in res))

        return self._useragents


    @property
    def max_users(self):
        uas = self.get_entries()
        if uas:
            return uas.most_common(1)[0][1]
        else:
            return 0

    @property
    def total_users(self):
        uas = self.get_entries()
        if uas:
            return sum(uas.values())
        else:
            return 0


# regular expressions for detecting a client application from a User-Agent
RE_GPODROID = re.compile('GpodRoid ([0-9.]+) Mozilla/5.0 \(Linux; U; Android ([0-9a-z.-]+);')
RE_GPODDER = re.compile('mygpoclient/([0-9.]+) \([^)]+\) gPodder/([0-9.]+)')
RE_MYGPOCLIENT = re.compile('mygpoclient/([0-9.]+) \([^)]+\)')
RE_CLEMENTINE = re.compile('Clementine ([0-9a-z.-]+)')
RE_AMAROK = re.compile('amarok/([0-9.]+)')
RE_GPNACCOUNT = re.compile('GPodder.net Account for Android')


class ClientStats(UserAgentStats):
    """ Provides statistics about client applications """

    def __init__(self):
        self._clients = None
        super(ClientStats, self).__init__()


    def get_entries(self):

        if self._clients is None:
            self._clients = Counter()

            uas = super(ClientStats, self).get_entries()
            for ua_string, count in uas.items():
                client = self.parse_ua_string(ua_string) or ua_string
                self._clients[client] += count

        return self._clients


    def parse_ua_string(self, ua_string):

        m = RE_GPODROID.search(ua_string)
        if m:
            return Client('gpodroid', m.group(1), None, None, 'android', m.group(2))

        m = RE_GPODDER.search(ua_string)
        if m:
            return Client('gpodder', m.group(2), 'mygpoclient', m.group(1), None, None)

        m = RE_MYGPOCLIENT.search(ua_string)
        if m:
            return Client(None, None, 'mygpoclient', m.group(1), None, None)

        m = RE_CLEMENTINE.search(ua_string)
        if m:
            return Client('clementine', m.group(1), None, None, None, None)

        m = RE_AMAROK.search(ua_string)
        if m:
            return Client('amarok', m.group(1), None, None, None, None)

        m = RE_GPNACCOUNT.search(ua_string)
        if m:
            return Client(None, None, 'gpodder.net-account-android', None, 'android', None)

        return None
