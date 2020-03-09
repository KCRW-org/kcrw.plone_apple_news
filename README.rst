=====================
kcrw.plone_apple_news
=====================

This package provides a Plone addon that integrates publishing CMS content to
Apple News using the `Apple News API`_. It provides a variety of features that
attempt to render Plone content into `Apple News Format (ANF)`_ articles.
This package is intended to be used by a variety of audiences:

- Content managers can manually create, update and delete Apple News articles
  using toolbar actions (the permission is assigned by default to Reviewers
  and Admins/Managers).
- Integrators and power-users can setup automated actions to create, update,
  publish, and delete Apple News article using actions registered with Plone's
  content rules engine.
- Developers can register event handlers to perform Apple News API actions,
  adapters to provide custom rendering of specific content, and register custom
  functions for transforming HTML content into Apple News components.

This add-on relies on the `kcrw.apple_news`_ python library, which is
documented at `kcrw.apple_news Read the Docs`_.


Features
--------

- Control Panel for setting Apple News API parameters (key, secret, channel id),
  Content related settings like image scales to include, and the ability to
  customize the Apple News documnent styles and layout using custom JSON.
- A behavior for Dexterity content types and a marker interface for other content
  which enables Apple News actions.
- Provides a set of actions for uploading, updating, and deleting Articles
  in an Apple News channel. Additionally, there's an action for downloading
  a document ZIP bundle for local development and customization.
- Content Rules actions for uploading, updating, and deleting Apple News
  articles.
- An adapter for transforming Dexterity and AT content into Apple News Article
  format. This can be subclassed to provide custom behavior for specific content
  types.
- A pluggable HTML processor for transforming WYSIWYG entered HTML into Article
  components. Currently this it includes the following functions:

  - Translating class attributes into `ANF text style`_ attributes
  - Resolving UID based urls
  - Converting image tags into Photo/Image components and including internal
    images in the ANF article bundle
  - Stripping out all HTML elements and attributes not supported by ANF

To Do
-----

- Add tag splitter for supported embed.ly plugin components
- Add tag splitter to provide social media components for social embeds
- Add related items module using `ArticleLink` and `ArticleThumbnail`
  components.
- Add tag splitter to separate `video` tags into into `Video` components
- Add tag splitter to separate `audio` tags into into `Audio` components


Installation
------------

Install kcrw.plone_apple_news by adding it to your buildout::

    [buildout]

    ...

    eggs =
        kcrw.plone_apple_news


and then running ``bin/buildout``. After restarting your instance, you can
install the "Apple News Integration" add-on from the Site Setup -> Add-ons
control panel.

If you are running Plone < 4.3.18, you may need to pin lxml>=3.1.0 in your buildout.


Quick Start
-----------

You'll need an Apple News Publisher account to make full use of this add-on.
The first step is creating an account and getting API key and Channel
information in `News Publisher`_. Apple provides
`detailed documentation for News Publisher`_ as well. Once you hav a account
setup and have installed the add-on you can enter your account information in
the "Apple News Settings" control panel under Plone Site Setup.

Go to the "Dexterity Content Types" panel select the "News Item" type
(this add-on will work with other types, but "News Item" is the obvious
choice for testing), and use the "Behaviors" tab to enable the
"Apple News Integration" behavior. Now when viewing a News Item you
should see options under the toolbar "Actions" menu to
"Create Apple News Article" and "Export Apple News Article as ZIP".
The former uploads your article to your channel, and the latter (which
is available even if you don't have API credentials set) downloads
a ZIP file of the ANF formatted article for debugging/review
and preview in the News Preview app. Once you've used the "Create"
action, it will be replaced with actions to "Update" and "Delete"
the article from your Apple News Channel.


Contribute
----------

- Issue Tracker: https://github.com/KCRW-org/kcrw.plone_apple_news/issues
- Source Code: https://github.com/KCRW-org/kcrw.plone_apple_news


Support
-------

If you are having issues, please let me know.


License
-------

The project is licensed under the GPLv2.


.. _Apple News API: https://developer.apple.com/documentation/apple_news/apple_news_api
.. _Apple News Format (ANF): https://developer.apple.com/documentation/apple_news/apple_news_format_tutorials
.. _kcrw.apple_news Read the Docs: https://kcrwapple-news.readthedocs.io
.. _ANF text style: https://developer.apple.com/documentation/apple_news/textstyle
.. _News Publisher: https://www.icloud.com/newspublisher/
.. _detailed documentation for News Publisher: https://support.apple.com/guide/news-publisher/welcome/icloud
