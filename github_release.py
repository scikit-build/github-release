#!/usr/bin/env python2.7

import fnmatch
import glob
import json
import os
import sys
import tempfile

import requests
from requests import request

def print_asset_info(i, asset):
    print '  Asset #{i} name     : {name}'.format(i=i, **asset)
    print '  Asset #{i} size     : {size}'.format(i=i, **asset)
    print '  Asset #{i} uploader : {login}'.format(i=i, **asset['uploader'])
    print '  Asset #{i} URL      : {browser_download_url}'.format(i=i, **asset)
    print

def print_release_info(release):
    print  'Tag name      : {tag_name}'.format(**release)
    if release['name']:
     print 'Name          : {name}'.format(**release) 
    print  'ID            : {id}'.format(**release)
    print  'Created       : {created_at}'.format(**release)
    print  'URL           : {html_url}'.format(**release)
    print  'Author        : {login}'.format(**release['author'])
    print  'Is published  : {0}'.format(not release['draft'])
    if release['body']:
     print 'Release notes :'
     print release['body']
    print
    for (i, asset) in enumerate(release['assets']):
        print_asset_info(i, asset)

def get_releases(repo_name):
    response = request('GET', 'https://api.github.com/repos/{0}/releases'.format(repo_name))
    response.raise_for_status()
    return response.json()

def get_release_info(repo_name, tag_name):
    releases = get_releases(repo_name)
    try:
        release = next(r for r in releases if r['tag_name'] == tag_name)
        return release
    except StopIteration:
        raise Exception('Release with tag_name {0} not found'.format(tag_name))

def patch_release(repo_name, tag_name, **values):
    release = get_release_info(repo_name, tag_name)
    data = {
        "tag_name": release["tag_name"],
        "target_commitish": release["target_commitish"],
        "name": release["name"],
        "body": release["body"],
        "draft": release["draft"],
        "prerelease": release["prerelease"] }
    data.update(values)
    response = request('PATCH', 'https://api.github.com/repos/{0}/releases/{1}'.format(repo_name, release['id']),
        data=json.dumps(data),
        headers={'Content-Type': 'application/json'})
    response.raise_for_status()

def get_asset_info(repo_name, tag_name, filename):
    release = get_release_info(repo_name, tag_name)
    try:
        asset = next(a for a in release['assets'] if a['name'] == filename)
        return asset
    except StopIteration:
        raise Exception('Asset with filename {0} not found in release with tag_name {1}'.format(filename, tag_name))

def gh_release_list(repo_name):
    response = request('GET', 'https://api.github.com/repos/{0}/releases'.format(repo_name))
    response.raise_for_status()
    map(print_release_info, sorted(response.json(), key=lambda r: r['tag_name']))

def gh_release_info(repo_name, tag_name):
    release = get_release_info(repo_name, tag_name)
    print_release_info(release)

def gh_release_create(repo_name, tag_name):
    data = json.dumps({'tag_name': tag_name, 'draft': True})
    response = request('POST', 'https://api.github.com/repos/{0}/releases'.format(repo_name),
        data=json.dumps({'tag_name': tag_name, 'draft': True}),
        headers={'Content-Type': 'application/json'})
    response.raise_for_status()
    print_release_info(response.json())

def gh_release_delete(repo_name, tag_name):
    release = get_release_info(repo_name, tag_name)
    response = request('DELETE', 'https://api.github.com/repos/{0}/releases/{1}'.format(repo_name, release['id']))
    response.raise_for_status()

def gh_release_publish(repo_name, tag_name):
    patch_release(repo_name, tag_name, draft=False)

def gh_release_unpublish(repo_name, tag_name):
    patch_release(repo_name, tag_name, draft=True)

def gh_release_notes(repo_name, tag_name):
    release = get_release_info(repo_name, tag_name)
    (_, filename) = tempfile.mkstemp(suffix='.md')
    try:
        if release['body']:
            with open(filename, 'w+b') as f:
                f.write(release['body'])
        ret = os.system('{0} {1}'.format(os.environ['EDITOR'], filename))
        if ret: raise Exception('{0} returned exit code {1}'.format(os.environ['EDITOR'], ret))
        with open(filename, 'rb') as f:
            body = f.read()
        if release['body'] == body:
            return
        patch_release(repo_name, tag_name, body=body)
    finally:
        os.remove(filename)

