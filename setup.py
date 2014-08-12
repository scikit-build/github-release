#!/usr/bin/env python2.7

import setuptools

try:
    with open('requirements.txt', 'r') as f:
        requirements = f.read().split()
except IOError:
    with open('githubrelease.egg-info/requires.txt', 'r') as f:
        requirements = f.read().split()

setuptools.setup(
    name='githubrelease',
    version_command='git describe',
    author='Joost Molenaar',
    author_email='j.j.molenaar@gmail.com',
    url='https://github.com/j0057/github-release',
    py_modules=['github_release'],
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'github-release = github_release:gh_release',
            'github-asset = github_release:gh_asset'
        ]})
