from mygpo.api.models import URLSanitizingRule, Podcast
import urlparse
import re


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

    podcasts = Podcast.objects.all()
    duplicates = 0
    sanitized_urls = []
    for p in podcasts:
        su = p.url
        su = basic_sanitizing(su)
        su = apply_sanitizing_rules(su)
        if su in sanitized_urls:
            duplicates += 1
        else:
            sanitized_urls.append(su)
    return duplicates

