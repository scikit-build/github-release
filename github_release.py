#!/usr/bin/env python2.7

import json
import os
import sys
import requests
from requests import request

KEY = 'ebeb42747a0a7c1bec493b7cd5895ecc4bb844db'
AUTH = requests.auth.HTTPBasicAuth(KEY, 'x-oauth-basic')

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
    response = request('GET', 'https://api.github.com/repos/{0}/releases'.format(repo_name), auth=AUTH)
    response.raise_for_status()
    return response.json()

def get_release_info(repo_name, tag_name):
    releases = get_releases(repo_name)
    try:
        release = next(r for r in releases if r['tag_name'] == tag_name)
        return release
    except StopIteration:
        raise Exception('Release with tag_name {0} not found'.format(tag_name))

def get_asset_info(repo_name, tag_name, filename):
    release = get_release_info(repo_name, tag_name)
    try:
        asset = next(a for a in release['assets'] if a['name'] == filename)
        return asset
    except StopIteration:
        raise Exception('Asset with filename {0} not found in release with tag_name {1}'.format(filename, tag_name))

def gh_release_list(repo_name):
    response = request('GET', 'https://api.github.com/repos/{0}/releases'.format(repo_name), auth=AUTH)
    response.raise_for_status()
    map(print_release_info, sorted(response.json(), key=lambda r: r['tag_name']))

def gh_release_info(repo_name, tag_name):
    release = get_release_info(repo_name, tag_name)
    print_release_info(release)

def gh_release_create(repo_name, tag_name):
    data = json.dumps({'tag_name': tag_name, 'draft': True})
    response = request('POST', 'https://api.github.com/repos/{0}/releases'.format(repo_name), auth=AUTH, 
        data=json.dumps({'tag_name': tag_name, 'draft': True}),
        headers={'Content-Type': 'application/json'})
    response.raise_for_status()
    print_release_info(response.json())

def gh_release_delete(repo_name, tag_name):
    release = get_release_info(repo_name, tag_name)
    response = request('DELETE', 
        'https://api.github.com/repos/{0}/releases/{1}'.format(repo_name, release['id']), 
        auth=AUTH)
    response.raise_for_status()

def gh_release_set_draft(repo_name, tag_name, is_draft):
    release = get_release_info(repo_name, tag_name)
    response = request('PATCH', 'https://api.github.com/{0}/releases/{1}'.format(repo_name, release['id']),
        auth=AUTH,
        data=json.dumps({'draft': is_draft}),
        headers={'Content-Type': 'application/json'})
    response.raise_for_status()

def gh_release_publish(repo_name, tag_name):
    gh_release_set_draft(repo_name, tag_name, is_draft=False)

def gh_release_unpublish(repo_name, tag_name):
    gh_release_set_draft(repo_name, tag_name, is_draft=True)

def gh_asset_upload(repo_name, tag_name, filename):
    release = get_release_info(repo_name, tag_name)
    with open(filename) as f:
        basename = os.path.basename(filename)
        response = request('POST', 
            'https://uploads.github.com/repos/{0}/releases/{1}/assets?name={2}'.format(repo_name, release['id'], basename),
            headers={'Content-Type':'application/octet-stream'},
            auth=AUTH,
            data=f.read())
        response.raise_for_status()

def gh_asset_erase(repo_name, tag_name, filename):
    asset = get_asset_info(repo_name, tag_name, filename)
    response = request('DELETE',
        'https://api.github.com/repos/{0}/releases/assets/{1}'.format(repo_name, asset['id']),
        auth=AUTH)
    response.raise_for_status()

def gh_asset_download(repo_name, tag_name=None, asset_name=None):
    releases = get_releases(repo_name)
    for release in releases:
        if tag_name and release['tag_name'] != tag_name:
            continue
        for asset in release['assets']:
            if asset_name and asset['name'] != asset_name:
                continue
            if os.path.exists(asset['name']):
                continue
            print 'downloading {0} from release {1}'.format(asset['name'], release['tag_name'])
            response = request(
                method='GET',
                url='https://api.github.com/repos/{0}/releases/assets/{1}'.format(repo_name, asset['id']),
                auth=AUTH,
                allow_redirects=False,
                headers={'Accept':'application/octet-stream'})
            while response.status_code == 302:
                response = request('GET', response.headers['Location'], allow_redirects=False)
            with open(asset_name, 'w+b') as f:
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
    }
    commands[args.pop(1)](*args)

def gh_asset():
    args = sys.argv[1:]
    commands = {
        'upload': gh_asset_upload,          # gh-asset j0057/iplbapi upload 1.4.4 bla-bla_1.4.4.whl
                                            # gh-asset j0057/iplbapi download
                                            # gh-asset j0057/iplbapi download 1.4.4
        'download': gh_asset_download,      # gh-asset j0057/iplbapi download 1.4.4 bla-bla_1.4.4.whl
        'erase': gh_asset_erase,            # gh-asset j0057/iplbapi erase 1.4.4 bla-bla_1.4.4.whl
    }
    commands[args.pop(1)](*args)

def handle_http_error(func):
    try:
        func()
        sys.exit(0)
    except requests.exceptions.HTTPError as e:
        print e
        print e.request
        print e.request.url
        print e.response
        print e.response.content
        sys.exit(1)

if __name__ == '__main__':
    handle_http_error(gh_release)
    #handle_http_error(gh_asset)
