#!/usr/bin/env python2.7

from setuptools import setup

with open('requirements.txt', 'r') as fp:
    requirements = list(filter(bool, (line.strip() for line in fp)))

setup_requires = ['setuptools-version-command']

setup(
    name='githubrelease',
    version_command='git describe',
    author='Joost Molenaar',
    author_email='j.j.molenaar@gmail.com',
    url='https://github.com/j0057/github-release',
    py_modules=['github_release'],
    install_requires=requirements,
    setup_requires=setup_requires,
    entry_points={
        'console_scripts': [
            'githubrelease = github_release:main',
            'github-release = github_release:gh_release',
            'github-asset = github_release:gh_asset'
        ]}
)
