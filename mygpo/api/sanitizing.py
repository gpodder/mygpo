import collections

from django.core.cache import cache

from mygpo.core import models
from mygpo.api.models import Podcast, Episode, EpisodeAction
from mygpo.data.models import Listener
from mygpo.log import log
from mygpo.utils import iterate_together, progress
import urlparse
import re



def sanitize_urls(urls, obj_type='podcast', rules=None):
    """ Apply sanitizing rules to the given URLs and return the results """

    rules = get_sanitizing_rules(obj_type, rules)
    return (sanitize_url(url, rules=rules) for url in urls)


def sanitize_url(url, obj_type='podcast', rules=None):
    """ Apply sanitizing rules to the given URL and return the results """

    rules = get_sanitizing_rules(obj_type, rules=rules)
    url = basic_sanitizing(url)
    url = apply_sanitizing_rules(url, rules)
    return url


def get_sanitizing_rules(obj_type, rules=None):
    """ Returns the sanitizing-rules from the cache or the database """

    cache_name = '%s-sanitizing-rules' % obj_type

    sanitizing_rules = \
            rules or \
            cache.get(cache_name) or \
            list(models.SanitizingRule.for_obj_type(obj_type))

    cache.set(cache_name, sanitizing_rules, 60 * 60)

    return sanitizing_rules


def basic_sanitizing(url):
    """
    does basic sanitizing through urlparse and additionally converts the netloc to lowercase
    """
    r = urlparse.urlsplit(url)
    netloc = r.netloc.lower()
    r2 = urlparse.SplitResult(r.scheme, netloc, r.path, r.query, r.fragment)
    return r2.geturl()


def apply_sanitizing_rules(url, rules):
    """
    applies all url sanitizing rules to the given url
    setting podcast=True uses only those rules which have use_podcast set to True. 
    When passing podcast=False this check is ommitted. The same is valid
    for episode.
    """

    for rule in rules:

        orig = url

        # check for precompiled regex first
        if hasattr(rule, 'search_re'):
            url = rule.search_re.sub(rule.replace, url)
        else:
            url = re.sub(rule.search, rule.replace, url)

        if orig != url:
            c = getattr(rule, 'hits', 0)
            rule.hits = c+1

    return url


def maintenance(dry_run=False):
    """
    This currently checks how many podcasts could be removed by
    applying both basic sanitizing rules and those from the database.

    This will later be used to replace podcasts!
    """

    podcast_rules = get_sanitizing_rules('podcast')
    episode_rules = get_sanitizing_rules('episode')

    num_podcasts = Podcast.objects.count()
    num_episodes = Episode.objects.count()

    print 'Stats'
    print ' * %d podcasts - %d rules' % (num_podcasts, len(podcast_rules))
    print ' * %d episodes - %d rules' % (num_episodes, len(episode_rules))
    if dry_run:
        print ' * dry run - nothing will be written to the database'
    print

    print 'precompiling regular expressions'

    podcast_rules = list(precompile_rules(podcast_rules))
    episode_rules = list(precompile_rules(episode_rules))

    p_stats = collections.defaultdict(int)
    e_stats = collections.defaultdict(int)

    podcasts = Podcast.objects.only('id', 'url').order_by('id').iterator()

    for n, p in enumerate(podcasts):
        try:
            su = sanitize_url(p.url, rules=podcast_rules)
        except Exception, e:
            log('failed to sanitize url for podcast %s: %s' % (p.id, e))
            print 'failed to sanitize url for podcast %s: %s' % (p.id, e)
            p_stats['error'] += 1
            continue

        # nothing to do
        if su == p.url:
            p_stats['unchanged'] += 1
            continue

        # invalid podcast, remove
        if su == '':
            try:
                if not dry_run:
                    p.delete()
                p_stats['deleted'] += 1

            except Exception, e:
                log('failed to delete podcast %s: %s' % (p.id, e))
                print 'failed to delete podcast %s: %s' % (p.id, e)
                p_stats['error'] += 1

            continue

        try:
            su_podcast = Podcast.objects.get(url=su)

        except Podcast.DoesNotExist, e:
            # "target" podcast does not exist, we simply change the url
            if not dry_run:
                log('updating podcast %s - "%s" => "%s"' % (p.id, p.url, su))
                p.url = su
                p.save()

            p_stats['updated'] += 1
            continue

        # nothing to do
        if p == su_podcast:
            p_stats['unchanged'] += 1
            continue

        # last option - merge podcasts
        try:
            if not dry_run:
                rewrite_podcasts(p, su_podcast)
                p.delete()

            p_stats['merged'] += 1

        except Exception, e:
            log('error rewriting podcast %s: %s' % (p.id, e))
            print 'error rewriting podcast %s: %s' % (p.id, e)
            p_stats['error'] += 1
            continue

        progress(n+1, num_podcasts, str(p.id))

    print 'finished %s podcasts' % (n+1)
    print '%(unchanged)d unchanged, %(merged)d merged, %(updated)d updated, %(deleted)d deleted, %(error)d error' % p_stats
    print 'Hits'
    for _, r in podcast_rules:
        print '% 30s: %d' % (r.slug, getattr(r, 'hits', 0) if hasattr(r, 'hits') else 0)

    episodes = Episode.objects.only('id', 'url').order_by('id').iterator()
    for e in episodes:
        try:
            su = sanitize_url(e.url, rules=episode_rules)
        except Exception, ex:
            log('failed to sanitize url for episode %s: %s' % (e.id, ex))
            print 'failed to sanitize url for episode %s: %s' % (e.id, ex)
            e_stats['error'] += 1
            continue

        # nothing to do
        if su == e.url:
            e_stats['unchanged'] += 1
            continue

        # invalid episode, remove
        if su == '':
            try:
                if not dry_run:
                    delete_episode(e)

                e_stats['deleted'] += 1
            except Exception, ex:
                log('failed to delete episode %s: %s' % (e.id, ex))
                print 'failed to delete episode %s: %s' % (e.id, ex)
                e_stats['error'] += 1

            continue

        try:
            su_episode = Episode.objects.get(url=su, podcast=e.podcast)

        except Episode.DoesNotExist, ex:
            # "target" episode does not exist, we simply change the url
            if not dry_run:
                log('updating episode %s - "%s" => "%s"' % (e.id, e.url, su))
                e.url = su
                e.save()

            e_stats['updated'] += 1
            continue

        # nothing to do
        if e == su_episode:
            e_stats['unchanged'] += 1
            continue


        # last option - merge episodes
        try:
            if not dry_run:
                rewrite_episode_actions(e, su_episode)
                rewrite_listeners(e, su_episode)
                e.delete()

            e_stats['merged'] += 1

        except Exception, ex:
            log('error rewriting episode %s: %s' % (e.id, ex))
            print 'error rewriting episode %s: %s' % (e.id, ex)
            e_stats['error'] += 1
            continue

        progress(n+1, num_episodes, str(e.id))

    print 'finished %s episodes' % num_episodes
    print '%(unchanged)d unchanged, %(merged)d merged, %(updated)d updated, %(deleted)d deleted, %(error)d error' % e_stats
    print
    print 'finished %s podcasts' % num_podcasts
    print '%(unchanged)d unchanged, %(merged)d merged, %(updated)d updated, %(deleted)d deleted, %(error)d error' % p_stats
    print
    print 'Hits'
    for _, r in episode_rules:
        print '% 30s: %d' % (r.slug, getattr(r, 'hits', 0) if hasattr(r, 'hits') else 0)



