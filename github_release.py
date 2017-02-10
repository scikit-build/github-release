#!/usr/bin/env python2.7

from __future__ import print_function

import argparse
import fnmatch
import glob
import json
import os
import sys
import tempfile


from functools import wraps
from pprint import pprint

import requests
from requests import request


GITHUB_API = "https://api.github.com"


def _request(*args, **kwargs):
    if "GITHUB_TOKEN" in os.environ:
        kwargs["auth"] = (os.environ["GITHUB_TOKEN"], 'x-oauth-basic')
    return request(*args, **kwargs)


#
# Releases
#

def print_release_info(release):
    print('Tag name      : {tag_name}'.format(**release))
    if release['name']:
        print('Name          : {name}'.format(**release))
    print('ID            : {id}'.format(**release))
    print('Created       : {created_at}'.format(**release))
    print('URL           : {html_url}'.format(**release))
    print('Author        : {login}'.format(**release['author']))
    print('Is published  : {0}'.format(not release['draft']))
    print('Is prerelease : {0}'.format(release['prerelease']))
    if release['body']:
        print('Release notes :')
        print(release['body'])
    print('')
    for (i, asset) in enumerate(release['assets']):
        print_asset_info(i, asset)


def get_releases(repo_name):
    response = _request('GET', GITHUB_API + '/repos/{0}/releases'.format(repo_name))
    response.raise_for_status()
    return response.json()


def get_release(repo_name, tag_name):
    releases = get_releases(repo_name)
    try:
        release = next(r for r in releases if r['tag_name'] == tag_name)
        return release
    except StopIteration:
        return None


def get_release_info(repo_name, tag_name):
    release = get_release(repo_name, tag_name)
    if release is not None:
        return release
    else:
        raise Exception('Release with tag_name {0} not found'.format(tag_name))


def _update_release_sha(repo_name, tag_name, new_release_sha, dry_run):
    """Update the commit associated with a given release tag.

    Since updating a tag commit is not directly possible, this function
    does the following steps:
    * set the release tag to ``<tag_name>-tmp`` and associate it
      with ``new_release_sha``.
    * delete tag ``refs/tags/<tag_name>``.
    * update the release tag to ``<tag_name>`` and associate it
      with ``new_release_sha``.
    """
    if new_release_sha is None:
        return
    refs = get_refs(repo_name, tags=True, pattern="refs/tags/%s" % tag_name)
    if not refs:
        return
    assert len(refs) == 1
    previous_release_sha = refs[0]["object"]["sha"]
    if previous_release_sha == new_release_sha:
        return
    tmp_tag_name = tag_name + "-tmp"
    patch_release(repo_name, tag_name,
                  tag_name=tmp_tag_name,
                  target_commitish=new_release_sha,
                  dry_run=dry_run,
                  update_release_sha=False)
    gh_ref_delete(repo_name, "refs/tags/%s" % tag_name, dry_run=dry_run)
    patch_release(repo_name, tmp_tag_name,
                  tag_name=tag_name,
                  target_commitish=new_release_sha,
                  dry_run=dry_run,
                  update_release_sha=False)
    gh_ref_delete(repo_name,
                  "refs/tags/%s" % tmp_tag_name, dry_run=dry_run)


def patch_release(repo_name, current_tag_name, **values):
    dry_run = values.get("dry_run", False)
    verbose = values.get("verbose", False)
    release = get_release_info(repo_name, current_tag_name)

    if values.get("update_release_sha", True):
        _update_release_sha(
            repo_name,
            values.get("tag_name", release["tag_name"]),
            values.get("target_commitish", release["target_commitish"]),
            dry_run
        )

    data = {
        "tag_name": release["tag_name"],
        "target_commitish": release["target_commitish"],
        "name": release["name"],
        "body": release["body"],
        "draft": release["draft"],
        "prerelease": release["prerelease"]
    }

    updated = []
    for key in data:
        if key in values and data[key] != values[key]:
            updated.append("%s: '%s' -> '%s'" % (key, data[key], values[key]))
    if updated:
        print("updating release [%s]: \n  %s" % (current_tag_name, "\n  ".join(updated)))

    data.update(values)

    if not dry_run:
        response = _request('PATCH', GITHUB_API + '/repos/{0}/releases/{1}'.format(
              repo_name, release['id']),
              data=json.dumps(data),
              headers={'Content-Type': 'application/json'})
        response.raise_for_status()

    if current_tag_name != data["tag_name"]:
        gh_ref_delete(
            repo_name, "refs/tags/%s" % current_tag_name,
            tags=True, verbose=verbose, dry_run=dry_run)


