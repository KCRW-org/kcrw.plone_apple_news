# -*- coding: utf-8 -*-
from OFS.SimpleItem import SimpleItem
from plone.app.contentrules import PloneMessageFactory as _
from plone.app.contentrules.browser.formhelper import NullAddForm
from plone.contentrules.rule.interfaces import IExecutable
from plone.contentrules.rule.interfaces import IRuleElementData
from Products.CMFPlone import utils
from Products.statusmessages.interfaces import IStatusMessage
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from ..interfaces import IAppleNewsActions


class IAppleNewsDeleteAction(Interface):
    """Interface for the configurable aspects of a delete action.
    """


@implementer(IAppleNewsDeleteAction, IRuleElementData)
class DeleteAction(SimpleItem):
    """The actual persistent implementation of the action element.
    """

    element = 'kcrw.apple_news_actions.delete'
    summary = _(u'Delete Apple News Article')


@adapter(Interface, IAppleNewsDeleteAction, Interface)
@implementer(IExecutable)
class DeleteActionExecutor(object):
    """The executor for this action.
    """

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        obj = self.event.object
        adapter = IAppleNewsActions(obj, alternate=None)
        if adapter is not None:
            if not adapter.data.get('id'):
                return False
            adapter.delete_article()
            return True
        return False

    def error(self, obj, error):
        request = getattr(self.context, 'REQUEST', None)
        if request is not None:
            title = utils.pretty_title_or_id(obj, obj)
            message = _(u"Unable to delete Apple News article for ${name} as part of content rule: ${error}",  # noqa
                          mapping={'name': title, 'error': error})
            IStatusMessage(request).addStatusMessage(message, type='error')


class DeleteAddForm(NullAddForm):
    """A degenerate "add form" for delete actions.
    """

    def create(self):
        return DeleteAction()
