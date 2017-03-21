#!/usr/bin/env python2.7

from __future__ import print_function

import fnmatch
import glob
import json
import os
import random
import string
import tempfile
import time


from functools import wraps
from pprint import pprint

import click
import requests
from requests import request


GITHUB_API = "https://api.github.com"


def _request(*args, **kwargs):
    with_auth = kwargs.pop("with_auth", True)
    if "GITHUB_TOKEN" in os.environ and with_auth:
        kwargs["auth"] = (os.environ["GITHUB_TOKEN"], 'x-oauth-basic')
    for _ in range(3):
        response = request(*args, **kwargs)
        is_travis = os.getenv("TRAVIS",  None) is not None
        if is_travis and 400 <= response.status_code < 500:
            print("Retrying in 1s (%s Client Error: %s for url: %s)" % (
                response.status_code, response.reason, response.url))
            time.sleep(1)
            continue
        break
    return response


def handle_http_error(func):
    @wraps(func)
    def with_error_handling(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            print('Error sending {0} to {1}'.format(
                e.request.method, e.request.url))
            print('<', e.request.method, e.request.path_url)
            for k in sorted(e.request.headers.keys()):
                print('<', k, ':', e.request.headers[k])
            if e.request.body:
                print('<')
                print('<', repr(e.request.body[:35]),
                      '(total {0} bytes of data)'.format(len(e.request.body)))
            print('')
            print('>', e.response.status_code, e.response.reason)
            for k in sorted(e.response.headers.keys()):
                print('>', k.title(), ':', e.response.headers[k])
            if e.response.content:
                print('>')
                print('>', repr(e.response.content[:35]),
                      '(total {0} bytes of data)'.format(
                          len(e.response.content)))
            return 1
    return with_error_handling


@click.group()
def main():
    """A CLI to easily manage GitHub releases, assets and references."""
    pass


@main.group("release")
@click.argument('repo_name', metavar="REPOSITORY")
@click.pass_context
@handle_http_error
def gh_release(ctx, repo_name):
    """Manage releases (list, create, delete, ...) for
    REPOSITORY (e.g jcfr/sandbox)
    """
    ctx.obj = repo_name


# 1.6.0 (deprecated): Remove this bloc
class AssetGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        cmd_name = "delete" if cmd_name == "erase" else cmd_name
        return click.Group.get_command(self, ctx, cmd_name)


@main.group("asset", cls=AssetGroup)
@click.argument('repo_name', metavar="REPOSITORY")
@click.pass_context
@handle_http_error
def gh_asset(ctx, repo_name):
    """Manage release assets (upload, download, ...) for
    REPOSITORY (e.g jcfr/sandbox)
    """
    ctx.obj = repo_name


@main.group("ref")
@click.argument('repo_name', metavar="REPOSITORY")
@click.pass_context
@handle_http_error
def gh_ref(ctx, repo_name):
    """Manage references (list, create, delete, ...) for
    REPOSITORY (e.g jcfr/sandbox)
    """
    ctx.obj = repo_name


#
# Releases
#

def print_release_info(release, title=None, indent=""):
    if title is None:
        title = "release '{0}' info".format(release["tag_name"])
    print(indent + title)
    indent = "  " + indent
    print(indent + 'Tag name      : {tag_name}'.format(**release))
    if release['name']:
        print(indent + 'Name          : {name}'.format(**release))
    print(indent + 'ID            : {id}'.format(**release))
    print(indent + 'Created       : {created_at}'.format(**release))
    print(indent + 'URL           : {html_url}'.format(**release))
    print(indent + 'Author        : {login}'.format(**release['author']))
    print(indent + 'Is published  : {0}'.format(not release['draft']))
    print(indent + 'Is prerelease : {0}'.format(release['prerelease']))
    if release['body']:
        print(indent + 'Release notes :')
        print(indent + release['body'])
    print('')
    for (i, asset) in enumerate(release['assets']):
        print_asset_info(i, asset, indent=indent)


def get_releases(repo_name, verbose=False):
    response = _request(
        'GET', GITHUB_API + '/repos/{0}/releases'.format(repo_name))
    response.raise_for_status()
    releases = response.json()
    if verbose:
        list(map(print_release_info,
                 sorted(response.json(), key=lambda r: r['tag_name'])))
    return releases


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
    * set the release tag to ``<tag_name>-tmp-XXXXXX`` (where `XXXXXX` is a
      random string) and associate it with ``new_release_sha``.
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
    suffix = ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(6))
    tmp_tag_name = tag_name + "-tmp-%s" % suffix
    patch_release(repo_name, tag_name,
                  tag_name=tmp_tag_name,
                  target_commitish=new_release_sha,
                  dry_run=dry_run)
    gh_ref_delete(repo_name, "refs/tags/%s" % tag_name, dry_run=dry_run)
    patch_release(repo_name, tmp_tag_name,
                  tag_name=tag_name,
                  target_commitish=new_release_sha,
                  dry_run=dry_run)
    gh_ref_delete(repo_name,
                  "refs/tags/%s" % tmp_tag_name, dry_run=dry_run)


