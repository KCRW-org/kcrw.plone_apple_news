import sys

try:
    from . import forms
except ImportError:
    from . import forms_plone4 as forms
    sys.modules['kcrw.plone_apple_news.actions.forms'] = forms
