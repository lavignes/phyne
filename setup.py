#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'A fine lexer generator for Python',
    'author': 'Scott LaVigne',
    'url': 'https://github.com/pyrated/phyne',
    'download_url': 'https://github.com/pyrated/phyne.git',
    'author_email': 'pyrated@gmail.com',
    'version': '0.1',
    'packages': ['phyne'],
    'scripts': [],
    'name': 'phyne'
}

setup(**config)