def get_asset_info(repo_name, tag_name, filename):
    release = get_release_info(repo_name, tag_name)
    try:
        asset = next(a for a in release['assets'] if a['name'] == filename)
        return asset
    except StopIteration:
        raise Exception('Asset with filename {0} not found in release with tag_name {1}'.format(filename, tag_name))


def gh_release_list(repo_name):
    response = _request('GET', GITHUB_API + '/repos/{0}/releases'.format(repo_name))
    response.raise_for_status()
    map(print_release_info, sorted(response.json(), key=lambda r: r['tag_name']))


gh_release_list.description = {
  "help": "List releases",
  "params": ["repo_name"]
}


def gh_release_info(repo_name, tag_name):
    release = get_release_info(repo_name, tag_name)
    print_release_info(release)


gh_release_info.description = {
  "help": "Get release description",
  "params": ["repo_name", "tag_name"]
}


def gh_release_create(repo_name, tag_name, publish=False, prerelease=False, target_commitish=None):
    if get_release(repo_name, tag_name) is not None:
        print('release %s: already exists' % tag_name)
        return
    data = {
        'tag_name': tag_name,
        'draft': not publish and not prerelease,
        'prerelease': prerelease
    }
    if target_commitish is not None:
        data["target_commitish"] = target_commitish
    response = _request(
          'POST', GITHUB_API + '/repos/{0}/releases'.format(repo_name),
          data=json.dumps(data),
          headers={'Content-Type': 'application/json'})
    response.raise_for_status()
    print_release_info(response.json())


gh_release_create.description = {
  "help": "Create a release",
  "params": ["repo_name", "tag_name", "publish", "prerelease", "target_commitish"],
  "optional_params": {"publish": bool, "prerelease": bool, "target_commitish": str}
}


def gh_release_edit(repo_name, current_tag_name,
                    tag_name=None, target_commitish=None, name=None,
                    body=None,
                    draft=None, prerelease=None, dry_run=False, verbose=False):
    attributes = {}
    for key in ["tag_name", "target_commitish", "name", "body", "draft", "prerelease", "dry_run", "verbose"]:
        if locals().get(key, None) is not None:
            attributes[key] = locals()[key]
    patch_release(repo_name, current_tag_name, **attributes)


gh_release_edit.description = {
  "help": "Edit a release",
  "params": ["repo_name", "current_tag_name", "tag_name", "target_commitish", "name", "body", "draft", "prerelease", "dry-run", "verbose"],
  "optional_params": {"tag_name": str, "target_commitish": str, "name": str, "body": str, "draft": bool, "prerelease": bool, "dry-run": bool, "verbose": bool},
  "optional_params_defaults": {"draft": None, "prerelease": None}
}


def gh_release_delete(repo_name, pattern, keep_pattern=None, dry_run=False, verbose=False):
    releases = get_releases(repo_name)
    for release in releases:
        if not fnmatch.fnmatch(release['tag_name'], pattern):
            if verbose:
                print('skipping release {0}: do not match {1}'.format(
                    release['tag_name'], pattern))
            continue
        if keep_pattern is not None:
            if fnmatch.fnmatch(release['tag_name'], keep_pattern):
                continue
        print('deleting release {0}'.format(release['tag_name']))
        if dry_run:
            continue
        response = _request('DELETE', GITHUB_API + '/repos/{0}/releases/{1}'.format(repo_name, release['id']))
        response.raise_for_status()


gh_release_delete.description = {
  "help": "Delete selected releases",
  "params": ["repo_name", "pattern", "keep_pattern", "dry-run", "verbose"],
  "optional_params": {"keep_pattern": str, "dry-run": bool, "verbose": bool}
}


def gh_release_publish(repo_name, tag_name, prerelease=False):
    patch_release(repo_name, tag_name, draft=False, prerelease=prerelease)


gh_release_publish.description = {
  "help": "Publish a release setting draft to 'False'",
  "params": ["repo_name", "tag_name", "prerelease"],
  "optional_params": {"prerelease": bool}
}


