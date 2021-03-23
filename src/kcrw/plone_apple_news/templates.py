ARTICLE_BASE = {
    "version": "1.7",
    "layout": {
        "columns": 12,
        "width": 1280,
        "margin": 60,
        "gutter": 20,
    },
    "components": [],
    "documentStyle": {
        "backgroundColor": "#FFFFFF",
    },
    "textStyles": {
        "class-style-discreet": {
            "textColor": "#86868B",
            "fontSize": 14,
        },
        "style-underline": {
            "underline": True,
        },
    },
    "componentTextStyles": {
        "default": {
            "fontName": "Helvetica",
            "fontSize": 18,
            "lineHeight": 25,
            "linkStyle": {
                "textColor": "#1D1D1F",
            },
        },
        "default-title": {
            "fontSize": 45,
            "lineHeight": 48,
            "fontName": "Verdana-Bold",
            "hyphenation": False,
        },
        "default-intro": {
            "fontSize": 20,
        },
        "default-byline": {
            "fontSize": 14,
            "hyphenation": False,
            "textColor": "#86868B",
        },
        "default-body": {
            "hyphenation": True,
            "paragraphSpacingAfter": 18,
            "paragraphSpacingBefore": 18,
        },
        "default-caption": {
            "fontSize": 14,
            "textAlignment": "center",
            "textColor": "#86868B",
        },
        "body-container": {},
        "body-section": {},
        "body-section-first": {},
        "body-section-last": {},
        "footer-section": {},
        "footer-section-first": {},
        "footer-section-last": {},
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
        "bodyVideoEmbedStyle": {},
        "footerStyle": {},
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
            "margin": {
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
            "columnStart": 0,
            "columnSpan": 4,
            "padding": {
                "top": 0,
                "right": 5,
                "bottom": 10,
                "left": 0,
            },
        },
        "imageRight": {
            "columnStart": 8,
            "columnSpan": 4,
            "padding": {
                "top": 0,
                "right": 0,
                "bottom": 10,
                "left": 5,
            },
        },
        "bodyPhoto": {
            "columnStart": 1,
            "columnSpan": 10,
            "margin": {
                "top": 20,
                "bottom": 20,
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
                "top": 20,
                "bottom": 20,
            },
        },
        "footerLayout": {
            "margin": {
                "top": 10,
                "bottom": 40,
            },
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
