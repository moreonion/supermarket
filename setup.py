#!/usr/bin/env python

from distutils.core import setup

setup(
    name='supermarket',
    version='0.0',
    description='The g2k supermarket project database.',
    author='Roman Zimmermann',
    author_email='roman@more-onion.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
    ],
    packages=['supermarket'],
    install_requires=[
        'Flask',
        'Flask-Cors',
        'Flask-Script',
        'Flask-SQLAlchemy',
        'moflask',
    ],
    dependency_links=[
      'git+https://github.com/moreonion/moflask.git@master#egg=moflask-0.1',
    ],
    extras_require={
        'test': ['pytest'],
    },
)