def gh_release_unpublish(repo_name, tag_name, prerelease=False):
    draft = not prerelease
    patch_release(repo_name, tag_name, draft=draft, prerelease=prerelease)


gh_release_unpublish.description = {
  "help": "Unpublish a release setting draft to 'True'",
  "params": ["repo_name", "tag_name", "prerelease"],
  "optional_params": {"prerelease": bool}
}


def gh_release_notes(repo_name, tag_name):
    release = get_release_info(repo_name, tag_name)
    (_, filename) = tempfile.mkstemp(suffix='.md')
    try:
        if release['body']:
            with open(filename, 'w+b') as f:
                f.write(release['body'])
        ret = os.system('{0} {1}'.format(os.environ['EDITOR'], filename))
        if ret:
            raise Exception('{0} returned exit code {1}'.format(os.environ['EDITOR'], ret))
        with open(filename, 'rb') as f:
            body = f.read()
        if release['body'] == body:
            return
        patch_release(repo_name, tag_name, body=body)
    finally:
        os.remove(filename)


gh_release_notes.description = {
  "help": "Set release notes",
  "params": ["repo_name", "tag_name"]
}


def gh_release_debug(repo_name, tag_name):
    release = get_release_info(repo_name, tag_name)
    pprint(release)


gh_release_debug.description = {
  "help": "Print release detailed information",
  "params": ["repo_name", "tag_name"]
}


#
# Assets
#

def print_asset_info(i, asset):
    print('  Asset #{i} name     : {name}'.format(i=i, **asset))
    print('  Asset #{i} size     : {size}'.format(i=i, **asset))
    print('  Asset #{i} uploader : {login}'.format(i=i, **asset['uploader']))
    print('  Asset #{i} URL      : {browser_download_url}'.format(i=i, **asset))
    print('')


def gh_asset_upload(repo_name, tag_name, pattern, dry_run=False):
    release = get_release_info(repo_name, tag_name)
    uploaded = False
    upload_url = release["upload_url"]
    if "{" in upload_url:
        upload_url = upload_url[:upload_url.index("{")]
    for filename in glob.glob(pattern):
        print('release {0}: uploading {1}'.format(tag_name, filename))
        if dry_run:
            uploaded = True
            continue
        with open(filename, 'rb') as f:
            basename = os.path.basename(filename)
            url = '{0}?name={1}'.format(upload_url, basename)
            print('url:', url)
            response = _request('POST', url, headers={'Content-Type': 'application/octet-stream'}, data=f.read())
            response.raise_for_status()
            uploaded = True
    if not uploaded:
        print("release {0}: skipping upload: there are no files matching '{1}'".format(tag_name, pattern))


gh_asset_upload.description = {
  "help": "Upload release assets",
  "params": ["repo_name", "tag_name", "pattern", "dry-run"],
  "optional_params": {"dry-run": bool}
}


def gh_asset_erase(repo_name, tag_name, pattern,
                   keep_pattern=None, dry_run=False):
    release = get_release_info(repo_name, tag_name)
    for asset in release['assets']:
        if not fnmatch.fnmatch(asset['name'], pattern):
            continue
        if keep_pattern is not None:
            if fnmatch.fnmatch(asset['name'], keep_pattern):
                continue
        print('release {0}: deleting {1}'.format(tag_name, asset['name']))
        if dry_run:
            continue
        response = _request(
              'DELETE',
              GITHUB_API + '/repos/{0}/releases/assets/{1}'.format(repo_name, asset['id']))
        response.raise_for_status()


gh_asset_erase.description = {
  "help": "Delete selected release assets",
  "params": ["repo_name", "tag_name", "pattern", "keep-pattern", "dry-run"],
  "optional_params": {"keep-pattern": str, "dry-run": bool}
}


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
            print('release {0}: downloading {1}'.format(release['tag_name'], asset['name']))
            response = _request(
                method='GET',
                url=GITHUB_API + '/repos/{0}/releases/assets/{1}'.format(repo_name, asset['id']),
                allow_redirects=False,
                headers={'Accept': 'application/octet-stream'})
            while response.status_code == 302:
                response = _request('GET', response.headers['Location'], allow_redirects=False)
            with open(asset['name'], 'w+b') as f:
                f.write(response.content)


