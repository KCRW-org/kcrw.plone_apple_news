import six
from copy import deepcopy
from Acquisition import aq_base
from DateTime import DateTime
from zope.annotation.interfaces import IAnnotations
from zope.component import adapter
from zope.interface import implementer
from plone.api import user
try:
    from Products.Archetypes.interfaces import IBaseContent
except ImportError:
    IBaseContent = None
from Products.CMFCore.interfaces import IDublinCore
from Products.CMFPlone.utils import safe_unicode
from kcrw.apple_news import API, AppleNewsError
from .interfaces import IAppleNewsActions
from .interfaces import IAppleNewsSupport
from .interfaces import IAppleNewsGenerator
from .templates import METADATA_BASE
from .html import obj_url
from .html import process_html
from .utils import article_base
from .utils import get_settings
from .utils import mergedicts
from .utils import pretty_text_list


CONTENT_TYPE_MAP = {
    'image/png': '.png',
    'image/jpeg': '.jpg',
    'image/gif': '.gif',
    'image/tiff': '.tif',
}


@adapter(IAppleNewsSupport)
@implementer(IAppleNewsActions)
class AppleNewsActions(object):
    """Provides actions for apple news integration"""
    annotations_key = 'kcrw.apple_news_info'
    api = settings = article_adapter = None

    def __init__(self, context):
        self.context = context
        self.article = IAppleNewsGenerator(context, alternate=None)
        settings = self.settings = get_settings()
        if settings and getattr(settings, 'api_key_id', None):
            self.api = API(settings.api_key_id, settings.api_key_secret,
                           settings.channel_id)
        else:
            raise AppleNewsError('API settings not set.')

    @property
    def data(self):
        return IAnnotations(self.context).get(self.annotations_key, {})

    def update_revision(self, article_data):
        IAnnotations(self.context)[self.annotations_key] = {
            'id': article_data['data'].get('id'),
            'revision': article_data['data'].get('revision')
        }

    def create_article(self):
        if self.data:
            raise AppleNewsError('Article already published')
        adapter = self.article
        article = adapter.article_data()
        metadata = adapter.article_metadata()
        assets = adapter.article_assets()
        article_data = self.api.create_article(article, metadata, assets)
        self.update_revision(article_data)
        return article_data

    def update_article(self):
        if not self.data:
            raise AppleNewsError('Article not yet published')
        adapter = self.article
        article = adapter.article_data()
        metadata = adapter.article_metadata()
        assets = adapter.article_assets()
        if not metadata:
            metadata = {'data': {}}
        metadata['data']['revision'] = self.data['revision']
        article_data = self.api.update_article(
            self.data['id'], metadata, article, assets
        )
        self.update_revision(article_data)
        return article_data

    def update_metadata(self, additional_data=None):
        if not self.data:
            raise AppleNewsError('Article not yet published')
        adapter = self.article
        article = adapter.article_data()
        article_meta = {'metadata': article.get('metadata', {})}
        metadata = adapter.article_metadata()
        if not metadata:
            metadata = {'data': {}}
        metadata['data']['revision'] = self.data['revision']
        if additional_data:
            metadata = dict(mergedicts(metadata, additional_data))
        article_data = self.api.update_article(
            self.data['id'], metadata, article_meta
        )
        self.update_revision(article_data)
        return article_data

    def delete_article(self):
        """Publishes a new Apple News Article"""
        if not self.data:
            raise AppleNewsError('Article not yet published')
        try:
            self.api.delete_article(self.data['id'])
        except AppleNewsError as e:
            # In case of 404 delete annotation key
            if e.code == 404:
                del IAnnotations(self.context)[self.annotations_key]
            raise
        del IAnnotations(self.context)[self.annotations_key]

    def refresh_revision(self):
        """Retrieves info about existing Apple News Article"""
        if not self.data:
            raise AppleNewsError('Article not yet published')
        article_data = self.api.read_article(self.data['id'])
        self.update_revision(article_data)


