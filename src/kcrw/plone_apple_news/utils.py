import json
from copy import deepcopy
from zope.component import queryUtility
from plone.registry.interfaces import IRegistry
from .interfaces import IAppleNewsSettings
from .templates import ARTICLE_BASE
from kcrw.plone_apple_news import _

SEP = _(u'list_separator', default=u',')
FINAL_SEP = _(u'final_list_seperator', default=u' and')


def get_settings():
    registry = queryUtility(IRegistry)
    if registry is not None:
        return registry.forInterface(
            IAppleNewsSettings, prefix='kcrw.apple_news',
            check=False
        )
    return {}


def pretty_text_list(entries, context):
    if not entries:
        return u''
    if len(entries) == 1:
        return entries[0]

    sep = context.translate(SEP)
    final_sep = context.translate(FINAL_SEP)
    result = u''
    last = len(entries) - 1
    for i, e in enumerate(entries):
        if i != 0:
            result += (sep if i != last else final_sep)
            result += u' '
        result += e
    return result


def mergedicts(dict1, dict2):
    for k in set(dict1.keys()).union(dict2.keys()):
        if k in dict1 and k in dict2:
            if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
                yield (k, dict(mergedicts(dict1[k], dict2[k])))
            elif dict2[k] is not None:
                yield (k, dict2[k])
        elif k in dict1 and dict1[k] is not None:
            yield (k, dict1[k])
        elif dict2[k] is not None:
            yield (k, dict2[k])


def article_base():
    settings = get_settings()
    custom = getattr(settings, 'article_customizations', None)
    base = deepcopy(ARTICLE_BASE)
    if custom and custom.strip():
        custom = json.loads(custom)
        return dict(mergedicts(base, custom))
    return base
