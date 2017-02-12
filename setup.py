#!/usr/bin/env python2.7

from setuptools import setup

with open('requirements.txt', 'r') as fp:
    requirements = list(filter(bool, (line.strip() for line in fp)))

with open('requirements-dev.txt', 'r') as fp:
    dev_requirements = list(filter(bool, (line.strip() for line in fp)))

setup_requires = ['setuptools-version-command']

setup(
    name='githubrelease',
    version_command='git describe',
    author='Joost Molenaar, Jean-Christophe Fillion-Robin',
    author_email='j.j.molenaar@gmail.com, jchris.fillionr@kitware.com',
    url='https://github.com/j0057/github-release',
    py_modules=['github_release'],
    install_requires=requirements,
    tests_require=dev_requirements,
    setup_requires=setup_requires,
    entry_points={
        'console_scripts': [
            'githubrelease = github_release:main',
            'github-release = github_release:gh_release',
            'github-asset = github_release:gh_asset'
        ]},
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
    ],
    license="Apache",
)