def patch_release(repo_name, current_tag_name, **values):
    dry_run = values.get("dry_run", False)
    verbose = values.get("verbose", False)
    release = get_release_info(repo_name, current_tag_name)
    new_tag_name = values.get("tag_name", release["tag_name"])

    _update_release_sha(
        repo_name,
        new_tag_name,
        values.get("target_commitish", None),
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
        print("updating '%s' release: \n  %s" % (
            current_tag_name, "\n  ".join(updated)))
        print("")

    data.update(values)

    if not dry_run:
        url = GITHUB_API + '/repos/{0}/releases/{1}'.format(
            repo_name, release['id'])
        response = _request(
            'PATCH', url,
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
        raise Exception('Asset with filename {0} not found in '
                        'release with tag_name {1}'.format(filename, tag_name))


@gh_release.command("list")
@click.pass_obj
def _cli_release_list(repo_name):
    """List releases"""
    return get_releases(repo_name, verbose=True)


@gh_release.command("info")
@click.argument("tag_name")
@click.pass_obj
def _cli_release_info(repo_name, tag_name):
    """Get release description"""
    release = get_release_info(repo_name, tag_name)
    print_release_info(release)


@gh_release.command("create")
@click.argument("tag_name")
@click.argument("asset_pattern", nargs=-1)
@click.option("--name")
@click.option("--publish", is_flag=True, default=False)
@click.option("--prerelease", is_flag=True, default=False)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--target-commitish")
@click.pass_obj
def cli_release_create(*args, **kwargs):
    """Create a release"""
    gh_release_create(*args, **kwargs)


def gh_release_create(repo_name, tag_name, asset_pattern=None, name=None,
                      publish=False, prerelease=False,
                      target_commitish=None, dry_run=False):
    if get_release(repo_name, tag_name) is not None:
        print('release %s: already exists\n' % tag_name)
        return
    data = {
        'tag_name': tag_name,
        'draft': not publish and not prerelease,
        'prerelease': prerelease
    }
    if name is not None:
        data["name"] = name
    if target_commitish is not None:
        data["target_commitish"] = target_commitish
    if not dry_run:
        response = _request(
              'POST', GITHUB_API + '/repos/{0}/releases'.format(repo_name),
              data=json.dumps(data),
              headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        print_release_info(response.json(),
                           title="created '%s' release" % tag_name)
    else:
        print("created '%s' release (dry_run)" % tag_name)
    if asset_pattern is not None:
        gh_asset_upload(repo_name, tag_name, asset_pattern, dry_run=dry_run)


@gh_release.command("edit")
@click.argument("current_tag_name")
@click.option("--tag-name", default=None)
@click.option("--target-commitish", default=None)
@click.option("--name", default=None)
@click.option("--body", default=None)
@click.option("--draft", is_flag=True, default=None)
@click.option("--prerelease", is_flag=True, default=None)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--verbose", is_flag=True, default=False)
@click.pass_obj
def _cli_release_edit(*args, **kwargs):
    """Edit a release"""
    gh_release_edit(*args, **kwargs)


def gh_release_edit(repo_name, current_tag_name,
                    tag_name=None, target_commitish=None, name=None,
                    body=None,
                    draft=None, prerelease=None, dry_run=False, verbose=False):
    attributes = {}
    for key in [
        "tag_name", "target_commitish", "name", "body", "draft",
        "prerelease", "dry_run", "verbose"
    ]:
        if locals().get(key, None) is not None:
            attributes[key] = locals()[key]
    patch_release(repo_name, current_tag_name, **attributes)


@gh_release.command("delete")
@click.argument("pattern")
@click.option("--keep-pattern")
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--verbose", is_flag=True, default=False)
@click.pass_obj
def _cli_release_delete(*args, **kwargs):
    """Delete selected release"""
    gh_release_delete(*args, **kwargs)


def gh_release_delete(repo_name, pattern, keep_pattern=None,
                      dry_run=False, verbose=False):
    releases = get_releases(repo_name)
    candidates = []
    # Get list of candidate releases
    for release in releases:
        if not fnmatch.fnmatch(release['tag_name'], pattern):
            if verbose:
                print('skipping release {0}: do not match {1}'.format(
                    release['tag_name'], pattern))
            continue
        if keep_pattern is not None:
            if fnmatch.fnmatch(release['tag_name'], keep_pattern):
                continue
        candidates.append(release['tag_name'])
    for tag_name in candidates:
        release = get_release(repo_name, tag_name)
        print('deleting release {0}'.format(release['tag_name']))
        if dry_run:
            continue
        url = (GITHUB_API
               + '/repos/{0}/releases/{1}'.format(repo_name, release['id']))
        response = _request('DELETE', url)
        response.raise_for_status()
    return len(candidates) > 0


@gh_release.command("publish")
@click.argument("tag_name")
@click.option("--prerelease", is_flag=True, default=False)
@click.pass_obj
def _cli_release_publish(*args, **kwargs):
    """Publish a release setting draft to 'False'"""
    gh_release_publish(*args, **kwargs)


def gh_release_publish(repo_name, tag_name, prerelease=False):
    patch_release(repo_name, tag_name, draft=False, prerelease=prerelease)


@gh_release.command("unpublish")
@click.argument("tag_name")
@click.option("--prerelease", is_flag=True, default=False)
@click.pass_obj
def _cli_release_unpublish(*args, **kwargs):
    """Unpublish a release setting draft to 'True'"""
    gh_release_unpublish(*args, **kwargs)


def gh_release_unpublish(repo_name, tag_name, prerelease=False):
    draft = not prerelease
    patch_release(repo_name, tag_name, draft=draft, prerelease=prerelease)


@gh_release.command("release-notes")
@click.argument("tag_name")
@click.pass_obj
def _cli_release_notes(*args, **kwargs):
    """Set release notes"""
    gh_release_notes(*args, **kwargs)


def gh_release_notes(repo_name, tag_name):
    release = get_release_info(repo_name, tag_name)
    (_, filename) = tempfile.mkstemp(suffix='.md')
    try:
        if release['body']:
            with open(filename, 'w+b') as f:
                f.write(release['body'])
        ret = os.system('{0} {1}'.format(os.environ['EDITOR'], filename))
        if ret:
            raise Exception(
                '{0} returned exit code {1}'.format(os.environ['EDITOR'], ret))
        with open(filename, 'rb') as f:
            body = f.read()
        if release['body'] == body:
            return
        patch_release(repo_name, tag_name, body=body)
    finally:
        os.remove(filename)


@gh_release.command("debug")
@click.argument("tag_name")
@click.pass_obj
def _cli_release_debug(repo_name, tag_name):
    """Print release detailed information"""
    release = get_release_info(repo_name, tag_name)
    pprint(release)


#
# Assets
#

def print_asset_info(i, asset, indent=""):
    print(indent + "Asset #{i}".format(i=i))
    indent = "  " + indent
    print(indent + "name      : {name}".format(i=i, **asset))
    print(indent + "size      : {size}".format(i=i, **asset))
    print(indent + "uploader  : {login}".format(i=i, **asset['uploader']))
    print(indent + "URL       : {browser_download_url}".format(i=i, **asset))
    print(indent + "Downloads : {download_count}".format(i=i, **asset))
    print("")


@gh_asset.command("upload")
@click.argument("tag_name")
@click.argument("pattern")
@click.pass_obj
def _cli_asset_upload(*args, **kwargs):
    """Upload release assets"""
    gh_asset_upload(*args, **kwargs)


def gh_asset_upload(repo_name, tag_name, pattern, dry_run=False, verbose=False):
    if not dry_run:
        release = get_release_info(repo_name, tag_name)
    else:
        release = {"assets": [], "upload_url": "unknown"}
    uploaded = False
    already_uploaded = False
    upload_url = release["upload_url"]
    if "{" in upload_url:
        upload_url = upload_url[:upload_url.index("{")]

    if type(pattern) in [list, tuple]:
        filenames = []
        for package in pattern:
            filenames.extend(glob.glob(package))
        set(filenames)
    elif pattern:
        filenames = glob.glob(pattern)
    else:
        filenames = []

    if len(filenames) > 0:
        print("uploading '%s' release asset(s) "
              "(found %s):" % (tag_name, len(filenames)))

    for filename in filenames:
        print("  uploading %s" % filename)
        basename = os.path.basename(filename)
        # Skip if an asset with same name has already been uploaded
        # Trying to upload would give a HTTP error 422
        download_url = None
        for asset in release["assets"]:
            if asset["name"] == basename:
                download_url = asset["browser_download_url"]
                break
        if download_url:
            already_uploaded = True
            print("  skipping (asset with same name already exists)")
            print("  download_url: %s" % download_url)
            print("")
            continue
        if dry_run:
            uploaded = True
            print("  download_url: Unknown (dry_run)")
            print("")
            continue
        # Attempt upload
        with open(filename, 'rb') as f:
            url = '{0}?name={1}'.format(upload_url, basename)
            if verbose:
                print("  upload_url: %s" % url)
            response = _request(
                'POST', url,
                headers={'Content-Type': 'application/octet-stream'},
                data=f.read())
            response.raise_for_status()
            asset = response.json()
            print("  download_url: %s" % asset["browser_download_url"])
            print("")
            uploaded = True
    if not uploaded and not already_uploaded:
        print("skipping upload of '%s' release assets ("
              "no files match pattern(s): %s)" % (tag_name, pattern))
        print("")


@gh_asset.command("delete")
@click.argument("tag_name")
@click.argument("pattern")
@click.option("--keep-pattern", default=None)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--verbose", is_flag=True, default=False)
@click.pass_obj
def _cli_asset_delete(*args, **kwargs):
    """Delete selected release assets"""
    gh_asset_delete(*args, **kwargs)


def gh_asset_delete(repo_name, tag_name, pattern,
                    keep_pattern=None, dry_run=False, verbose=False):
    release = get_release_info(repo_name, tag_name)
    # List of assets
    excluded_assets = {}
    matched_assets = []
    matched_assets_to_keep = {}
    for asset in release['assets']:
        if not fnmatch.fnmatch(asset['name'], pattern):
            skip_reason = "do NOT match pattern '%s'" % pattern
            excluded_assets[asset['name']] = skip_reason
            continue
        matched_assets.append(asset)
        if keep_pattern is not None:
            if fnmatch.fnmatch(asset['name'], keep_pattern):
                skip_reason = "match keep_pattern '%s'" % keep_pattern
                matched_assets_to_keep[asset['name']] = skip_reason
                continue
    # Summary
    summary = "matched: %s, matched-but-keep: %s, not-matched: %s" % (
        len(matched_assets),
        len(matched_assets_to_keep),
        len(excluded_assets)
    )
    print("deleting '%s' release asset(s) (%s):" % (tag_name, summary))
    # Perform deletion
    for asset in matched_assets:
        if asset['name'] in matched_assets_to_keep:
            if verbose:
                skip_reason = matched_assets_to_keep[asset['name']]
                print("  skipping %s (%s)" % (asset['name'], skip_reason))
            continue
        print("  deleting %s" % asset['name'])
        if dry_run:
            continue
        url = (
            GITHUB_API
            + '/repos/{0}/releases/assets/{1}'.format(repo_name, asset['id'])
        )
        response = _request('DELETE', url)
        response.raise_for_status()
    if len(matched_assets) == 0:
        print("  nothing to delete")
    print("")
    if verbose:
        indent = "  "
        print(indent + "assets NOT matching selection pattern [%s]:" % pattern)
        for asset_name in excluded_assets:
            print(indent + "  " + asset_name)
        print("")


@gh_asset.command("download")
@click.argument("tag_name")
@click.argument("pattern", required=False)
@click.pass_obj
def _cli_asset_download(*args, **kwargs):
    """Download release assets"""
    gh_asset_download(*args, **kwargs)


def gh_asset_download(repo_name, tag_name=None, pattern=None):
    releases = get_releases(repo_name)
    downloaded = 0
    for release in releases:
        if tag_name and not fnmatch.fnmatch(release['tag_name'], tag_name):
            continue
        for asset in release['assets']:
            if pattern and not fnmatch.fnmatch(asset['name'], pattern):
                continue
            if os.path.exists(asset['name']):
                absolute_path = os.path.abspath(asset['name'])
                print('release {0}: '
                      'skipping {1}: '
                      'found {2}'.format(
                        release['tag_name'], asset['name'], absolute_path))
                continue
            print('release {0}: '
                  'downloading {1}'.format(release['tag_name'], asset['name']))
            response = _request(
                method='GET',
                url=GITHUB_API + '/repos/{0}/releases/assets/{1}'.format(
                    repo_name, asset['id']),
                allow_redirects=False,
                headers={'Accept': 'application/octet-stream'})
            while response.status_code == 302:
                response = _request(
                    'GET', response.headers['Location'], allow_redirects=False,
                    with_auth=False
                )
            with open(asset['name'], 'w+b') as f:
                f.write(response.content)
            downloaded += 1
    return downloaded


#
# References
#

def print_object_info(ref_object, indent=""):
    print(indent + 'Object')
    print(indent + '  type : {type}'.format(**ref_object))
    print(indent + '  sha  : {sha}'.format(**ref_object))


def print_ref_info(ref, indent=""):
    print(indent + "Reference '{ref}'".format(**ref))
    print_object_info(ref['object'], indent="  " + indent)
    print("")


def get_refs(repo_name, tags=None, pattern=None):
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


@gh_ref.command("list")
@click.option("--tags", is_flag=True, default=False)
@click.option("--pattern", default=None)
@click.option("--verbose", is_flag=True, default=False)
@click.pass_obj
def _cli_ref_list(*args, **kwargs):
    """List all references"""
    gh_ref_list(*args, **kwargs)


def gh_ref_list(repo_name, tags=None,  pattern=None, verbose=False):
    refs = get_refs(repo_name, tags=tags, pattern=pattern)
    sorted_refs = sorted(refs, key=lambda r: r['ref'])
    if verbose:
        list(map(print_ref_info, sorted_refs))
    else:
        list(map(lambda ref: print(ref['ref']), sorted_refs))


@gh_ref.command("create")
@click.argument("reference")
@click.argument("sha")
@click.pass_obj
def _cli_ref_create(*args, **kwargs):
    """Create reference (e.g heads/foo, tags/foo)"""
    gh_ref_create(*args, **kwargs)


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


@gh_ref.command("delete")
@click.argument("pattern")
@click.option("--keep-pattern", default=None)
@click.option("--tags", is_flag=True, default=False)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--verbose", is_flag=True, default=False)
@click.pass_obj
def _cli_ref_delete(*args, **kwargs):
    """Delete selected references"""
    gh_ref_delete(*args, **kwargs)


def gh_ref_delete(repo_name, pattern, keep_pattern=None, tags=False,
                  dry_run=False, verbose=False):
    refs = get_refs(repo_name, tags=tags)
    for ref in refs:
        if not fnmatch.fnmatch(ref['ref'], pattern):
            if verbose:
                print('skipping reference {0}: '
                      'do not match {1}'.format(ref['ref'], pattern))
            continue
        if keep_pattern is not None:
            if fnmatch.fnmatch(ref['ref'], keep_pattern):
                continue
        print('deleting reference {0}'.format(ref['ref']))
        if dry_run:
            continue
        response = _request(
            'DELETE',
            GITHUB_API + '/repos/{0}/git/{1}'.format(repo_name, ref['ref']))
        response.raise_for_status()


#
# Script entry point
#

if __name__ == '__main__':
    main()
