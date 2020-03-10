ARTICLE_BASE = {
    "version": "1.7",
    "layout": {
        "columns": 12,
        "width": 1280,
        "margin": 120,
        "gutter": 20,
    },
    "components": [],
    "documentStyle": {
        "backgroundColor": "#fbfbfd",
    },
    "textStyles": {
        "class-style-discreet": {
            "textColor": "#86868b",
            "fontSize": 14,
        }
    },
    "componentTextStyles": {
        "default": {
            "fontName": "Helvetica",
            "fontSize": 18,
            "lineHeight": 25,
            "linkStyle": {
                "textColor": "#1d1d1f",
            },
        },
        "default-title": {
            "fontSize": 45,
            "lineHeight": 48,
            "fontWeight": "bold",
            "hyphenation": False,
        },
        "default-intro": {
            "fontSize": 20,
        },
        "default-byline": {
            "fontSize": 14,
            "hyphenation": False,
            "textColor": "#86868b",
        },
        "default-body": {
            "hyphenation": True,
        },
        "default-caption": {
            "fontName": "Verdana",
            "fontSize": 14,
            "textAlignment": "center",
            "textColor": "#86868b",
        },
        "body-container": {},
        "body-section-first": {},
        "body-section-last": {},
    },
    "componentStyles": {
        "headerStyle": {},
        "titleStyle": {},
        "subheadStyle": {},
        "bylineStyle": {},
        "leadPhotoContainerStyle": {},
        "leadPhotoStyle": {},
        "leadPhotoCaptionStyle": {},
        "bodyStyle": {},
        "bodyPhotoStyle": {},
        "bodyPhotoInsetStyle": {},
        "bodyPhotoContainerStyle": {},
        "captionStyle": {},
        "bodyImageStyle": {},
        "bodyVideoEmbedStyle": {}
    },
    "componentLayouts": {
        "headerLayout": {
            "margin": {
                "top": 20,
                "bottom": 20,
            },
        },
        "titleLayout": {},
        "subheadLayout": {
            "margin": {
                "top": 5,
            }
        },
        "bylineLayout": {},
        "leadPhotoContainer": {
            "ignoreViewportPadding": True,
            "ignoreDocumentMargin": True,
            "margin": {
                "bottom": 10,
            },
        },
        "leadPhoto": {
            "ignoreViewportPadding": True,
            "ignoreDocumentMargin": True,
        },
        "leadPhotoCaptionLayout": {
            "ignoreViewportPadding": True,
            "ignoreDocumentMargin": True,
            "padding": {
                "top": 2,
                "bottom": 2,
            },
        },
        "bodyLayout": {
            "margin": {
                "top": 20,
                "bottom": 40,
            },
        },
        "imageLeft": {
            "columnSpan": 4,
            "padding": {
                "top": 10,
                "right": 5,
                "bottom": 10,
            },
        },
        "imageRight": {
            "columnStart": 8,
            "padding": {
                "top": 10,
                "bottom": 10,
                "left": 5,
            },
        },
        "bodyPhoto": {
            "columnStart": 1,
            "columnSpan": 10,
            "padding": {
                "top": 40,
                "bottom": 40,
            },
        },
        "captionLayout": {
            "padding": {
                "top": 2,
                "bottom": 2,
            },
        },
        "bodyImage": {},
        "bodyVideoEmbed": {
            "margin": {
                "bottom": 60,
            }
        },
    },
    "metadata": {
        "generatorName": "Plone Apple News",
        "generatorVersion": "0.1.0",
    },
}

METADATA_BASE = {
    "data": {
        "isPreview": True,
        "maturityRating": None,
    },
}

ALLOWED_HTML_TAGS = [
    'p', 'br', 'ul', 'ol', 'li', 'blockquote',
    'a', 'strong', 'b', 'em', 'i', 'sup', 'sub', 'del', 's',
    'pre', 'code', 'samp',
    'footer', 'aside', 'span', 'div',
]

ALLOWED_HTML_ATTRS = [
    'id', 'href', 'data-anf-textstyle',
]
