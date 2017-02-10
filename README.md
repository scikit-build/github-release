# githubrelease

This is a python script to manage releases on github. I made it because it
sucks to have to download a file from a server, only to upload it to Github
from the desktop. It also sucks to download a file from github to your 
desktop, and then SCP it to a server. This thing works nicely from an SSH 
session.

## installing 

Install it in the global python:

```
pip install githubrelease
```

Done!

## configuring

First, [generate a new token](https://help.github.com/articles/creating-an-access-token-for-command-line-use). It should have
the repo scope.

Then, there are two options:

* Set the `GITHUB_TOKEN` environment variable:

```bash
export GITHUB_TOKEN=...
/path/to/command

# or 

GITHUB_TOKEN=... /path/to/command
```


* Put the key in `~/.netrc`, which should have mode 0600 (`-rw-------`):

```
machine api.github.com
login [TOKEN]
password x-oauth-basic

machine uploads.github.com
login [TOKEN]
password x-oauth-basic
```

## installed scripts

The package installs two scripts, `github-release` and `github-asset`

### github-release

This script deals with releases. The general usage is:

    github-release username/reponame command [tag]

It understands the following commands:

| command       | parameters    | description                       |
|---------------|---------------|-----------------------------------|
| list          |               | list all releases                 |
| info          | tagname       | list one release                  |
| create        | tagname       | create a release                  |
| delete        | tagname       | delete a release                  |
| publish       | tagname       | make release public               |
| unpublish     | tagname       | make release draft                |
| release-notes | tagname       | use $EDITOR to edit release notes |

### github-asset

This script deals with release assets. The general usage is:

    github-asset username/reponame command [tag] [filename]

It understands the following commands:

| command   | parameters        | description                                               |
|-----------|-------------------|-----------------------------------------------------------|
| upload    | tagname filename  | upload a file to a release                                |
| download  |                   | download all files from all releases to current directory |
| download  | tagname           | download all files from a release to current directory    |
| download  | tagname filename  | download file to current directory                        |
| delete    | tagname filename  | delete a file from a release                              |

When specifying filenames, shell-like wildcards are supported, but make sure to
quote using single quotes, i.e. don't let the shell expand the wildcard pattern.

For the `download` command, you also need to specify a tagname of `'*'`

Examples:

```
$ # upload all example-project-1.4* files in /home/me/pkg
$ github-asset octocat/example-project upload 1.4 '/home/me/pkg/example-project-1.4*'

$ # download all wheels from all releases
$ github-asset octocat/example-project download '*' '*.whl'

$ # download all files from release 1.4
$ github-asset octocat/example-project download 1.4

$ # download all files from example-project
# github-asset octocat/example-project download
```
