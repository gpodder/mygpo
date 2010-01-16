from mygpo.api.models import URLSanitizingRule, Podcast, ToplistEntry, SuggestionEntry, SubscriptionAction, SubscriptionMeta, Subscription, Episode, EpisodeAction
from mygpo.log import log
import urlparse
import re
import sys

def sanitize_url(url, podcast=True, episode=False):
    url = basic_sanitizing(url)
    url = apply_sanitizing_rules(url, podcast, episode)
    return url

def basic_sanitizing(url):
    """
    does basic sanitizing through urlparse and additionally converts the netloc to lowercase
    """
    r = urlparse.urlsplit(url)
    netloc = r.netloc.lower()
    r2 = urlparse.SplitResult(r.scheme, netloc, r.path, r.query, r.fragment)
    return r2.geturl()

def apply_sanitizing_rules(url, podcast=True, episode=False):
    """
    applies all url sanitizing rules to the given url
    setting podcast=True uses only those rules which have use_podcast set to True. 
    When passing podcast=False this check is ommitted. The same is valid
    for episode.
    """
    rules = URLSanitizingRule.objects.all().order_by('priority')
    if podcast: rules = rules.filter(use_podcast=True)
    if episode: rules = rules.filter(use_podcast=True)

    for r in rules:
        url = re.sub(r.search, r.replace, url)

    return url

def maintenance():
    """
    This currently checks how many podcasts could be removed by 
    applying both basic sanitizing rules and those from the database.

    This will later be used to replace podcasts!
    """
    print 'Stats'
    print ' * %s podcasts' % Podcast.objects.count()
    print ' * %s rules' % URLSanitizingRule.objects.count()
    print
    print 'working...'

    unchanged = 0
    merged = 0
    updated = 0

    count = 0
    podcasts = Podcast.objects.all()
    duplicates = 0
    sanitized_urls = []
    for p in podcasts:
        count += 1
        if (count % 1000) == 0: print '%s %% (podcast id %s)' % (((count + 0.0)/podcasts.count()*100), p.id)

        su = sanitize_url(p.url)
        if su == p.url: 
            unchanged += 1
            continue
    
        try:
            su_podcast = Podcast.objects.get(url=su)
            rewrite_podcasts(p, su_podcast)
            p.delete()
            merged += 1

        except Podcast.DoesNotExist, e:
            log('updating podcast %s - %s => %s' % (p.id, p.url, su))
            p.url = su
            p.save()
            updated += 1

    print ' * %s unchanged' % unchanged
    print ' * %s merged' % merged
    print ' * %s updated' % updated


def rewrite_podcasts(p_old, p_new):

    log('merging podcast %s (%s) to correct podcast %s (%s)' % (p_old.id, p_old.url, p_new.id, p_new.url))

    # we simply delete incorrect toplist and suggestions entries, 
    # because we can't re-calculate them
    ToplistEntry.objects.filter(podcast=p_old).delete()
    SuggestionEntry.objects.filter(podcast=p_old).delete()

    rewrite_episodes(p_old, p_new)

    for sm in SubscriptionMeta.objects.filter(podcast=p_old):
        try:
            sm_new = SubscriptionMeta.objects.get(user=sm.user, podcast=p_new)
            log('subscription meta %s (user %s, podcast %s) already exists, deleting %s (user %s, podcast %s)' % (sm_new.id, sm.user.id, p_new.id, sm.id, sm.user.id, p_old.id))
            # meta-info already exist for the correct podcast, delete the other one
            sm.delete()

        except SubscriptionMeta.DoesNotExist:
            # meta-info for new podcast does not yet exist, update the old one
            log('updating subscription meta %s (user %s, podcast %s => %s)' % (sm.id, sm.user, p_old.id, p_new.id))
            sm.podcast = p_new
            sm.save()

    for sa in SubscriptionAction.objects.filter(podcast=p_old):
        try:
            log('updating subscription action %s (device %s, action %s, timestamp %s, podcast %s => %s)' % (sa.id, sa.device.id, sa.action, sa.timestamp, sa.podcast.id, p_new.id))
            sa.podcast = p_new
            sa.save()
        except Exception as e:
            log('error updating subscription action %s: %s, deleting' % (sa.id, e))
            sa.delete()

def rewrite_episodes(p_old, p_new):

    for e in Episode.objects.filter(podcast=p_old):
        try:
            e_new = Episode.objects.get(podcast=p_new, url=e.url)
            log('episode %s (url %s, podcast %s) already exists; updating episode actions for episode %s (url %s, podcast %s)' % (e_new.id, e.url, p_new.id, e.id, e.url, p_old.id))
            rewrite_episode_actions(e, e_new)
            log('episode actions for episode %s (url %s, podcast %s) updated, deleting.' % (e.id, e.url, p_old.id))
            e.delete()

        except Episode.DoesNotExist:
            log('updating episode %s (url %s, podcast %s => %s)' % (e.id, e.url, p_old.id, p_new.od))
            e.podcast = p_new
            e.save()

        
def rewrite_episode_actions(e_old, e_new):
    
    for ea in EpisodeAction.objects.filter(episode=e_old):
        try:
            log('updating episode action %s (user %s, timestamp %s, episode %s => %s)' % (ea.id, ea.user.id, ea.timestamp, e_old.id, e_new.id))
            ea.epsidode = e_new
            ea.save()

        except Exception as e:
            log('error updating episode action %s: %s, deleting' % (sa.id, e))
            ea.delete()

