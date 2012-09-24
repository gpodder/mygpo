from mygpo.core.models import SanitizingRule
from mygpo.cache import cache_result
from mygpo.couch import get_main_database
from mygpo.db.couchdb.utils import multi_request_view


class SanitizingRuleStub(object):
    pass


@cache_result(timeout=60*60)
def sanitizingrules_by_obj_type(obj_type):
    r = SanitizingRule.view('sanitizing_rules/by_target',
            include_docs = True,
            startkey     = [obj_type, None],
            endkey       = [obj_type, {}],
        )

    for rule in r:
        obj = SanitizingRuleStub()
        obj.slug = rule.slug
        obj.applies_to = list(rule.applies_to)
        obj.search = rule.search
        obj.replace = rule.replace
        obj.priority = rule.priority
        obj.description = rule.description
        yield obj


@cache_result(timeout=60*60)
def sanitizingrule_for_slug(slug):
    r = SanitizingRule.view('sanitizing_rules/by_slug',
            include_docs=True,
            key=slug,
        )

    return r.one() if r else None


def missing_slug_count(doc_type, start, end):
    db = get_main_database()
    res = db.view('slugs/missing',
            startkey     = [doc_type] + end,
            endkey       = [doc_type] + start,
            descending   = True,
            reduce       = True,
            group        = True,
            group_level  = 1,
        )
    return res.first()['value'] if res else 0


def missing_slugs(doc_type, start, end, wrapper, **kwargs):

    db = get_main_database()
    return multi_request_view(db, 'slugs/missing',
            startkey     = [doc_type] + end,
            endkey       = [doc_type] + start,
            descending   = True,
            include_docs = True,
            reduce       = False,
            wrapper      = wrapper,
            auto_advance = False,
            **kwargs
        )
