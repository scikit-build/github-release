
from . import (
    check_releases,
    clear_github_release_and_tags,
    github_token_required,
    integration_test_repo_name_required,
    REPO_NAME
)

import github_release as ghr


@github_token_required
@integration_test_repo_name_required
def test_delete_simple():
    clear_github_release_and_tags()

    # Create release
    for tag_name in ["0.1.0", "0.2.0", "0.3.0", "0.4.0", "0.4.1"]:
        ghr.gh_release_create(
            REPO_NAME, tag_name, publish=True
        )
    assert (check_releases([
        {"tag_name": "0.1.0"},
        {"tag_name": "0.2.0"},
        {"tag_name": "0.3.0"},
        {"tag_name": "0.4.0"},
        {"tag_name": "0.4.1"},
    ]))

    # Delete release
    assert ghr.gh_release_delete(REPO_NAME, "0.2.0")
    assert (check_releases([
        {"tag_name": "0.1.0"},
        {"tag_name": "0.3.0"},
        {"tag_name": "0.4.0"},
        {"tag_name": "0.4.1"},
    ]))

    # Delete nonexistent release should gracefully return
    assert not ghr.gh_release_delete(REPO_NAME, "0.2.0")
    assert (check_releases([
        {"tag_name": "0.1.0"},
        {"tag_name": "0.3.0"},
        {"tag_name": "0.4.0"},
        {"tag_name": "0.4.1"},
    ]))

    # Delete release
    assert ghr.gh_release_delete(REPO_NAME, "*0.3*")
    assert (check_releases([
        {"tag_name": "0.1.0"},
        {"tag_name": "0.4.0"},
        {"tag_name": "0.4.1"},
    ]))

    # Delete release
    assert ghr.gh_release_delete(REPO_NAME, "*0.4*")
    assert (check_releases([
        {"tag_name": "0.1.0"},
    ]))


@github_token_required
@integration_test_repo_name_required
def test_delete_keep_pattern():
    clear_github_release_and_tags()

    # Create release
    for tag_name in ["0.0.0", "0.0.1",
                     "1.0.0", "1.0.1",
                     "1.1.0", "1.1.1"]:
        ghr.gh_release_create(
            REPO_NAME, tag_name, publish=True
        )

    # Delete all "1.*" releases expect the one matching "1.1.*"
    assert ghr.gh_release_delete(REPO_NAME, "1.*", keep_pattern="1.1.*")
    assert (check_releases([
        {"tag_name": "0.0.0"},
        {"tag_name": "0.0.1"},
        {"tag_name": "1.1.0"},
        {"tag_name": "1.1.1"},
    ]))
