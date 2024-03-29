import six
import transaction
from copy import deepcopy
from Acquisition import aq_base
from DateTime import DateTime
from zope.annotation.interfaces import IAnnotations
from zope.component import adapter, queryUtility
from zope.interface import implementer
from plone.api import user
from plone.indexer import indexer
from plone.scale.scale import scaleImage
from plone.i18n.normalizer.interfaces import IFileNameNormalizer
try:
    from Products.Archetypes.interfaces import IBaseContent
except ImportError:
    IBaseContent = None
from OFS.Image import Pdata
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

META_FIELDS = set((
    'isCandidateToBeFeatured',
    'isHidden',
    'isPreview',
    'isSponsored',
    'links',
    'maturityRating',
    'targetTerritoryCountryCodes',
))


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

    def update_from_apple(self, article_data):
        IAnnotations(self.context)[self.annotations_key] = {
            'id': article_data['data'].get('id'),
            'revision': article_data['data'].get('revision'),
            'metadata': self.extract_metadata(article_data),
        }

    def make_api_request(self, method, *args):
        """We commit a transaction before making the _slow_ API request,
        start a new transaction after, and commit after updating internal data.
        Ideally this would be done via some async processing, which could be handled
        via a custom adapter."""
        transaction.commit()
        article_data = method(*args)
        transaction.abort()
        transaction.begin()
        self.update_from_apple(article_data)
        transaction.commit()
        transaction.begin()
        return article_data

    def extract_metadata(self, article_data):
        data = article_data.get('data', {})
        meta = {k: data[k] for k in META_FIELDS if k in data}
        if 'links' in meta and 'self' in meta['links']:
            del meta['links']['self']
        return meta

    def create_article(self):
        if self.data:
            self.context.reindexObject(idxs=['has_apple_news'])
            raise AppleNewsError('Article already published', code=418)
        adapter = self.article
        article = adapter.article_data()
        metadata = adapter.article_metadata()
        assets = adapter.article_assets()
        article_data = self.make_api_request(
            self.api.create_article,
            article, metadata, assets
        )
        self.context.reindexObject(idxs=['has_apple_news'])
        return article_data

    def update_article(self):
        if not self.data:
            raise AppleNewsError('Article not yet published', code=418)
        adapter = self.article
        article = adapter.article_data()
        metadata = adapter.article_metadata()
        assets = adapter.article_assets()
        if not metadata:
            metadata = {'data': {}}

        # Update metadata with stored data from Apple News
        self.refresh_revision()
        metadata['data'].update(self.data.get('metadata', {}))

        metadata['data']['revision'] = self.data['revision']
        # Publish updates
        article_data = self.make_api_request(
            self.api.update_article,
            self.data['id'], metadata, article, assets
        )
        return article_data

    def update_metadata(self, additional_data=None):
        if not self.data:
            raise AppleNewsError('Article not yet published', code=418)
        adapter = self.article
        article = adapter.article_data()
        article_meta = {'metadata': article.get('metadata', {})}
        metadata = adapter.article_metadata()
        if not metadata:
            metadata = {'data': {}}

        # Update metadata with stored data from Apple News
        self.refresh_revision()
        metadata['data'].update(self.data.get('metadata', {}))

        metadata['data']['revision'] = self.data['revision']
        if additional_data:
            metadata = dict(mergedicts(metadata, additional_data))
        article_data = self.make_api_request(
            self.api.update_article,
            self.data['id'], metadata, article_meta
        )
        return article_data

    def delete_article(self):
        """Publishes a new Apple News Article"""
        if not self.data:
            raise AppleNewsError('Article not yet published', code=418)
        try:
            self.api.delete_article(self.data['id'])
        except AppleNewsError as e:
            # In case of 404 delete annotation key
            if e.code == 404:
                del IAnnotations(self.context)[self.annotations_key]
                self.context.reindexObject(idxs=['has_apple_news'])
            raise
        del IAnnotations(self.context)[self.annotations_key]
        self.context.reindexObject(idxs=['has_apple_news'])

    def refresh_revision(self):
        """Retrieves info about existing Apple News Article"""
        if not self.data:
            raise AppleNewsError('Article not yet published', code=418)
        article_data = self.api.read_article(self.data['id'])
        self.update_from_apple(article_data)


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
    footer = None

    def __init__(self, context):
        self.context = context
        self.assets = {}
        settings = get_settings()
        if settings:
            self.primary_scale = getattr(settings, 'primary_scale', u'large')
            self.body_scale = getattr(settings, 'body_scale', u'large')
            if getattr(settings, 'thumb_scale', None):
                self.thumb_scale = settings.thumb_scale
            if getattr(settings, 'footer_html', None):
                self.footer = settings.footer_html.strip()

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
            meta['thumbnailURL'] = u'bundle://{}'.format(thumb_name)

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
                    ctype = image.getContentType()
                    ext = CONTENT_TYPE_MAP.get(ctype, '')
                    if not fname.lower().endswith(ext) and not fname.lower().endswith('.jpeg'):
                        fname += ext
                    normalizer = queryUtility(IFileNameNormalizer)
                    if normalizer is not None:
                        fname = normalizer.normalize(safe_unicode(fname))
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
            ctype = getattr(image, 'contentType', None)
            ext = CONTENT_TYPE_MAP.get(ctype, '')
            if ext not in fname.lower():
                fname += ext
            normalizer = queryUtility(IFileNameNormalizer)
            if normalizer is not None:
                fname = normalizer.normalize(safe_unicode(fname))
            return fname

    @staticmethod
    def get_image_data(context, name):
        # Archetypes Support
        if IBaseContent is not None and IBaseContent.providedBy(context):
            field = context.getField(name)
            if field is not None:
                image = field.get(context)
                if image is not None:
                    data = getattr(aq_base(image), 'data', None)
                if isinstance(data, Pdata):
                    return str(data)
                return data
        # Otherwise attribute lookup
        has_image = getattr(
            aq_base(context), name, None
        ) is not None
        if has_image:
            image = getattr(context, name)
            try:
                return image.open()
            except AttributeError:
                return getattr(aq_base(image), 'data', image)

    def populate_image(self, context, name, scale_name):
        filename = self.get_image_filename(context, name)
        if filename is not None:
            if scale_name:
                filename = u'{}-{}'.format(scale_name, safe_unicode(filename))
            if filename not in self.assets:
                scale_view = context.unrestrictedTraverse('@@images')
                scales = scale_view.getAvailableSizes()
                if scale_name not in scales:
                    return
                width, height = scales.get(scale_name)
                data = self.get_image_data(context, name)
                if not data or not width or not height:
                    return
                try:
                    result = scaleImage(data, direction="thumbnail",
                                        width=width, height=height,
                                        allow_webp=False)
                except TypeError:
                    result = scaleImage(data, direction="thumbnail",
                                        width=width, height=height)
                if result is not None:
                    data, format_, dimensions = result
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
            return self.html_to_components(text)

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
                "URL": u"bundle://{}".format(img_name),
                "layout": "leadPhoto",
                "style": "leadPhotoStyle",
            }
            caption = self.get_primary_caption()
            if caption:
                image["caption"] = {
                    "text": caption,
                    "format": "html",
                }
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
        footer = self.footer_component()
        if footer:
            components.append(footer)
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
                        'URL': u'bundle://{}'.format(filename),
                    }
            classes = set(img['classes'])
            if 'captioned' in classes and img['description']:
                component['caption'] = {
                    "text": img['description'],
                    "format": "html",
                }
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

    def html_to_components(self, html, part_name='body'):
        components = []
        parts = process_html(html, self.context, part_name)
        total = len(parts)
        for i, part in enumerate(parts):
            if isinstance(part, six.string_types):
                components.append({
                    "role": "body",
                    "format": "html",
                    "textStyle": '{}-section'.format(part_name),
                    "text": part,
                })
                if i == 0:
                    components[-1]['textStyle'] = '{}-section-first'.format(part_name)
                if i == total + 1:
                    components[-1]['textStyle'] = '{}-section-last'.format(part_name)
                continue
            rendered_part = self.process_part(part)
            if rendered_part:
                components.extend(rendered_part)
        return components

    def body_component(self):
        """Splits HTML text into components separated by photo objects.
           Adds internal images as assets. Resolves UID links. Removes
           HTML not allowed by Apple News."""
        components = self.get_body_parts() or []
        section = {
            "role": "container",
            "textStyle": "body-container",
            "layout": "bodyLayout",
            "style": "bodyStyle",
            "components": components
        }
        if components:
            return section

    def footer_component(self):
        component = {}
        if self.footer:
            components = self.html_to_components(self.footer, 'footer')
            if len(components):
                component = {
                    "role": "aside",
                    "layout": "footerLayout",
                    "style": "footerStyle",
                    "components": components,
                }
        return component


@indexer(IAppleNewsSupport)
def has_apple_news(obj):
    adapter = IAppleNewsActions(obj)
    return bool(adapter.data.get('id'))
