import json
import six
import zipfile
from AccessControl import ClassSecurityInfo, Unauthorized
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
from plone.batching import Batch
from plone.protect import CheckAuthenticator
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.log import log
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from zExceptions import NotFound
from ..interfaces import IAppleNewsActions
from ..interfaces import IAppleNewsGenerator
from kcrw.apple_news import AppleNewsError
from kcrw.plone_apple_news import _


@implementer(IPublishTraverse)
class AppleNewsActions(BrowserView):
    """Provides actions for Apple News API integration"""
    security = ClassSecurityInfo()

    def get_adapter(self):
        return IAppleNewsActions(self.context, alternate=None)

    def redirect(self):
        self.request.response.redirect(self.context.absolute_url())
        return ''

    def is_published(self):
        try:
            adapter = self.get_adapter()
            if adapter is not None:
                return adapter.data.get('id') is not None
        except Exception:
            return False

    security.declarePublic('can_create')
    def can_create(self):
        return not self.is_published()

    security.declarePublic('can_delete')
    def can_delete(self):
        return self.is_published()

    security.declarePublic('can_update')
    def can_update(self):
        return self.is_published()

    def create_article(self):
        """Create a new Article in Apple News"""
        CheckAuthenticator(self.request)
        if not _checkPermission('Apple News: Manage News Content',
                                self.context):
            raise Unauthorized
        adapter = self.get_adapter()
        article_data = adapter.create_article()
        IStatusMessage(self.request).addStatusMessage(
            _(u"Added new article with id: {}".format(article_data['data']['id'])),
            "info"
        )

    def update_article(self):
        """Update an Article in Apple News"""
        CheckAuthenticator(self.request)
        if not _checkPermission('Apple News: Manage News Content',
                                self.context):
            raise Unauthorized
        adapter = self.get_adapter()
        try:
            adapter.update_article()
        except AppleNewsError as e:
            log('Handled Apple News Error {}: {}'.format(e, e.data))
            if e.code == 409:
                message = _(
                    u'Unable to update article ({}) because'.format(
                        adapter.data['id']
                    ) + u'it has conflicting changes. Retry again to refresh.'
                )
            else:
                message = _(
                    u'Error {} updating article ({}).'.format(
                        e.code, adapter.data['id']
                    ) + u'See logs for more details.'
                )
            IStatusMessage(self.request).addStatusMessage(message, "error")
        else:
            IStatusMessage(self.request).addStatusMessage(
                _(u"Updated article with id: {}".format(adapter.data['id'])),
                "info"
            )

    def delete_article(self):
        """Delete an Article from Apple News"""
        adapter = self.get_adapter()
        article_id = adapter.data['id']
        try:
            adapter.delete_article()
        except AppleNewsError as e:
            log('Handled Apple News Error {}: {}'.format(e, e.data))
            if e.code == 404:
                message = _(
                    u'Article was already deleted ({}). Clearing Id.'.format(
                        article_id
                    )
                )
                IStatusMessage(self.request).addStatusMessage(message, "warning")
            else:
                message = _(
                    u'Error {} deleting article ({}).'.format(
                        e.code, article_id
                    ) + u'See logs for more details.'
                )
                IStatusMessage(self.request).addStatusMessage(message, "error")
        else:
            IStatusMessage(self.request).addStatusMessage(
                _(u"Deleted article with id: {}".format(article_id)),
                "info"
            )

    def export_article(self):
        generator = IAppleNewsGenerator(self.context)
        article = generator.article_data()
        metadata = generator.article_metadata()
        assets = generator.article_assets()
        adapter = self.get_adapter()
        if adapter.data.get('revision'):
            metadata['data']['revision'] = adapter.data['revision']
        try:
            fh = six.BytesIO()  # This is not a context manager in PY2
            with zipfile.ZipFile(fh, mode="w",
                                 compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr('article.json',
                            json.dumps(article, indent=True).encode('utf8'))
                zf.writestr('metadata.json',
                            json.dumps(metadata, indent=True).encode('utf8'))
                for fname in assets:
                    zf.writestr(fname, assets[fname])

            resp = self.request.response
            resp.setHeader(
                'Content-Disposition', 'Attachment; filename="{}.zip"'.format(
                    self.context.getId()
                )
            )
            resp.setHeader('Content-Type', 'application/zip')
            fh.seek(0)
            return fh.read()
        finally:
            fh.close()

    def publishTraverse(self, request, name):
        self.req_method = name
        return self

    def __call__(self, *args, **kw):
        method_name = None
        if hasattr(self, 'req_method'):
            method_name = self.req_method

        if not method_name:
            return self

        CheckAuthenticator(self.request)
        if not _checkPermission('Apple News: Manage News Content',
                                self.context):
            raise Unauthorized
        if method_name:
            methods = {'create-article': self.create_article,
                       'update-article': self.update_article,
                       'delete-article': self.delete_article,
                       'export-article': self.export_article}
            if method_name in methods:
                value = methods[method_name]()
                if value is None:
                    return self.redirect()
                return value
            else:
                raise NotFound


class BulkAppleNewsForm(BrowserView):
    """Form for finding and updating Apple news articles in bulk"""
    template = ViewPageTemplateFile('templates/bulk_update.pt')
    batch = ()
    label = u'Bulk Update Apple News Articles'

    def update(self):
        uids = []
        request = self.request
        b_start = request.form.get('b_start', 0)
        catalog = getToolByName(self.context, 'portal_catalog')
        self.batch = Batch(
            catalog(has_apple_news=True, sort_on='Date', sort_order='descending'),
            start=b_start, size=50
        )
        if request.method.lower() == 'post':
            messages = []
            authenticator = getMultiAdapter(
                (self.context, request), name=u"authenticator"
            )
            if not authenticator.verify():
                raise Unauthorized
            uids = request.get('uids', [])
            if not uids:
                return
            count = 0
            brains = catalog(has_apple_news=True, UID=uids)
            for b in brains:
                obj = b.getObject()
                adapter = IAppleNewsActions(obj, alternate=None)
                if adapter is not None:
                    try:
                        adapter.update_article()
                        count += 1
                    except AppleNewsError as e:
                        log(u'Handled Apple News Error in bulk update '
                            u'{}: {}'.format(e, e.data))
                        if e.code == 409:
                            messages.append(
                                u'Unable to update article "{}" '.format(
                                    safe_unicode(b.Title)
                                ) + u'because there are conflicting changes '
                                u'in Apple News Publisher'
                            )
                        else:
                            messages.append(
                                u'Unable to update article "{}" '.format(
                                    safe_unicode(b.Title)
                                ) + u'check logs for details.'
                            )
            msg_adapter = IStatusMessage(self.request)
            msg_adapter.add(
                u'Updated {} Apple News article with {} errors'.format(
                    count, len(brains) - count
                ), type=u"info"
            )
            for msg in messages:
                msg_adapter.add(msg, type=u'error')

    def __call__(self):
        """Call update and render"""
        self.update()
        return self.template()
