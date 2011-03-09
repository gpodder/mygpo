from mygpo.core import models
from mygpo.api.models import Podcast, SubscriptionAction, SubscriptionMeta, Subscription, Episode, EpisodeAction
from mygpo.api.models.episodes import Chapter
from mygpo.data.models import BackendSubscription, Listener
from mygpo.log import log
from mygpo.utils import iterate_together
import urlparse
import re



def sanitize_url(url, obj_type='podcast', rules=None):
    rules = rules or models.SanitizingRule.for_obj_type(obj_type)
    url = basic_sanitizing(url)
    url = apply_sanitizing_rules(url, rules)
    return url


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

    for r in rules:
        if isinstance(r, tuple):
            precompiled, r = r
        else:
            precompiled = None


        orig = url

        if precompiled:
            url = precompiled.sub(r.replace, url)
        else:
            url = re.sub(r.search, r.replace, url)

        if orig != url:
            c = getattr(r, 'hits', 0) if hasattr(r, 'hits') else 0
            r.hits = c+1

    return url


def maintenance(dry_run=False):
    """
    This currently checks how many podcasts could be removed by
    applying both basic sanitizing rules and those from the database.

    This will later be used to replace podcasts!
    """

    podcast_rules = models.SanitizingRule.for_obj_type('podcast')
    episode_rules = models.SanitizingRule.for_obj_type('episode')


    print 'Stats'
    print ' * %d podcasts - %d rules' % (Podcast.objects.count(), len(podcast_rules))
    print ' * %d episodes - %d rules' % (Episode.objects.count(), len(episode_rules))
    if dry_run:
        print ' * dry run - nothing will be written to the database'
    print

    print 'precompiling regular expressions'

    podcast_rules = precompile_rules(podcast_rules)
    episode_rules = precompile_rules(episode_rules)

    p_unchanged = 0
    p_merged = 0
    p_updated = 0
    p_deleted = 0
    p_error = 0
    e_unchanged = 0
    e_merged = 0
    e_updated = 0
    e_deleted = 0
    e_error = 0

    count = 0

    podcasts = Podcast.objects.only('id', 'url').iterator()
    total = Podcast.objects.count()
    duplicates = 0
    sanitized_urls = []
    for p in podcasts:
        count += 1
        if (count % 1000) == 0: print '% 3.2f%% (podcast id %s)' % (((count + 0.0)/total*100), p.id)
        try:
            su = sanitize_url(p.url, rules=podcast_rules)
        except Exception, e:
            raise
            log('failed to sanitize url for podcast %s: %s' % (p.id, e))
            print 'failed to sanitize url for podcast %s: %s' % (p.id, e)
            return
            p_error += 1
            continue

        # nothing to do
        if su == p.url:
            p_unchanged += 1
            continue

        # invalid podcast, remove
        if su == '':
            try:
                if not dry_run:
                    delete_podcast(p)
                p_deleted += 1

            except Exception, e:
                log('failed to delete podcast %s: %s' % (p.id, e))
                print 'failed to delete podcast %s: %s' % (p.id, e)
                p_error += 1

            continue

        try:
            su_podcast = Podcast.objects.get(url=su)

        except Podcast.DoesNotExist, e:
            # "target" podcast does not exist, we simply change the url
            if not dry_run:
                log('updating podcast %s - "%s" => "%s"' % (p.id, p.url, su))
                p.url = su
                p.save()

            p_updated += 1
            continue

        # nothing to do
        if p == su_podcast:
            p_unchanged += 1
            continue

        # last option - merge podcasts
        try:
            if not dry_run:
                rewrite_podcasts(p, su_podcast)
                tmp = Subscription.objects.filter(podcast=p)
                if tmp.count() > 0: print tmp.count()
                p.delete()

            p_merged += 1

        except Exception, e:
            log('error rewriting podcast %s: %s' % (p.id, e))
            print 'error rewriting podcast %s: %s' % (p.id, e)
            p_error += 1
            continue

    print 'finished %s podcasts' % count
    print ' * %s unchanged' % p_unchanged
    print ' * %s merged' % p_merged
    print ' * %s updated' % p_updated
    print ' * %s deleted' % p_deleted
    print ' * %s error' % p_error
    print 'Hits'
    for _, r in podcast_rules:
        print '% 30s: %d' % (r.slug, getattr(r, 'hits', 0) if hasattr(r, 'hits') else 0)

    count = 0
    total = Episode.objects.count()
    episodes = Episode.objects.only('id', 'url').iterator()
    for e in episodes:
        count += 1
        if (count % 10000) == 0: print '% 3.2f%% (episode id %s)' % (((count + 0.0)/total*100), e.id)
        try:
            su = sanitize_url(e.url, rules=episode_rules)
        except Exception, ex:
            log('failed to sanitize url for episode %s: %s' % (e.id, ex))
            print 'failed to sanitize url for episode %s: %s' % (e.id, ex)
            p_error += 1
            continue

        # nothing to do
        if su == e.url:
            e_unchanged += 1
            continue

        # invalid episode, remove
        if su == '':
            try:
                if not dry_run:
                    delete_episode(e)

                e_deleted += 1
            except Exception, ex:
                log('failed to delete episode %s: %s' % (e.id, ex))
                print 'failed to delete episode %s: %s' % (e.id, ex)
                e_error += 1

            continue

        try:
            su_episode = Episode.objects.get(url=su, podcast=e.podcast)

        except Episode.DoesNotExist, ex:
            # "target" episode does not exist, we simply change the url
            if not dry_run:
                log('updating episode %s - "%s" => "%s"' % (e.id, e.url, su))
                e.url = su
                e.save()

            e_updated += 1
            continue

        # nothing to do
        if e == su_episode:
            e_unchanged += 1
            continue


        # last option - merge episodes
        try:
            if not dry_run:
                rewrite_episode_actions(e, su_episode)
                rewrite_listeners(e, su_episode)
                rewrite_chapters(e, su_episode)
                e.delete()

            e_merged += 1

        except Exception, ex:
            log('error rewriting episode %s: %s' % (e.id, ex))
            print 'error rewriting episode %s: %s' % (e.id, ex)
            e_error += 1
            continue


    print 'finished %s episodes' % count
    print ' * %s unchanged' % e_unchanged
    print ' * %s merged' % e_merged
    print ' * %s updated' % e_updated
    print ' * %s deleted' % e_deleted
    print ' * %s error' % e_error
    print
    print 'finished %s podcasts' % count
    print ' * %s unchanged' % p_unchanged
    print ' * %s merged' % p_merged
    print ' * %s updated' % p_updated
    print ' * %s deleted' % p_deleted
    print ' * %s error' % p_error
    print
    print 'Hits'
    for _, r in episode_rules:
        print '% 30s: %d' % (r.slug, getattr(r, 'hits', 0) if hasattr(r, 'hits') else 0)



