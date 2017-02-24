
import pytest

from . import (
    check_releases,
    clear_github_release_and_tags,
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


@github_token_required
@integration_test_repo_name_required
@pytest.mark.parametrize("release_type", ['draft', 'prerelease', 'release'])
def test_edit_tag_name(release_type):
    clear_github_release_and_tags()

    cases = {
        'draft': {"draft": True, "prerelease": False},
        'prerelease': {"draft": False, "prerelease": True},
        'release': {"draft": False, "prerelease": False}
    }

    params = cases[release_type]

    # Create release
    ghr.gh_release_create(
        REPO_NAME, "0.1.0",
        prerelease=params["prerelease"],
        publish=not params["prerelease"] and not params["draft"]
    )

    assert (check_releases([
        {"tag_name": "0.1.0",
         "draft": params["draft"],
         "prerelease": params["prerelease"]}
    ]))

    # Edit release
    ghr.gh_release_edit(REPO_NAME, "0.1.0", tag_name="0.1.0-edited")

    assert (check_releases([
        {"tag_name": "0.1.0-edited",
         "draft": params["draft"],
         "prerelease": params["prerelease"]},
    ]))


@git_user_email_required
@git_user_name_required
@github_token_required
@integration_test_repo_name_required
@pytest.mark.parametrize("release_type", ['draft', 'prerelease', 'release'])
def test_edit_target_commitish(gh_src_dir, release_type):
    cases = {
        'draft': {"draft": True, "prerelease": False},
        'prerelease': {"draft": False, "prerelease": True},
        'release': {"draft": False, "prerelease": False}
    }

    params = cases[release_type]

    with push_dir(gh_src_dir):
        sha = do_commit()  # 2017-01-02
        do_commit(push=True)  # 2017-01-03

        # Create release
        ghr.gh_release_create(
            REPO_NAME, "0.1.0",
            prerelease=params["prerelease"],
            publish=not params["prerelease"] and not params["draft"]
        )

        run("git fetch origin")
        run("git fetch origin --tags")

        assert (check_releases([
            {"tag_name": "0.1.0",
             "draft": params["draft"],
             "prerelease": params["prerelease"],
             "tag_date": "20170103"}
        ]))

        # Edit release
        ghr.gh_release_edit(
            REPO_NAME, "0.1.0",
            target_commitish=sha
        )

        run("git fetch origin")
        run("git fetch origin --tags")

        assert (check_releases([
            {"tag_name": "0.1.0",
             "draft": params["draft"],
             "prerelease": params["prerelease"],
             "tag_date": "20170102"
             }
        ]))


@github_token_required
@integration_test_repo_name_required
@pytest.mark.parametrize("release_type", ['draft', 'prerelease', 'release'])
def test_edit_name_and_body(release_type):
    clear_github_release_and_tags()

    cases = {
        'draft': {"draft": True, "prerelease": False},
        'prerelease': {"draft": False, "prerelease": True},
        'release': {"draft": False, "prerelease": False}
    }

    params = cases[release_type]

    # Create release
    ghr.gh_release_create(
        REPO_NAME, "0.1.0",
        prerelease=params["prerelease"],
        publish=not params["prerelease"] and not params["draft"]
    )

    assert (check_releases([
        {"tag_name": "0.1.0",
         "draft": params["draft"],
         "prerelease": params["prerelease"]}
    ]))

    # Edit release
    ghr.gh_release_edit(
        REPO_NAME, "0.1.0",
        name="name-edited", body="body-edited"
    )

    assert (check_releases([
        {"tag_name": "0.1.0",
         "draft": params["draft"],
         "prerelease": params["prerelease"],
         "name": "name-edited",
         "body": "body-edited"},
    ]))


@github_token_required
@integration_test_repo_name_required
@pytest.mark.parametrize("from_release_type",
                         ['draft', 'prerelease', 'release'])
@pytest.mark.parametrize("to_release_type",
                         ['draft', 'prerelease', 'release'])
def test_edit_release_type(from_release_type, to_release_type):
    clear_github_release_and_tags()

    cases = {
        'draft': {"draft": True, "prerelease": False},
        'prerelease': {"draft": False, "prerelease": True},
        'release': {"draft": False, "prerelease": False}
    }

    if from_release_type == to_release_type:
        pytest.skip("from_release_type is identical to "
                    "to_release_type: %s" % to_release_type)

    from_params = cases[from_release_type]
    to_params = cases[to_release_type]

    # Create release
    ghr.gh_release_create(
        REPO_NAME, "0.1.0",
        prerelease=from_params["prerelease"],
        publish=not from_params["prerelease"] and not from_params["draft"]
    )

    assert (check_releases([
        {"tag_name": "0.1.0",
         "draft": from_params["draft"],
         "prerelease": from_params["prerelease"]}
    ]))

    # Edit release
    ghr.gh_release_edit(
        REPO_NAME, "0.1.0", **to_params
    )

    assert (check_releases([
        {"tag_name": "0.1.0",
         "draft": to_params["draft"],
         "prerelease": to_params["prerelease"]},
    ]))
