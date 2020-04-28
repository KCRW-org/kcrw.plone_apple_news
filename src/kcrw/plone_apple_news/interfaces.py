# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

import json
from zope.interface import Attribute
from zope.interface import Interface
from zope.interface import Invalid
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope import schema
from kcrw.plone_apple_news import _


def json_constraint(value):
    try:
        json.loads(value)
    except Exception as e:
        raise Invalid('Invalid JSON: {}'.format(str(e)))
    return True


class IKcrwPloneAppleNewsLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IAppleNewsSupport(Interface):
    """Interface for Apple News Behavior"""


class IAppleNewsSettings(Interface):
    """Control Panel Settings Interface"""

    api_key_id = schema.TextLine(
        title=_(u'Apple News API Key Id')
    )
    api_key_secret = schema.TextLine(
        title=_(u'Apple News API Key Secret')
    )
    channel_id = schema.TextLine(
        title=_(u'Apple News Channel Id')
    )
    canonical_url = schema.URI(
        title=_(u'Canonical Site URL'),
        description=_(u'Enter the canonical URL for this website, '
                      u'if it differs from the CMS editing url.'),
        required=False
    )
    primary_scale = schema.Choice(
        title=_(u'Primary Image Scale'),
        description=_(u'Image scale to use for primary Apple News image.'),
        vocabulary=u'plone.app.vocabularies.ImagesScales',
        default=u'large',
        required=False
    )
    body_scale = schema.Choice(
        title=_(u'Body Image Scale'),
        description=_(u'Image scale to use for images in text body.'),
        vocabulary=u'plone.app.vocabularies.ImagesScales',
        default=u'large',
        required=True
    )
    thumb_scale = schema.Choice(
        title=_(u'Thumbnail Scale'),
        description=_(u'Image scale to use for Apple News thumbnail.'),
        vocabulary=u'plone.app.vocabularies.ImagesScales',
        default=u'preview',
        required=True
    )
    footer_html = schema.Text(
        title=_(u'Footer HTML'),
        description=_(u'Optional custom HTML for article footers'),
        required=False
    )
    article_customizations = schema.Text(
        title=_(u'Custom Article JSON'),
        description=_(u'Customized Article JSON for e.g. style and layout.'
                      u'Will be merged with default.'),
        constraint=json_constraint,
        required=False
    )


class IAppleNewsActions(Interface):
    """Apple News Integration Actions"""

    data = Attribute("Stored article data")

    def create_article():
        """Publishes a new Apple News Article"""

    def update_article():
        """Publishes a new Apple News Article"""

    def update_metadata(additional_data=None):
        """Publishes a new Apple News Article"""

    def delete_article():
        """Publishes a new Apple News Article"""

    def refresh_revision():
        """Sync revision metadata"""


class IAppleNewsGenerator(Interface):
    """Apple News Integration Actions"""

    def article_data():
        """Gets JSON formatted article data"""

    def article_metadata():
        """Gets JSON formatted article metadata"""

    def article_assets():
        """Gets a dictionary of file assets for the article"""
