
import os

import pytest

from . import (
    GIT_USER_EMAIL,
    git_user_email,
    GIT_USER_NAME,
    git_user_name,
    github_token_required,
    push_dir,
    REPO_NAME,
    reset,
    run
)


@github_token_required
@pytest.fixture(scope='function')
def gh_src_dir(tmpdir_factory):
    tmp_dir = tmpdir_factory.mktemp("source")
    with push_dir(tmp_dir):
        # clone
        token = os.environ["GITHUB_TOKEN"]
        run("git clone https://%s@github.com/%s source" % (token, REPO_NAME))

        srcdir = tmp_dir.join("source")
        srcdir.chdir()

        assert srcdir.join(".git").check()

        if git_user_email() is None:
            run("git config user.email %s" % GIT_USER_EMAIL)
        if git_user_name() is None:
            run("git config user.name %s" % GIT_USER_NAME)

        reset()

        return srcdir
