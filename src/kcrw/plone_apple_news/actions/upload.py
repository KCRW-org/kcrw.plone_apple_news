from OFS.SimpleItem import SimpleItem
from zope import schema
from plone.app.contentrules import PloneMessageFactory as _
from plone.app.contentrules.actions import ActionAddForm
from plone.app.contentrules.actions import ActionEditForm
from plone.app.contentrules.browser.formhelper import ContentRuleFormWrapper
from plone.contentrules.rule.interfaces import IExecutable
from plone.contentrules.rule.interfaces import IRuleElementData
from Products.CMFPlone import utils
from Products.statusmessages.interfaces import IStatusMessage
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from ..interfaces import IAppleNewsActions


class IAppleNewsUploadAction(Interface):
    """Interface for the configurable aspects of an upload action.
    """

    force_updates = schema.Bool(
        title=_(u'Force Update'),
        description=_(u'Force updates even if the Article has changed on Apple News.'),
        required=False,
        default=False,
    )


@implementer(IAppleNewsUploadAction, IRuleElementData)
class UploadAction(SimpleItem):
    """The actual persistent implementation of the action element.
    """

    element = 'kcrw.apple_news_actions.upload'
    summary = _(u'Create or Update Apple News Article')


@adapter(Interface, IAppleNewsUploadAction, Interface)
@implementer(IExecutable)
class UploadActionExecutor(object):
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
            if adapter.data.get('id'):
                if self.element.force_updates:
                    adapter.refresh_revision()
                adapter.update_article()
            else:
                adapter.create_article()
            return True
        return False

    def error(self, obj, error):
        request = getattr(self.context, 'REQUEST', None)
        if request is not None:
            title = utils.pretty_title_or_id(obj, obj)
            message = _(u"Unable to upload Apple News article for ${name} as part of content rule: ${error}",  # noqa
                          mapping={'name': title, 'error': error})
            IStatusMessage(request).addStatusMessage(message, type='error')


class UploadAddForm(ActionAddForm):
    """An add form for apple news upload actions.
    """
    schema = IAppleNewsUploadAction
    label = _(u'Add Apple News Upload Action')
    description = _(u'This action creates or updates an Apple News Article '
                    u'from a content object.')
    Type = UploadAction


class UploadAddFormView(ContentRuleFormWrapper):
    form = UploadAddForm


class UploadEditForm(ActionEditForm):
    """An edit form for apple news upload rule action.

    z3c.form does all the magic here.
    """
    schema = IAppleNewsUploadAction
    label = _(u'Edit Apple News Upload Action')
    description = _(u'This action creates or updates an Apple News Article '
                    u'from a content object.')
    form_name = _(u'Configure action')


class UploadEditFormView(ContentRuleFormWrapper):
    form = UploadEditForm