def gh_asset_upload(repo_name, tag_name, pattern):
    release = get_release_info(repo_name, tag_name)
    for filename in glob.glob(pattern):
        with open(filename, 'rb') as f:
            basename = os.path.basename(filename)
            response = request('POST', 
                'https://uploads.github.com/repos/{0}/releases/{1}/assets?name={2}'.format(repo_name, release['id'], basename),
                headers={'Content-Type':'application/octet-stream'},
                data=f.read())
            response.raise_for_status()

def gh_asset_erase(repo_name, tag_name, pattern):
    release = get_releases(repo_name)
    for asset in release['assets']:
        if not fnmatch.fnmatch(asset['name'], pattern):
            continue
        response = request('DELETE',
            'https://api.github.com/repos/{0}/releases/assets/{1}'.format(repo_name, asset['id']))
        response.raise_for_status()

def gh_asset_download(repo_name, tag_name=None, pattern=None):
    releases = get_releases(repo_name)
    for release in releases:
        if tag_name and not fnmatch.fnmatch(release['tag_name'], tag_name):
            continue
        for asset in release['assets']:
            if pattern and not fnmatch.fnmatch(asset['name'], pattern):
                continue
            if os.path.exists(asset['name']):
                continue
            print 'release {0}: downloading {1}'.format(release['tag_name'], asset['name'])
            response = request(
                method='GET',
                url='https://api.github.com/repos/{0}/releases/assets/{1}'.format(repo_name, asset['id']),
                allow_redirects=False,
                headers={'Accept':'application/octet-stream'})
            while response.status_code == 302:
                response = request('GET', response.headers['Location'], allow_redirects=False)
            with open(asset['name'], 'w+b') as f:
                f.write(response.content)

def gh_release():
    args = sys.argv[1:]
    commands = {
        'list': gh_release_list,            # gh-release j0057/iplbapi list
        'info': gh_release_info,            # gh-release j0057/iplbapi info 1.4.3
        'create': gh_release_create,        # gh-release j0057/iplbapi create 1.4.4
        'delete': gh_release_delete,        # gh-release j0057/iplbapi delete 1.4.4
        'publish': gh_release_publish,      # gh-release j0057/iplbapi publish 1.4.4
        'unpublish': gh_release_unpublish,  # gh-release j0057/iplbapi unpublish 1.4.4
        'release-notes': gh_release_notes,  # gh-release j0057/iplbapi release-notes 1.4.3
    }
    return handle_http_error(lambda: commands[args.pop(1)](*args))

def gh_asset():
    args = sys.argv[1:]
    commands = {
        'upload': gh_asset_upload,          # gh-asset j0057/iplbapi upload 1.4.4 bla-bla_1.4.4.whl
                                            # gh-asset j0057/iplbapi download
                                            # gh-asset j0057/iplbapi download 1.4.4
        'download': gh_asset_download,      # gh-asset j0057/iplbapi download 1.4.4 bla-bla_1.4.4.whl
        'delete': gh_asset_erase,           # gh-asset j0057/iplbapi erase 1.4.4 bla-bla_1.4.4.whl
        'erase': gh_asset_erase,            # gh-asset j0057/iplbapi erase 1.4.4 bla-bla_1.4.4.whl
    }
    return handle_http_error(lambda: commands[args.pop(1)](*args))

def handle_http_error(func):
    try:
        func()
        return 0
    except requests.exceptions.HTTPError as e:
        print 'Error sending {0} to {1}'.format(e.request.method, e.request.url)
        print '<', e.request.method, e.request.path_url
        for k in sorted(e.request.headers.keys()):
            print '<', k, ':', e.request.headers[k]
        if e.request.body:
            print '<'
            print '<', repr(e.request.body[:35]), '(total {0} bytes of data)'.format(len(e.request.body))
        print
        print '>', e.response.status_code, e.response.reason
        for k in sorted(e.response.headers.keys()):
            print '>', k.title(), ':', e.response.headers[k]
        if e.response.content:
            print '>'
            print '>', repr(e.response.content[:35]), '(total {0} bytes of data)'.format(len(e.response.content))
        return 1

