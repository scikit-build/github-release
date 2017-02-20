
import pytest

from . import (
    GIT_USER_EMAIL,
    git_user_email,
    GIT_USER_NAME,
    git_user_name,
    push_dir,
    REPO_NAME,
    reset,
    run
)


@pytest.fixture(scope='function')
def gh_src_dir(tmpdir_factory):
    tmp_dir = tmpdir_factory.mktemp("source")
    if git_user_email() is None:
        run("git config --add user.email", GIT_USER_EMAIL)
    if git_user_name() is None:
        run("git config --add user.name", GIT_USER_NAME)
    with push_dir(tmp_dir):
        # clone
        run("git clone https://github.com/%s source" % REPO_NAME)

        srcdir = tmp_dir.join("source")
        srcdir.chdir()

        assert srcdir.join(".git").check()

        reset()

        return srcdir
