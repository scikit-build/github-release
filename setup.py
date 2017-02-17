#!/usr/bin/env python2.7

from setuptools import setup

with open('requirements.txt', 'r') as fp:
    requirements = list(filter(bool, (line.strip() for line in fp)))

with open('requirements-dev.txt', 'r') as fp:
    dev_requirements = list(filter(bool, (line.strip() for line in fp)))

setup_requires = ['setuptools-version-command']

setup(
    name='githubrelease',

    url='https://github.com/j0057/github-release',

    author='Joost Molenaar, Jean-Christophe Fillion-Robin',
    author_email='j.j.molenaar@gmail.com, jchris.fillionr@kitware.com',

    version_command='git describe',

    py_modules=['github_release'],
    entry_points={
        'console_scripts': [
            'githubrelease = github_release:main',
            'github-release = github_release:gh_release',
            'github-asset = github_release:gh_asset'
        ]},

    license="Apache",

    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Version Control',
        'Topic :: System :: Software Distribution'
    ],

    install_requires=requirements,
    tests_require=dev_requirements,
    setup_requires=setup_requires
)
