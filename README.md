# githubrelease

This project aims at streamlining the distribution of
[releases](https://github.com/blog/1547-release-your-software) on Github.


> I made it because it sucks to have to download a file from a server,
> only to upload it to Github from the desktop.
>
> It also sucks to download a file from github to your desktop, and then
> SCP it to a server.
>
> This thing works nicely from an SSH session.
>
> -- <cite>@j0057 on Wednesday, August 13, 2014</cite>


In a nutshell, it allows to easily manage GitHub releases and
associated assets directly from the command-line:

```bash
$ githubrelease release jcfr/sandbox create 1.0.0 --prerelease
created '1.0.0' release

$ githubrelease asset jcfr/sandbox 1.0.0 "dist/*"
uploading '1.0.0' release asset(s) (found 16):
```

... or even from python:

```python
from github_release import gh_release_create, gh_asset_upload
gh_release_create("jcfr/sandbox ", "1.0.0", prerelease=True)
gh_asset_upload("jcfr/sandbox", "1.0.0", "dist/*")
```

That said, if you are looking for a full fledged GitHub API support for
Python, you should probably look into project like [PyGithub](https://github.com/PyGithub/PyGithub)

# Table of Contents

   * [githubrelease](#githubrelease)
   * [installing](#installing)
   * [configuring](#configuring)
   * [using the cli](#using-the-cli)
      * [release command](#release-command)
      * [asset command](#asset-command)
      * [ref command](#ref-command)
   * [using the module](#using-the-module)
   * [testing](#testing)
   * [maintainers: how to make a release ?](#maintainers-how-to-make-a-release-)
   * [license](#license)

<!--
<small>*Created by [gh-md-toc](https://github.com/ekalinin/github-markdown-toc)*</small>
-->

# installing

Install it in the global python:

```
pip install githubrelease
```

Done!

# configuring

First, [generate a new token](https://help.github.com/articles/creating-an-access-token-for-command-line-use). It should have
the repo scope.

Then, there are two options:

* Set the `GITHUB_TOKEN` environment variable:

```bash
export GITHUB_TOKEN=YOUR_TOKEN
/path/to/command
```


* Put the key in `~/.netrc`, which should have mode 0600 (`-rw-------`):

```
machine api.github.com
login YOUR_TOKEN
password x-oauth-basic

machine uploads.github.com
login YOUR_TOKEN
password x-oauth-basic
```

where ``YOUR_TOKEN`` should be replaced with the generated token.

# using the cli

The package installs one CLI named ``githubrelease``.

```bash
$ githubrelease 
Usage: githubrelease COMMAND [OPTIONS]
       githubrelease [-h]

A CLI to easily manage GitHub releases, assets and references.

Options:
    -h, --help       Show this help message and exit

Commands:
    release    Manage releases (list, create, delete, ...)
    asset      Manage release assets (upload, download, ...)
    ref        Manage references (list, create, delete, ...)

Run 'githubrelease COMMAND --help' for more information on a command.
```

<small>*For backward compatibility, it also installs `github-release` and `github-asset`*</small>

## ``release`` command

This command deals with releases. The general usage is:

    githubrelease release username/reponame command [tag] [options]

It understands the following commands:

| command       | parameters        | description                       |
|---------------|-------------------|-----------------------------------|
| list          |                   | list all releases                 |
| info          | tagname           | list one release                  |
| create        | tagname [options] | create a release                  |
| edit          | tagname [options] | Edit a release                    |
| delete        | tagname                | delete a release             |
| publish       | tagname [--prerelease] | make release public          |
| unpublish     | tagname [--prerelease] | make release draft           |
| release-notes | tagname           | use $EDITOR to edit release notes |

**Optional parameters:**

* create:

```bash
  --name NAME
  --publish
  --prerelease
  --target_commitish TARGET_COMMITISH
```

* edit:

```bash
  --tag_name TAG_NAME
  --target_commitish TARGET_COMMITISH
  --name NAME
  --body BODY
  --draft
  --prerelease
  --dry-run
  --verbose
```


## ``asset`` command

This command deals with release assets. The general usage is:

    githubrelease asset username/reponame command [tag] [filename] [options]

It understands the following commands:

| command   | parameters                 | description                                               |
|-----------|----------------------------|-----------------------------------------------------------|
| upload    | tagname filename           | upload a file to a release                                |
| download  |                            | download all files from all releases to current directory |
| download  | tagname                    | download all files from a release to current directory    |
| download  | tagname filename           | download file to current directory                        |
| delete    | tagname filename [options] | delete a file from a release                              |


**Optional parameters:**

* delete:

```bash
--keep-pattern KEEP_PATTERN
```


**Remarks:**

When specifying filenames, shell-like wildcards are supported, but make sure to
quote using single quotes, i.e. don't let the shell expand the wildcard pattern.

For the `download` command, you also need to specify a tagname of `'*'`


**Examples:**

```
$ # upload all example-project-1.4* files in /home/me/pkg
$ githubrelease asset octocat/example-project upload 1.4 '/home/me/pkg/example-project-1.4*'

$ # download all wheels from all releases
$ githubrelease asset octocat/example-project download '*' '*.whl'

$ # download all files from release 1.4
$ githubrelease asset octocat/example-project download 1.4

$ # download all files from example-project
# githubrelease asset octocat/example-project download
```

## ``ref`` command

This command deals with git references. The general usage is:

    githubrelease ref username/reponame command [options]

It understands the following commands:

| command   | parameters                             | description                                |
|-----------|----------------------------------------|--------------------------------------------|
| create    | ref sha                                | create reference (e.g heads/foo, tags/foo) |
| list      | [--tags] [--pattern PATTERN]           | list all references                        |
| delete    | pattern [--tags] [--keep_pattern KEEP_PATTERN] | delete selected references                 |


# using the module

The python API mirrors the command-line interface. Most of the available
function names follows this pattern:

```
gh_<COMMAND>_<COMMAND>
```

where the first ``<COMMAND>`` is either ``release``,
``asset`` or ``ref`` and the second one is any command respectively
documented above.

The parameters accepted by each function also mirrors the command-line
interface. The usual signature is:

```python
gh_<COMMAND>_<COMMAND>(repo_name, [param, [param,]] [option, [option]])
```

For example, here is the signature for ``gh_release_create``:

```python
def gh_release_create(repo_name, tag_name, 
                      name=None, publish=False, prerelease=False, target_commitish=None):
```

The type of each parameters or options can usually be inferred from
its name. If not, consider looking at [github_release.py](https://github.com/j0057/github-release/blob/update-readme/github_release.py).

```
repo_name        -> str
tag_name         -> str
name             -> str
publish          -> bool
prerelease       -> bool
target_commitish -> str
```

# testing

There are no formal tests yet :(

The plan is to leverage tools like [betamax](http://betamax.readthedocs.io)
allowing to intercept every request made and attempting to find a matching request
that has already been intercepted and recorded.

In the mean time, beside of manual testing, running the tests associated with
the ``publish_github_release`` add-on provided by [scikit-ci-addons](scikit-ci-addons.readthedocs.io/en/latest/addons.html#publish-github-release-py)
is all we have.

# maintainers: how to make a release ?

1. Configure `~/.pypirc` as described [here](https://packaging.python.org/distributing/#uploading-your-project-to-pypi).

2. Make sure the cli and module work as expected

3. Tag the release. Requires a GPG key with signatures. For version *X.Y.Z*::

    ```bash
    git tag -s -m "githubrelease X.Y.Z" X.Y.Z origin/master
    ```

4. Create the source tarball and binary wheels::

    ```bash
    rm -rf dist/
    python setup.py sdist bdist_wheel
    ```

5. Upload the packages to the testing PyPI instance::

    ```bash
    twine upload --sign -r pypitest dist/*
    ```

6. Check the [PyPI testing package page](https://testpypi.python.org/pypi/githubrelease/).

7. Upload the packages to the PyPI instance::

    ```bash
    twine upload --sign dist/*
    ```

8. Check the [PyPI package page](https://pypi.python.org/pypi/githubrelease/).

9. Make sure the package can be installed::

    ```bash
    mkvirtualenv test-pip-install
    pip install githubrelease
    rmvirtualenv test-pip-install
    ```


# license

Written by Joost Molenaar and Jean-Christophe Fillion-Robin

It is covered by the Apache License, Version 2.0:

http://www.apache.org/licenses/LICENSE-2.0

The license file was added at revision 0393859 on 2017-02-12, but you may
consider that the license applies to all prior revisions as well.