
import os
import random
import string

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


@pytest.fixture(scope='function')
def release_name(request):
    prefix = "".join(token[0] for token in request.node.originalname.split("_"))

    rnd = ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(6))

    return "%s-%s-0.1.0" % (prefix, rnd)
