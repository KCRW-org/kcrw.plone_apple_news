from plone.app.contentrules.actions import ActionAddForm
from plone.app.contentrules.actions import ActionEditForm
from plone.app.contentrules.browser.formhelper import ContentRuleFormWrapper
from .metadata import IAppleNewsMetadataAction
from .metadata import MetadataAction
from .upload import IAppleNewsUploadAction
from .upload import UploadAction
from .. import _


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