gh_asset_download.description = {
  "help": "Download release assets",
  "params": ["repo_name", "tag_name", "pattern"],
  "optional_params": {"tag_name": str, "pattern": str}
}


#
# References
#

def print_object_info(ref_object):
    print('Object:')
    print('  type        : {type}'.format(**ref_object))
    print('  sha         : {sha}'.format(**ref_object))


def print_ref_info(ref):
    print('-' * 80)
    print('Reference     : {ref}'.format(**ref))
    print_object_info(ref['object'])


def get_refs(repo_name, tags=False, pattern=None):
    response = _request(
          'GET', GITHUB_API + '/repos/{0}/git/refs'.format(repo_name))
    response.raise_for_status()

    # If "tags" is True, keep only "refs/tags/*"
    data = response.json()
    if tags:
        data = []
        for ref in response.json():
            if ref['ref'].startswith("refs/tags"):
                data.append(ref)

    # If "pattern" is not None, select only matching references
    filtered_data = data
    if pattern is not None:
        filtered_data = []
        for ref in data:
            if fnmatch.fnmatch(ref['ref'], pattern):
                filtered_data.append(ref)

    return filtered_data


def gh_ref_list(repo_name, tags=False,  pattern=None, verbose=False):
    refs = get_refs(repo_name, tags=tags, pattern=pattern)
    if verbose:
        map(print_ref_info, sorted(refs, key=lambda r: r['ref']))
    else:
        map(lambda ref: print(ref['ref']), sorted(refs, key=lambda r: r['ref']))


gh_ref_list.description = {
  "help": "List all references",
  "params": ["repo_name", "tags", "pattern", "verbose"],
  "optional_params": {"tags": bool, "pattern": str, "verbose": bool}
}


def gh_ref_create(repo_name, reference, sha):
    data = {
        'ref': "refs/%s" % reference,
        'sha': sha
    }
    response = _request(
          'POST', GITHUB_API + '/repos/{0}/git/refs'.format(repo_name),
          data=json.dumps(data),
          headers={'Content-Type': 'application/json'})
    response.raise_for_status()
    print_ref_info(response.json())


gh_ref_create.description = {
  "help": "Create reference (e.g heads/foo, tags/foo)",
  "params": ["repo_name", "reference", "sha"]
}


def gh_ref_delete(repo_name, pattern, keep_pattern=None, tags=False, dry_run=False, verbose=False):
    refs = get_refs(repo_name, tags=tags)
    for ref in refs:
        if not fnmatch.fnmatch(ref['ref'], pattern):
            if verbose:
                print('skipping reference {0}: do not match {1}'.format(ref['ref'], pattern))
            continue
        if keep_pattern is not None:
            if fnmatch.fnmatch(ref['ref'], keep_pattern):
                continue
        print('deleting reference {0}'.format(ref['ref']))
        if dry_run:
            continue
        response = _request(
              'DELETE', GITHUB_API + '/repos/{0}/git/{1}'.format(repo_name, ref['ref']))
        response.raise_for_status()


gh_ref_delete.description = {
  "help": "Delete selected references",
  "params": ["repo_name", "pattern", "keep_pattern", "tags", "dry-run", "verbose"],
  "optional_params": {"keep_pattern": str, "tags": bool, "dry-run": bool, "verbose": bool}
}


#
# Decorators
#

