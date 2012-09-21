from mygpo.core.models import SanitizingRule
from mygpo.cache import cache_result


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
