# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import kcrw.plone_apple_news


class KcrwPloneAppleNewsLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=kcrw.plone_apple_news)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'kcrw.plone_apple_news:default')


KCRW_PLONE_APPLE_NEWS_FIXTURE = KcrwPloneAppleNewsLayer()


KCRW_PLONE_APPLE_NEWS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(KCRW_PLONE_APPLE_NEWS_FIXTURE,),
    name='KcrwPloneAppleNewsLayer:IntegrationTesting',
)


KCRW_PLONE_APPLE_NEWS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(KCRW_PLONE_APPLE_NEWS_FIXTURE,),
    name='KcrwPloneAppleNewsLayer:FunctionalTesting',
)


KCRW_PLONE_APPLE_NEWS_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        KCRW_PLONE_APPLE_NEWS_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='KcrwPloneAppleNewsLayer:AcceptanceTesting',
)
