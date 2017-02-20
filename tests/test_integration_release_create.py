
from . import (
    check_releases,
    do_commit,
    git_user_email_required,
    git_user_name_required,
    github_token_required,
    integration_test_repo_name_required,
    push_dir,
    REPO_NAME,
    run
)

import github_release as ghr


@git_user_email_required
@git_user_name_required
@github_token_required
@integration_test_repo_name_required
def test_create_default(gh_src_dir):
    with push_dir(gh_src_dir):
        do_commit(push=True)  # 2017-01-02

        # Create release
        ghr.gh_release_create(
            REPO_NAME, "0.1.0"
        )

        # Fetch changes
        run("git fetch origin")

        assert (check_releases([
            {"tag_name": "0.1.0",
             "draft": True, "prerelease": False},
        ]))


@git_user_email_required
@git_user_name_required
@github_token_required
@integration_test_repo_name_required
def test_create_prerelease(gh_src_dir):
    with push_dir(gh_src_dir):
        do_commit(push=True)  # 2017-01-02

        # Create release
        ghr.gh_release_create(
            REPO_NAME, "0.1.0", prerelease=True
        )

        # Fetch changes
        run("git fetch origin")

        assert (check_releases([
            {"tag_name": "0.1.0", "tag_date": "20170102",
             "draft": False, "prerelease": True},
        ]))


@git_user_email_required
@git_user_name_required
@github_token_required
@integration_test_repo_name_required
def test_create_release(gh_src_dir):
    with push_dir(gh_src_dir):
        do_commit(push=True)  # 2017-01-02

        # Create release
        ghr.gh_release_create(
            REPO_NAME, "0.1.0", publish=True
        )

        # Fetch changes
        run("git fetch origin")

        assert (check_releases([
            {"tag_name": "0.1.0", "tag_date": "20170102",
             "draft": False, "prerelease": False},
        ]))


@git_user_email_required
@git_user_name_required
@github_token_required
@integration_test_repo_name_required
def test_create_release_custom_name(gh_src_dir):
    with push_dir(gh_src_dir):
        do_commit(push=True)  # 2017-01-02

        # Create release
        ghr.gh_release_create(
            REPO_NAME, "0.1.0", publish=True, name="Awesome"
        )

        # Fetch changes
        run("git fetch origin")

        assert (check_releases([
            {"tag_name": "0.1.0", "name": "Awesome", "tag_date": "20170102",
             "draft": False, "prerelease": False},
        ]))


@git_user_email_required
@git_user_name_required
@github_token_required
@integration_test_repo_name_required
def test_create_prerelease_target_commitish(gh_src_dir):
    with push_dir(gh_src_dir):
        do_commit()  # 2017-01-02
        sha = do_commit()  # 2017-01-03
        do_commit(push=True)  # 2017-01-04

        # Create release
        ghr.gh_release_create(
            REPO_NAME, "0.1.0", prerelease=True, target_commitish=sha
        )

        # Fetch changes
        run("git fetch origin")

        assert (check_releases([
            {"tag_name": "0.1.0", "tag_date": "20170103",
             "draft": False, "prerelease": True},
        ]))


@git_user_email_required
@git_user_name_required
@github_token_required
@integration_test_repo_name_required
def test_create_release_target_commitish(gh_src_dir):
    with push_dir(gh_src_dir):
        do_commit()  # 2017-01-02
        sha = do_commit()  # 2017-01-03
        do_commit(push=True)  # 2017-01-04

        # Create release
        ghr.gh_release_create(
            REPO_NAME, "0.1.0", publish=True, target_commitish=sha
        )

        # Fetch changes
        run("git fetch origin")

        assert (check_releases([
            {"tag_name": "0.1.0", "tag_date": "20170103",
             "draft": False, "prerelease": False},
        ]))
