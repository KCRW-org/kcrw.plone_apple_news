# -*- coding: utf-8 -*-
"""Installer for the kcrw.plone_apple_news package."""

from setuptools import find_packages
from setuptools import setup


long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CONTRIBUTORS.rst').read(),
    open('CHANGES.rst').read(),
])


setup(
    name='kcrw.plone_apple_news',
    version='0.1.0',
    description="Apple News API integration for Plone CMS",
    long_description=long_description,
    # Get more from https://pypi.org/classifiers/
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 4.3",
        "Framework :: Plone :: 4.0",
        "Framework :: Plone :: 5.1",
        "Framework :: Plone :: 5.2",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords='Python Plone',
    author='Alec Mitchell',
    author_email='alecpm@gmail.com',
    url='https://github.com/collective/kcrw.plone_apple_news',
    project_urls={
        'PyPI': 'https://pypi.python.org/pypi/kcrw.plone_apple_news',
        'Source': 'https://github.com/v/kcrw.plone_apple_news',
        'Tracker': 'https://github.com/KCRW-org/kcrw.plone_apple_news/issues',
    },
    license='GPL version 2',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['kcrw'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    python_requires="==2.7",
    install_requires=[
        'setuptools',
        # -*- Extra requirements: -*-
        'six',
        'plone.api',
        'plone.app.dexterity',
        'kcrw.apple_news',
        'plone.outputfilters',
        'plone.app.contentrules',
        'lxml>=3.1.0'
    ],
    extras_require={
        'test': [
            'plone.app.testing',
            'plone.testing',
            'mock',
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    [console_scripts]
    update_locale = kcrw.plone_apple_news.locales.update:update_locale
    """,
)