def delete_episode(e):
    EpisodeAction.objects.filter(episode=e).delete()
    Listener.objects.filter(episode=e).delete()
    e.delete()


def rewrite_podcasts(p_old, p_new):

    log('merging podcast %s "%s" to correct podcast %s "%s"' % (p_old.id, p_old.url, p_new.id, p_new.url))

    rewrite_episodes(p_old, p_new)

    rewrite_newpodcast(p_old, p_new)

def rewrite_newpodcast(p_old, p_new):
    p_n = models.Podcast.for_oldid(p_new.id)
    p_o = models.Podcast.for_oldid(p_old.id)

    if not p_o:
        return


    # merge subscriber data
    subscribers = []
    compare = lambda a, b: cmp(a.timestamp, b.timestamp)
    for n, o in iterate_together(p_n.subscribers, p_o.subscribers):

        # we assume that the new podcast has much more subscribers
        # taking only count of the old podcast would look like a drop
        if None in (n, o):
            continue

        subscribers.append(
                models.SubscriberData(
                    timestamp = o.timestamp,
                    subscriber_count = n.subscriber_count + \
                                       n.subscriber_count if n else 0\
                )
            )

    p_n.subscribers = subscribers

    p_n.save()
    p_o.delete()


def rewrite_episodes(p_old, p_new):

    for e in Episode.objects.filter(podcast=p_old):
        try:
            e_new, created_ = Episode.objects.get_or_create(podcast=p_new, url=e.url)

            log('episode %s (url %s, podcast %s) already exists; updating episode actions for episode %s (url %s, podcast %s)' % (e_new.id, e.url, p_new.id, e.id, e.url, p_old.id))
            rewrite_episode_actions(e, e_new)
            log('episode actions for episode %s (url "%s", podcast %s) updated.' % (e.id, e.url, p_old.id))
            rewrite_listeners(e, e_new)
            log('listeners for episode %s (url "%s", podcast %s) updated.' % (e.id, e.url, p_old.id))
            e.delete()

        except Episode.DoesNotExist:
            log('updating episode %s (url "%s", podcast %s => %s)' % (e.id, e.url, p_old.id, p_new.id))
            e.podcast = p_new
            e.save()


def rewrite_episode_actions(e_old, e_new):

    for ea in EpisodeAction.objects.filter(episode=e_old):
        try:
            log('updating episode action %s (user %s, timestamp %s, episode %s => %s)' % (ea.id, ea.user.id, ea.timestamp, e_old.id, e_new.id))
            ea.epsidode = e_new
            ea.save()

        except Exception, e:
            log('error updating episode action %s: %s, deleting' % (sa.id, e))
            ea.delete()


def rewrite_listeners(e_old, e_new):

    for l in Listener.objects.filter(episode=e_old):
        try:
            log('updating listener %s (user %s, device %s, podcast %s, episode %s => %s)' % (l.id, l.user.id, l.device.id, l.podcast.id, e_old.id, e_new.id))
            l.episode = e_new
            l.podcast = e_new.podcast
            l.save()

        except Exception, e:
            log('error updating listener %s: %s, deleting' % (l.id, e))
            l.delete()


def precompile_rules(rules):
    for rule in rules:
        rule.search_re = re.compile(rule.search, re.UNICODE)
        yield rule
