import pprint
from plone.app.registry.browser import controlpanel
from Products.CMFPlone.log import log_exc
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from kcrw.apple_news import API, AppleNewsError

from ..interfaces import IAppleNewsSettings
from kcrw.plone_apple_news import _


class AppleNewsSettingsForm(controlpanel.RegistryEditForm):
    schema = IAppleNewsSettings
    label = _(u"Apple News Settings")
    description = _(u"")
    enableCSRFProtection = True
    channel_info = None
    schema_prefix = 'kcrw.apple_news'

    def update(self):
        super(AppleNewsSettingsForm, self).update()
        settings = self.getContent()
        if settings and getattr(settings, 'api_key_id', None):
            api = API(settings.api_key_id, settings.api_key_secret,
                      settings.channel_id)
            try:
                self.channel_info = api.read_channel()
            except AppleNewsError:
                log_exc('Error on Apple News channel request')
                IStatusMessage(self.request).addStatusMessage(
                    _(u"Error retrieving Apple News channel info. "
                      u"See log for details."),
                    "error"
                )


class AppleNewsSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = AppleNewsSettingsForm
    index = ViewPageTemplateFile('templates/control_panel.pt')

    def pprint(self, obj):
        return pprint.pformat(obj)
