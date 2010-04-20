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

from mygpo.api.models import ToplistEntry
import re

try:
    import json

    # Python 2.5 seems to have a different json module
    if not 'dumps' in dir(json):
        raise ImportError

except ImportError:
    import json


def get_toplist(count, languages=None):
    """
    Returns count podcasts with the most subscribers (individual users)
    If languages is given as an array of 2-character languages codes, only
    podcasts with the given languages are considered

    For language-specific lists the entries' oldplace attribute is calculated
    based on the same language list
    """
    if not languages:
        return ToplistEntry.objects.all().order_by('-subscriptions')[:count]
    else:
        regex = '^(' + '|'.join(languages) + ')'
        podcast_entries_base = ToplistEntry.objects.filter(podcast__language__regex=regex)
        group_entries_base = ToplistEntry.objects.filter(podcast_group__podcast__language__regex=regex).distinct()

        old_podcast_entries = list(podcast_entries_base.exclude(oldplace=0).order_by('oldplace')[:count])
        old_group_entries = list(group_entries_base.exclude(oldplace=0).order_by('oldplace')[:count])
        old_list = merge_toplists(old_podcast_entries, old_group_entries, lambda x: x.oldplace, reverse=False)
        old_items = [e.get_item() for e in old_list]

        podcast_entries = podcast_entries_base.order_by('-subscriptions')[:count]
        group_entries = group_entries_base.order_by('-subscriptions')[:count]
        cur_list = merge_toplists(podcast_entries, group_entries, lambda x: x.subscriptions, reverse=True, count=count)

        for x in cur_list:
            x.oldplace = old_items.index(x.get_item())+1 if x.get_item() in old_items else 0

        return cur_list


def merge_toplists(podcast_entries, group_entries, sortkey, reverse, count=None):
    """
    merges a podcast- and a group toplist based on the given sortkey
    """
    entries = list(podcast_entries)
    entries.extend(group_entries)
    entries.sort(key=sortkey, reverse=reverse)
    if count:
        entries = entries[:count]
    return entries

