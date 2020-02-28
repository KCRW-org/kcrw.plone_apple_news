import json
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
from ..interfaces import json_constraint


class IAppleNewsMetadataAction(Interface):
    """Interface for the configurable aspects of a metadata update action.
    """

    metadata = schema.Text(
        title=_(u'JSON Metadata'),
        description=_(u'JSON formatted Apple News metadata for '
                      u'updating the Article. Default value attempts'
                      u'to make the article public.'),
        required=True,
        constraint=json_constraint,
        default=u'''{
            "data": {"isPreview": false}
        }'''
    )

    force_updates = schema.Bool(
        title=_(u'Force Update'),
        description=_(u'Force updates even if the Article has changed on Apple News.'),
        required=False,
        default=False,
    )


@implementer(IAppleNewsMetadataAction, IRuleElementData)
class MetadataAction(SimpleItem):
    """The actual persistent implementation of the action element.
    """

    element = 'kcrw.apple_news_actions.metadata'
    summary = _(u'Update Apple News Article Metatata, '
                u'e.g. to make an article public')


@adapter(Interface, IAppleNewsMetadataAction, Interface)
@implementer(IExecutable)
class MetadataActionExecutor(object):
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
                json_data = json.loads(self.element.metadata)
                adapter.update_metdata(json_data)
                return True
        return False

    def error(self, obj, error):
        request = getattr(self.context, 'REQUEST', None)
        if request is not None:
            title = utils.pretty_title_or_id(obj, obj)
            message = _(u"Unable to update Apple News article metadata for ${name} as part of content rule: ${error}",  # noqa
                          mapping={'name': title, 'error': error})
            IStatusMessage(request).addStatusMessage(message, type='error')


class MetadataAddForm(ActionAddForm):
    """An add form for Apple News metadata update actions.
    """
    schema = IAppleNewsMetadataAction
    label = _(u'Add Apple News Metadata Action')
    description = _(u'This action will make updates to '
                    u'Apple News Article metadata.')
    Type = MetadataAction


class MetadataAddFormView(ContentRuleFormWrapper):
    form = MetadataAddForm


class MetadataEditForm(ActionEditForm):
    """An edit form for Apple News metadata update rule actions.

    z3c.form does all the magic here.
    """
    schema = IAppleNewsMetadataAction
    label = _(u'Edit Apple News Metadata Action')
    description = _(u'This action will make updates to '
                    u'Apple News Article metadata.')
    form_name = _(u'Configure action')


class MetadataEditFormView(ContentRuleFormWrapper):
    form = MetadataEditForm
