from plone.app.contentrules.browser.formhelper import AddForm
from plone.app.contentrules.browser.formhelper import EditForm
from zope.formlib import form
from .metadata import IAppleNewsMetadataAction
from .metadata import MetadataAction
from .upload import IAppleNewsUploadAction
from .upload import UploadAction
from .. import _


class MetadataAddFormView(AddForm):
    """An add form for Apple News metadata update actions.
    """
    form_fields = form.FormFields(IAppleNewsMetadataAction)
    label = _(u'Add Apple News Metadata Action')
    description = _(u'This action will make updates to '
                    u'Apple News Article metadata.')
    form_name = _(u"Configure element")

    def create(self, data):
        a = MetadataAction()
        form.applyChanges(a, self.form_fields, data)
        return a


class MetadataEditFormView(EditForm):
    """An edit form for Apple News metadata update rule actions.

    z3c.form does all the magic here.
    """
    form_fields = form.FormFields(IAppleNewsMetadataAction)
    label = _(u'Edit Apple News Metadata Action')
    description = _(u'This action will make updates to '
                    u'Apple News Article metadata.')
    form_name = _(u'Configure action')


class UploadAddFormView(AddForm):
    """An add form for apple news upload actions.
    """
    form_fields = form.FormFields(IAppleNewsUploadAction)
    label = _(u'Add Apple News Upload Action')
    description = _(u'This action creates or updates an Apple News Article '
                    u'from a content object.')
    form_name = _(u"Configure element")

    def create(self, data):
        a = UploadAction()
        form.applyChanges(a, self.form_fields, data)
        return a


class UploadEditFormView(EditForm):
    """An edit form for apple news upload rule action.

    z3c.form does all the magic here.
    """
    form_fields = form.FormFields(IAppleNewsUploadAction)
    label = _(u'Edit Apple News Upload Action')
    description = _(u'This action creates or updates an Apple News Article '
                    u'from a content object.')
    form_name = _(u'Configure action')
