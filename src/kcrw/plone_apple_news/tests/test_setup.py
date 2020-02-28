# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from kcrw.plone_apple_news.testing import KCRW_PLONE_APPLE_NEWS_INTEGRATION_TESTING  # noqa: E501
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSetup(unittest.TestCase):
    """Test that kcrw.plone_apple_news is properly installed."""

    layer = KCRW_PLONE_APPLE_NEWS_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        if get_installer:
            self.installer = get_installer(self.portal, self.layer['request'])
        else:
            self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if kcrw.plone_apple_news is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'kcrw.plone_apple_news'))

    def test_browserlayer(self):
        """Test that IKcrwPloneAppleNewsLayer is registered."""
        from kcrw.plone_apple_news.interfaces import (
            IKcrwPloneAppleNewsLayer)
        from plone.browserlayer import utils
        self.assertIn(
            IKcrwPloneAppleNewsLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = KCRW_PLONE_APPLE_NEWS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        if get_installer:
            self.installer = get_installer(self.portal, self.layer['request'])
        else:
            self.installer = api.portal.get_tool('portal_quickinstaller')
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstallProducts(['kcrw.plone_apple_news'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if kcrw.plone_apple_news is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'kcrw.plone_apple_news'))

    def test_browserlayer_removed(self):
        """Test that IKcrwPloneAppleNewsLayer is removed."""
        from kcrw.plone_apple_news.interfaces import \
            IKcrwPloneAppleNewsLayer
        from plone.browserlayer import utils
        self.assertNotIn(
            IKcrwPloneAppleNewsLayer,
            utils.registered_layers())