@adapter(IDublinCore)
@implementer(IAppleNewsGenerator)
class BaseAppleNewsGenerator(object):
    """Convert content into an Apple News article"""
    assets = None
    primary_text = 'text'
    image_name = 'image'
    primary_scale = None
    thumb_scale = 'medium'
    body_scale = 'large'

    def __init__(self, context):
        self.context = context
        self.assets = {}
        settings = get_settings()
        if settings:
            self.primary_scale = getattr(settings, 'primary_scale', u'large')
            self.body_scale = getattr(settings, 'body_scale', u'large')
            if getattr(settings, 'thumb_scale', None):
                self.thumb_scale = settings.thumb_scale

    def article_data(self):
        """Gets JSON formatted article data"""
        context = self.context
        article = article_base()
        article['identifier'] = self.get_identifier()
        article['title'] = self.get_title()
        article["language"] = self.context.Language() or u'en-US'
        article['components'].extend(self.article_components())
        meta = article["metadata"]
        authors = self.get_authors()
        if authors:
            meta["authors"] = authors
        meta["excerpt"] = safe_unicode(context.Description())
        meta["datePublished"] = self.date().ISO8601()
        meta["dateCreated"] = context.CreationDate()
        meta["dateModified"] = context.ModificationDate()
        meta["canonicalURL"] = obj_url(context)
        thumb_name = self.populate_image(context, self.image_name,
                                         self.thumb_scale)
        if thumb_name:
            meta['thumbnailURL'] = 'bundle://{}'.format(thumb_name)

        return article

    def article_metadata(self):
        """Gets JSON formatted article metadata"""
        return deepcopy(METADATA_BASE)

    def article_assets(self):
        """Gets a dictionary of file assets for the article"""
        return self.assets

    def get_title(self):
        return safe_unicode(self.context.Title())

    def get_subhead(self):
        return safe_unicode(self.context.Description())

    def get_identifier(self):
        return safe_unicode(self.context.getId())

    @staticmethod
    def get_image_filename(context, name):
        # Archetypes Support
        if IBaseContent is not None and IBaseContent.providedBy(context):
            field = context.getField(name)
            if field is not None:
                image = field.get(context)
                if image is not None:
                    fname = image.getFilename()
                    if not fname:
                        fname = context.getId()
                        if '.' not in fname:
                            ctype = image.getContentType()
                            ext = CONTENT_TYPE_MAP.get(ctype, '')
                            fname += ext
                    return fname
            return None
        # Otherwise attribute lookup
        has_image = getattr(
            aq_base(context), name, None
        ) is not None
        if has_image:
            image = getattr(context, name)
            fname = getattr(image, 'filename', None)
            if not fname:
                fname = context.getId()
                if '.' not in fname:
                    ctype = getattr(image, 'contentType', None)
                    ext = CONTENT_TYPE_MAP.get(ctype, '')
                    fname += ext
            return fname

    def populate_image(self, context, name, scale_name):
        filename = self.get_image_filename(context, name)
        if filename is not None:
            if scale_name:
                filename = '{}-{}'.format(scale_name, filename)
            if filename not in self.assets:
                scale_view = context.unrestrictedTraverse('@@images')
                scale = scale_view.scale(name, scale_name)
                if scale is not None:
                    data = scale.data
                    if not isinstance(data, six.string_types):
                        data = data.data
                    self.assets[filename] = data
                else:
                    filename = None
        return filename

    def get_primary_caption(self):
        context = self.context
        if IBaseContent is not None and IBaseContent.providedBy(context):
            field = context.getField('imageCaption')
            if field is not None:
                return safe_unicode(field.get(context))
            return None
        if getattr(aq_base(context), 'image_caption', None):
            return getattr(context, 'image_caption')

    def get_authors(self):
        results = []
        creators = self.context.listCreators()
        if not creators:
            creators = [self.context.getOwner()]
        for creator in creators:
            user_info = user.get(creator)
            if user_info is not None:
                results.append(safe_unicode(
                    user_info.getProperty('fullname', None) or creator
                ))
            else:
                results.append(safe_unicode(creator))
        return results

    def date(self):
        context = self.context
        date = context.EffectiveDate()
        if not date or date == 'None':
            date = context.Date()
        if date and date != 'None':
            return DateTime(date)

    def get_byline(self):
        context = self.context
        byline = u''
        authors = pretty_text_list(self.get_authors(), context)
        if authors:
            byline = u'by {}'.format(authors)
        date = self.date()
        if date:
            date = safe_unicode(
                date.strftime('%A %B %d, %Y %I:%H') +
                date.strftime('%p').lower()
            )
            if byline:
                byline += u' \uFF5c '
            byline += date

        return byline

    def get_body_parts(self):
        text = None
        context = self.context
        text_field = self.primary_text
        if IBaseContent is not None and IBaseContent.providedBy(context):
            field = context.getField(text_field)
            if field is not None:
                text = safe_unicode(field.get(context))
        elif getattr(aq_base(context), text_field, None):
            text = getattr(context, text_field).raw

        if text:
            return process_html(text, self.context)

    def article_components(self):
        components = [{
            "role": "header",
            "layout": "headerLayout",
            "style": "headerStyle",
            "components": [],
        }]
        header = components[-1]['components']
        header.append({
            "role": "title",
            "text": self.get_title(),
            "layout": "titleLayout",
            "style": "titleStyle",
        })
        sub_head = self.get_subhead()
        if sub_head:
            header.append({
                "role": "intro",
                "text": sub_head,
                "layout": "subheadLayout",
                "style": "subheadStyle",
            })
        byline = self.get_byline()
        if byline:
            header.append({
                "role": "byline",
                "text": byline,
                "format": "html",
                "layout": "bylineLayout",
                "style": "bylineStyle",
            })
        img_name = self.populate_image(self.context, self.image_name,
                                       self.primary_scale)
        if img_name:
            image = {
                "role": "photo",
                "URL": "bundle://{}".format(img_name),
                "layout": "leadPhoto",
                "style": "leadPhotoStyle",
            }
            caption = self.get_primary_caption()
            if caption:
                image["caption"] = caption
                image = {
                    "role": "container",
                    "layout": "leadPhotoContainer",
                    "style": "leadPhotoContainerStyle",
                    "components": [
                        image,
                        {"role": "caption",
                         "layout": "leadPhotoCaptionLayout",
                         "style": "leadPhotoCaptionStyle",
                         "format": "html",
                         "text": caption}
                    ]
                }
            components.append(image)

        body = self.body_component()
        if body:
            components.append(body)
        return components

    def process_part(self, part):
        if 'type' in part:
            method = getattr(self, 'process_' + part['type'], None)
            if method is not None:
                return method(part['contents'])
        elif 'role' in part:
            return [part]
        elif isinstance(part, list):
            return part

    def process_body_images(self, images):
        components = []
        for img in images:
            # We call external images "image" and internal "photo"
            component = {
                'role': 'image',
                'layout': 'bodyImage',
                'style': 'bodyImageStyle',
                'URL': img['src'],
            }
            if img['image']:
                filename = self.populate_image(
                    img['fullimage'], 'image', self.body_scale
                )
                if filename:
                    component = {
                        'role': 'photo',
                        "layout": "bodyPhoto",
                        "style": "bodyPhotoStyle",
                        'URL': 'bundle://{}'.format(filename),
                    }
            classes = set(img['classes'])
            if 'captioned' in classes and img['description']:
                component['caption'] = img['description']
                del component['layout']
                component = {
                    "role": "container",
                    "layout": "bodyPhoto",
                    "style": "bodyPhotoContainerStyle",
                    "components": [
                        component,
                        {"role": "caption",
                         "layout": "captionLayout",
                         "style": "captionStyle",
                         "format": "html",
                         "text": img['description']},
                    ],
                }

            if 'image-right' in classes or 'image-left' in classes:
                component['style'] = "bodyPhotoInsetStyle"
                if 'anchor' in img:
                    component['anchor'] = {
                        "target": img['anchor'],
                        "targetAnchorPosition": "top"
                    }
            if 'image-right' in classes:
                component['layout'] = "imageRight"
            elif 'image-left' in classes:
                component['layout'] = "imageLeft"
                if 'anchor' in img:
                    component['anchor'] = {
                        "target": img['anchor'],
                        "targetAnchorPosition": "top"
                    }
            else:
                component['layout'] = "bodyPhoto"
                component['style'] = "bodyPhotoStyle"

            components.append(component)

        return components

    def body_component(self):
        """Splits HTML text into components separated by photo objects.
           Adds internal images as assets. Resolves UID links. Removes
           HTML not allowed by Apple News."""
        components = []
        section = {
            "role": "container",
            "textStyle": "body-container",
            "layout": "bodyLayout",
            "style": "bodyStyle",
            "components": components
        }
        parts = self.get_body_parts() or []
        total = len(parts)
        for i, part in enumerate(parts):
            if isinstance(part, six.string_types):
                components.append({
                    "role": "body",
                    "format": "html",
                    "text": part
                })
                if i == 0:
                    components[-1]['textStyle'] = 'body-section-first'
                if i == total + 1:
                    components[-1]['textStyle'] = 'body-section-last'
                continue
            rendered_part = self.process_part(part)
            if rendered_part:
                components.extend(rendered_part)
            # We have an image scale
        if components:
            return section