def handle_http_error(func):
    @wraps(func)
    def with_error_handling(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            print('Error sending {0} to {1}'.format(e.request.method, e.request.url))
            print('<', e.request.method, e.request.path_url)
            for k in sorted(e.request.headers.keys()):
                print('<', k, ':', e.request.headers[k])
            if e.request.body:
                print('<')
                print('<', repr(e.request.body[:35]), '(total {0} bytes of data)'.format(len(e.request.body)))
            print('')
            print('>', e.response.status_code, e.response.reason)
            for k in sorted(e.response.headers.keys()):
                print('>', k.title(), ':', e.response.headers[k])
            if e.response.content:
                print('>')
                print('>', repr(e.response.content[:35]), '(total {0} bytes of data)'.format(len(e.response.content)))
            return 1
    return with_error_handling


#
# Command line parsing helpers
#

def _gh_parser(commands, prog=None):
    parser = argparse.ArgumentParser(description=__doc__, prog=prog)
    parser.add_argument("repo_name", type=str)
    subparsers = parser.add_subparsers(help='sub-command help')

    for command in commands:
        func = commands[command]
        cmd_help = func.description["help"]
        cmd_params = list(func.description["params"])
        cmd_opt_params = func.description.get("optional_params", {})
        cmd_parser = subparsers.add_parser(command, help=cmd_help)
        for cmd_param in cmd_params:
            if cmd_param == "repo_name":  # parameter already specified above
                continue
            if cmd_param not in cmd_opt_params.keys():
                cmd_parser.add_argument(cmd_param, type=str)
            else:
                if cmd_opt_params[cmd_param] is bool:
                    cmd_parser.add_argument(
                        "--%s" % cmd_param, action='store_true')
                else:
                    cmd_parser.add_argument(
                        "--%s" % cmd_param, type=cmd_opt_params[cmd_param])
        cmd_parser.set_defaults(func=func)

        # Set defaults
        params_defaults = func.description.get("optional_params_defaults", {})
        cmd_parser.set_defaults(**params_defaults)

    return parser


def _gh_parse_arguments(commands, argv, prog):
    args = _gh_parser(commands, prog).parse_args(argv)
    func = args.func
    return func(*[
        vars(args).get(arg_name.replace("-", "_"), None)
        for arg_name in func.description["params"]
        ])


#
# Command line parsers
#

RELEASE_COMMANDS = {
    'list': gh_release_list,            # gh-release j0057/iplbapi list
    'info': gh_release_info,            # gh-release j0057/iplbapi info 1.4.3
    'create': gh_release_create,        # gh-release j0057/iplbapi create 1.4.4
    'edit': gh_release_edit,            # gh-release j0057/iplbapi edit 1.4.4 --name "Release 1.4.4"
    'delete': gh_release_delete,        # gh-release j0057/iplbapi delete 1.4.4
    'publish': gh_release_publish,      # gh-release j0057/iplbapi publish 1.4.4
    'unpublish': gh_release_unpublish,  # gh-release j0057/iplbapi unpublish 1.4.4
    'release-notes': gh_release_notes,  # gh-release j0057/iplbapi release-notes 1.4.3
    'debug': gh_release_debug           # gh-release j0057/iplbapi debug 1.4.3
}


@handle_http_error
def gh_release(argv=None, prog=None):
    return _gh_parse_arguments(RELEASE_COMMANDS, argv, prog)


ASSET_COMMANDS = {
    'upload': gh_asset_upload,          # gh-asset j0057/iplbapi upload 1.4.4 bla-bla_1.4.4.whl
                                        # gh-asset j0057/iplbapi download
                                        # gh-asset j0057/iplbapi download 1.4.4
    'download': gh_asset_download,      # gh-asset j0057/iplbapi download 1.4.4 bla-bla_1.4.4.whl
    'delete': gh_asset_erase,           # gh-asset j0057/iplbapi erase 1.4.4 bla-bla_1.4.4.whl
    'erase': gh_asset_erase,            # gh-asset j0057/iplbapi erase 1.4.4 bla-bla_1.4.4.whl
}


@handle_http_error
def gh_asset(argv=None, prog=None):
    return _gh_parse_arguments(ASSET_COMMANDS, argv, prog)


REF_COMMANDS = {
    'list': gh_ref_list,
    'create': gh_ref_create,
    'delete': gh_ref_delete
}


@handle_http_error
def gh_ref(argv=None, prog=None):
    return _gh_parse_arguments(REF_COMMANDS, argv, prog)


def main():
    prog = os.path.basename(sys.argv[0])
    parser = argparse.ArgumentParser(
        description=__doc__,
        usage="""%s [-h] {release, asset, ref} ...

positional arguments:
    {release, asset, ref}
                        sub-command help
    release             Manage releases (list, create, delete, ...)
    asset               Manage release assets (upload, download, ...)
    ref                 Manage references (list, create, delete, ...)

optional arguments:
  -h, --help            show this help message and exit
""" % prog)
    parser.add_argument('command', help='Subcommand to run')
    args = parser.parse_args(sys.argv[1:2])
    if "gh_%s" % args.command not in globals():
        print("Unrecognized command")
        parser.print_help()
        exit(1)
    globals()["gh_%s" % args.command](
        sys.argv[2:], "%s %s" % (prog, args.command))


#
# Script entry point
#

if __name__ == '__main__':
    main()
