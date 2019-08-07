#!/usr/bin/env python
"""Setup for unify."""

from __future__ import unicode_literals

import ast

from setuptools import setup


def version():
    """Return version string."""
    with open('unify.py') as input_file:
        for line in input_file:
            if line.startswith('__version__'):
                return ast.parse(line).body[0].value.s
    return None


with open('README.rst') as readme:
    setup(name='unify',
          version=version(),
          description='Modifies strings to all use the same '
                      '(single/double) quote where possible.',
          long_description=readme.read(),
          license='Expat License',
          author='Steven Myint',
          url='https://github.com/myint/unify',
          classifiers=['Intended Audience :: Developers',
                       'Environment :: Console',
                       'Programming Language :: Python :: 2.6',
                       'Programming Language :: Python :: 2.7',
                       'Programming Language :: Python :: 3',
                       'License :: OSI Approved :: MIT License'],
          keywords='strings, formatter, style',
          py_modules=['unify'],
          entry_points={
              'console_scripts': ['unify = unify:main']},
          install_requires=['untokenize'],
          test_suite='test_unify')
