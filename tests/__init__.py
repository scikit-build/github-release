
import datetime as dt
import errno
import fnmatch
import operator
import os
import shlex
import subprocess
import sys

from contextlib import contextmanager
from functools import reduce

import pytest
import requests

from github_release import get_releases, gh_ref_delete, gh_release_delete

REPO_NAME = os.environ.get("INTEGRATION_TEST_REPO_NAME", None)
PROJECT_NAME = REPO_NAME.split("/")[1] if REPO_NAME else None

github_token_required = pytest.mark.skipif(
    os.environ.get("GITHUB_TOKEN", None) is None,
    reason="GITHUB_TOKEN is required")

integration_test_repo_name_required = pytest.mark.skipif(
    os.environ.get("INTEGRATION_TEST_REPO_NAME", None) is None,
    reason="INTEGRATION_TEST_REPO_NAME is required")


def mkdir_p(path):
    """Ensure directory ``path`` exists. If needed, parent directories
    are created.

    Adapted from http://stackoverflow.com/a/600612/1539918
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:  # pragma: no cover
            raise


@contextmanager
def push_dir(directory=None, make_directory=False):
    """Context manager to change current directory.

    :param directory:
      Path to set as current working directory. If ``None``
      is passed, ``os.getcwd()`` is used instead.

    :param make_directory:
      If True, ``directory`` is created.
    """
    old_cwd = os.getcwd()
    if directory:
        if make_directory:
            mkdir_p(directory)
        os.chdir(str(directory))
    yield
    os.chdir(old_cwd)


@contextmanager
def push_argv(argv):
    old_argv = sys.argv
    sys.argv = argv
    yield
    sys.argv = old_argv


#
# Subprocess
#

def run(*popenargs, **kwargs):
    """Run command with arguments and returns a list of captured lines.

    Process output is read line-by-line and captured until execution is over.
    Specifying the ``limit`` argument allow to limit the number of line captured
    and exit earlier.

    By default, captured lines are displayed as they are captured. Setting
    ``verbose`` to False disable this. Unless, verbose has been explicitly
    enabled, setting ``limit`` also disable output.

    Otherwise, the arguments are the same as for the Popen constructor.

    If ``ignore_errors`` is set, errors are ignored; otherwise, if the exit code
    was non-zero it raises a CalledProcessError.  The CalledProcessError object
    will have the return code in the returncode attribute and output in the
    output attribute.

    The stdout argument is not allowed as it is used internally.
    To capture standard error in the result, use stderr=STDOUT.
    """
    limit = kwargs.pop("limit", None)
    verbose = kwargs.pop("verbose", limit is None)
    ignore_errors = kwargs.pop("ignore_errors", False)
    line_count = 0
    captured_lines = []
    null_output = None
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    if ignore_errors and 'stderr' not in kwargs:
        null_output = open(os.devnull, 'w')
        kwargs['stderr'] = null_output
    popenargs = list(popenargs)
    if isinstance(popenargs[0], str) and not kwargs.get("shell", False):
        popenargs[0] = shlex.split(popenargs[0])
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    # Adapted from http://blog.endpoint.com/2015/01/getting-realtime-output-using-python.html  # noqa: E501
    while True:
        output = process.stdout.readline()
        if sys.version_info[0] >= 3:
            output = output.decode()
        if output == '' and process.poll() is not None:
            break
        if output:
            captured_lines.append(output.strip())
            if verbose:
                print(output.rstrip())
            line_count += 1
        if limit is not None and line_count == limit:
            process.kill()
            break
    ret_code = process.poll()
    if null_output is not None:
        null_output.close()
    error_occurred = ret_code is not None and ret_code > 0
    if error_occurred and not ignore_errors:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(
            ret_code, cmd, output="\n".join(captured_lines))
    if error_occurred and ignore_errors:
        return None
    return (captured_lines[0]
            if limit == 1 and len(captured_lines) == 1
            else captured_lines)


#
# Version
#

def read_version_file():
    with open("VERSION") as content:
        return content.readline().strip()


#
# GitHub
#

def clear_github_release_and_tags():

    @contextmanager
    def _ignore_4xx_errors():
        try:
            yield
        except requests.exceptions.HTTPError as exc_info:
            response = exc_info.response
            if 400 <= response.status_code < 500:
                print("Ignoring (%s Client Error: %s for url: %s)" % (
                    response.status_code, response.reason, response.url))
                return
            if sys.version_info[0] >= 3:
                raise exc_info.with_traceback(sys.exc_info()[2])
            else:
                raise (sys.exc_info()[0],
                    sys.exc_info()[1], sys.exc_info()[2])  # noqa: E999

    # Remove release and tags from GitHub
    for release in get_releases(REPO_NAME):
        with _ignore_4xx_errors():
            gh_release_delete(REPO_NAME, release["tag_name"])
    with _ignore_4xx_errors():
        gh_ref_delete(REPO_NAME, "*", keep_pattern="refs/heads/master")


#
# Git
#

def git_user_email():
    return run("git config --get user.email", limit=1, ignore_errors=True)


def git_user_name():
    return run("git config --get user.name", limit=1, ignore_errors=True)


GIT_USER_EMAIL = os.environ.get("INTEGRATION_TEST_GIT_USER_EMAIL",
                                git_user_email())
git_user_email_required = pytest.mark.skipif(
    GIT_USER_EMAIL is None,
    reason="git 'user.email' is required")

GIT_USER_NAME = os.environ.get("INTEGRATION_TEST_GIT_USER_NAME",
                               git_user_name())
git_user_name_required = pytest.mark.skipif(
    GIT_USER_NAME is None,
    reason="git 'user.name' is required")


def reset():
    # Reset to first commit
    first_sha = run("git log --reverse --pretty=\"%H\"", limit=1)
    run("git reset --hard %s" % first_sha)
    run("git push --quiet origin master --force")

    clear_github_release_and_tags()

    # Remove local tags
    for tag in run("git tag"):
        run("git tag -d %s" % tag)

    assert len(get_releases(repo_name=REPO_NAME)) == 0


def generate_commit_date():
    """Return date formatted as `YYYYMMDD` that should be associated
    with the next commit.

    Date is generated using ``2017-01-01 + days`` where ``days`` is
    the number of commit found in the repository.
    """
    start_date = dt.datetime.strptime(
        "2017-01-01 12:00:00", "%Y-%m-%d %H:%M:%S")
    days = int(run("git rev-list --count HEAD", limit=1))
    return start_date + dt.timedelta(days=days)


def get_commit_date(ref="HEAD"):
    """Get date formatted as `YYYYMMDD` for `ref` commit."""
    return dt.datetime.strptime(
        run(
            "git log -1 --format=\"%%ad\" --date=local %s" % str(ref), limit=1),
        "%c").strftime("%Y%m%d")


def get_tag(ref="HEAD"):
    """Get tag associated with ``ref``.

    Return None if no association was found.
    """
    return run(
        "git describe --tags --exact-match %s" % str(ref),
        limit=1, ignore_errors=True)


def do_commit(version=None, branch=None, release_tag=None, push=False):
    # Compose commit message
    commit_date = generate_commit_date()
    if version is None:
        version = read_version_file()
    msg = "Update to %s.dev%s" % (version, commit_date.strftime("%Y%m%d"))
    if release_tag is not None:
        msg = "%s %s" % (PROJECT_NAME, release_tag)
        version = release_tag
    if branch is not None:
        msg = "%s (branch: %s)" % (msg, branch)
    commit_msg = "ENH: %s" % msg
    # Update README and VERSION files
    with open("README.md", "a") as content:
        content.write("* %s\n" % msg)
    with open("VERSION", "w") as content:
        content.write(version)
    # Commit changes
    run("git add README.md")
    run("git add VERSION")
    run("git commit -m \"%s\" --date=%s" % (commit_msg,
                                            commit_date.isoformat()))
    # Push
    if push:
        run("git push --quiet origin master")
    # Create tag
    if release_tag is not None:
        run("git tag -a -m \"ENH: %s %s\" %s" % (
            PROJECT_NAME, release_tag, release_tag))
        if push:
            run("git push --quiet origin refs/tags/%s" % release_tag)
    print("")
    # Create branch
    if branch is not None:
        run("git branch %s" % branch)
        if push:
            run("git push --quiet origin refs/heads/%s" % branch)
    print("")

    return run("git rev-parse HEAD", limit=1)


#
# Test
#

def get_release_packages(release):
    return [asset["name"] for asset in release["assets"]]


def display_package_names(expected, release):
    print("Package names:")
    if "packages" in expected:
        print("  expected:\n    %s" % "\n    ".join(expected["packages"]))
    print("  current:\n    %s" % "\n    ".join(get_release_packages(release)))


def display_release(what, release):
    print("%s [%s] release:" % (what, release["tag_name"]))
    for attribute in ["name", "draft", "prerelease"]:
        if attribute in release:
            print("  %s: %s" % (attribute, release[attribute]))


def check_releases(expected, releases=None):  # noqa: C901
    """Return False if expected release data are missing or incorrect.

    Expected data can be either a dictionary or a list of dictionaries.

    Supported attributes are tag_name, name, draft, prerelease, package_count,
    package_pattern, packages and tag_date.

    * tag_name, name, and body are string
    * draft and prerelease are boolean
    * package_count is an integer
    * packages is a list of strings
    * package_pattern is either one tuple or a list of tuples of the
      form (expected_count, pattern).
    """

    def display_error():
        print("-" * 80 + "\nERROR:\n")

    if releases is None:
        releases = get_releases(REPO_NAME)
    if type(expected) is list:
        # Check overall count
        if len(releases) != len(expected):
            display_error()
            print("Numbers of releases is incorrect")
            print("  expected: %s" % len(expected))
            print("   current: %s" % len(releases))
            print("")
            return False
        # Check each release
        statuses = []
        for _expected in expected:
            statuses.append(check_releases(_expected, releases))
        return reduce(operator.and_, statuses) if statuses else True

    # Lookup release
    current_release = None
    for release in releases:
        if release["tag_name"] == expected["tag_name"]:
            current_release = release
            break
    if current_release is None:
        display_error()
        print("release [%s] not found" % expected["tag_name"])
        print("")
        return False
    # Check simple attributes
    for attribute in ["name", "draft", "prerelease", "body"]:
        if attribute not in expected:
            continue
        if attribute not in release:
            display_error()
            print("Release [%s] is missing [%s] "
                  "attributes" % (expected["tag_name"], attribute))
            display_release("Expected", expected)
            display_release("Current", release)
            print("")
            return False
        if expected[attribute] != release[attribute]:
            display_error()
            print("Release [%s]: attribute [%s] is "
                  "different" % (expected["tag_name"], attribute))
            display_release("Expected", expected)
            display_release("Current", release)
            print("")
            return False
    if "package_count" in expected:
        current_count = len(release["assets"])
        expected_count = expected["package_count"]
        if current_count != expected_count:
            display_error()
            print("Release [%s]: "
                  "Number of packages does not match" % expected["tag_name"])
            print("  expected: %s" % expected["package_count"])
            print("  current: %s" % current_count)
            print("")
            display_package_names(expected, release)
            return False
    if "package_pattern" in expected:
        if "packages" in expected:
            display_error()
            print("Release [%s]: attributes 'package_pattern' and 'packages' "
                  "are exclusive. Use only one." % expected["tag_name"])
            print("")
            return False
        if "package_count" in expected:
            display_error()
            print("Release [%s]: attributes 'package_pattern' and "
                  "'package_count' are exclusive. "
                  "Use only one." % expected["tag_name"])
            print("")
            return False
        patterns = expected["package_pattern"]
        if type(patterns) is not list:
            patterns = [patterns]
        for expected_package_count, pattern in patterns:
            current_package_count = 0
            for package in get_release_packages(release):
                if fnmatch.fnmatch(package, pattern):
                    current_package_count += 1
                    continue
            if expected_package_count != current_package_count:
                display_error()
                print("Release [%s]: "
                      "Number of packages associated with pattern [%s] "
                      "does not match" % (expected["tag_name"], pattern))
                print("  expected: %s" % expected_package_count)
                print("  current: %s" % current_package_count)
                print("")
                display_package_names(expected, release)
                print("")
                return False
    if "packages" in expected:
        diff = set(expected["packages"]) & set(get_release_packages(release))
        if diff:
            display_error()
            print("Release [%s]: "
                  "List of packages names are different" % expected["tag_name"])
            display_package_names(expected, release)
            print("")
            return False
    if "tag_date" in expected and release["draft"] is not True:
        expected_tag_date = expected["tag_date"]
        release_tag_date = get_commit_date(release["tag_name"])
        if expected_tag_date != release_tag_date:
            display_error()
            print("Release [%s]: tag dates do not match" % expected["tag_name"])
            print("  expected tag_date: %s" % expected_tag_date)
            print("  current tag_date: %s" % release_tag_date)
            print("")
            return False
    # Check that expected attributes are correct (e.g without typo)
    for attribute in [
            "tag_name", "name", "body", "draft", "prerelease",
            "package_count", "package_pattern", "packages",
            "tag_date"]:
        expected.pop(attribute, None)
    if len(expected) > 0:
        display_error()
        print("Unknown expected attributes: %s\n" % ", ".join(expected))
        return False
    return True