def delete_podcast(p):
    SubscriptionAction.objects.filter(podcast=p).delete()
    BackendSubscription.objects.filter(podcast=p).delete()
    p.delete()


def delete_episode(e):
    EpisodeAction.objects.filter(episode=e).delete()
    Listener.objects.filter(episode=e).delete()
    e.delete()


def rewrite_podcasts(p_old, p_new):

    log('merging podcast %s "%s" to correct podcast %s "%s"' % (p_old.id, p_old.url, p_new.id, p_new.url))

    rewrite_episodes(p_old, p_new)

    rewrite_newpodcast(p_old, p_new)

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
        except Exception, e:
            log('error updating subscription action %s: %s, deleting' % (sa.id, e))
            sa.delete()

    for sub in BackendSubscription.objects.filter(podcast=p_old):
        try:
            log('updating subscription %s (device %s, user %s, since %s, podcast %s => %s)' % (sub.id, sub.device.id, sub.user.id, sub.subscribed_since, p_old.id, p_new.id))
            sub.podcast = p_new
            sub.save()
        except Exception, e:
            log('error updating subscription %s: %s, deleting' % (sub.id, e))
            sub.delete()


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
            rewrite_chapters(e, e_new)
            log('chapters for episode %s (url "%s", podcast %s) updated.' % (e.id, e.url, p_old.id))
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


def rewrite_chapters(e_old, e_new):

    for c in Chapter.objects.filter(episode=e_old):
        try:
            log('updating chapter %s (user %s, device %s, episode %s => %s)' % (c.id, c.device.id, e_old.id, e_new.id))
            c.episode = e_new
            c.save()

        except Exception, e:
            log('error updating chapter %s: %s, deleting' % (c.id, e))
            c.delete()


def precompile_rules(rules):
    return [( re.compile(rule.search, re.UNICODE), rule) for rule in rules]
