
from . import (
    do_commit,
    github_token_required,
    git_user_email_required,
    git_user_name_required,
    integration_test_repo_name_required,
    push_dir,
    REPO_NAME,
    run
)

import github_release as ghr


def _sorted_ref_list(*args, **kwargs):
    return sorted([ref["ref"] for ref in ghr.gh_ref_list(*args, **kwargs)])


@git_user_email_required
@git_user_name_required
@github_token_required
@integration_test_repo_name_required
def test_create(gh_src_dir):
    with push_dir(gh_src_dir):
        expected_refs = {}
        for name in ["0.1.0", "0.2.0"]:
            # tag
            sha = do_commit(push=True)
            ref = "tags/%s" % name
            ghr.gh_ref_create(REPO_NAME, ref, sha)
            expected_refs["refs/%s" % ref] = sha

            # branch
            sha = do_commit(push=True)
            ref = "heads/%s" % name
            ghr.gh_ref_create(REPO_NAME, ref, sha)
            expected_refs["refs/%s" % ref] = sha

            expected_refs["refs/heads/master"] = sha

        refs = {line.split()[1]: line.split()[0]
                for line in run("git ls-remote --tags --heads")}

        assert expected_refs == refs


@git_user_email_required
@git_user_name_required
@github_token_required
@integration_test_repo_name_required
def test_delete_simple(gh_src_dir):
    with push_dir(gh_src_dir):
        ghr.gh_ref_list(REPO_NAME) == ["refs/heads/master"]

        for tag_name in ["0.1.0", "0.2.0", "0.3.0",
                         "0.4.0", "0.4.1"]:
            do_commit(release_tag=tag_name, push=True)

        for branch in ["0.1.0", "0.2.0", "0.3.0",
                       "0.4.0", "0.4.1"]:
            do_commit(branch=branch, push=True)

        # Delete release
        assert ghr.gh_ref_delete(REPO_NAME, "*0.2.0")
        assert _sorted_ref_list(REPO_NAME) == sorted(
            [
                u"refs/tags/0.1.0",
                u"refs/tags/0.3.0",
                u"refs/tags/0.4.0",
                u"refs/tags/0.4.1",
                u"refs/heads/0.1.0",
                u"refs/heads/0.3.0",
                u"refs/heads/0.4.0",
                u"refs/heads/0.4.1",
                u"refs/heads/master",
            ])

        # Delete nonexistent release should gracefully return
        assert not ghr.gh_ref_delete(REPO_NAME, "*0.2.0")
        assert _sorted_ref_list(REPO_NAME) == sorted(
            [
                u"refs/tags/0.1.0",
                u"refs/tags/0.3.0",
                u"refs/tags/0.4.0",
                u"refs/tags/0.4.1",
                u"refs/heads/0.1.0",
                u"refs/heads/0.3.0",
                u"refs/heads/0.4.0",
                u"refs/heads/0.4.1",
                u"refs/heads/master",
            ])

        # Delete release
        assert ghr.gh_ref_delete(REPO_NAME, "*0.3*")
        assert _sorted_ref_list(REPO_NAME) == sorted(
            [
                u"refs/tags/0.1.0",
                u"refs/tags/0.4.0",
                u"refs/tags/0.4.1",
                u"refs/heads/0.1.0",
                u"refs/heads/0.4.0",
                u"refs/heads/0.4.1",
                u"refs/heads/master",
            ])

        # Delete release
        assert ghr.gh_ref_delete(REPO_NAME, "*0.4*")
        assert _sorted_ref_list(REPO_NAME) == sorted(
            [
                u"refs/tags/0.1.0",
                u"refs/heads/0.1.0",
                u"refs/heads/master",
            ])


@git_user_email_required
@git_user_name_required
@github_token_required
@integration_test_repo_name_required
def test_delete_tags(gh_src_dir):
    with push_dir(gh_src_dir):
        ghr.gh_ref_list(REPO_NAME) == ["refs/heads/master"]

        for tag_name in ["0.1.0", "0.2.0", "0.3.0",
                         "0.4.0", "0.4.1"]:
            do_commit(release_tag=tag_name, push=True)

        branches = [u"refs/heads/master"]
        for branch in ["0.1.0", "0.2.0", "0.3.0",
                       "0.4.0", "0.4.1"]:
            do_commit(branch=branch, push=True)
            branches.append(u"refs/heads/%s" % branch)

        # Delete release
        assert ghr.gh_ref_delete(REPO_NAME, "*0.2.0", tags=True)
        assert _sorted_ref_list(REPO_NAME) == sorted(
            [
                u"refs/tags/0.1.0",
                u"refs/tags/0.3.0",
                u"refs/tags/0.4.0",
                u"refs/tags/0.4.1",
            ] + branches)

        # Delete nonexistent release should gracefully return
        assert not ghr.gh_ref_delete(REPO_NAME, "*0.2.0", tags=True)
        assert _sorted_ref_list(REPO_NAME) == sorted(
            [
                u"refs/tags/0.1.0",
                u"refs/tags/0.3.0",
                u"refs/tags/0.4.0",
                u"refs/tags/0.4.1"
            ] + branches)

        # Delete release
        assert ghr.gh_ref_delete(REPO_NAME, "*0.3*", tags=True)
        assert _sorted_ref_list(REPO_NAME) == sorted(
            [
                u"refs/tags/0.1.0",
                u"refs/tags/0.4.0",
                u"refs/tags/0.4.1"
            ] + branches)

        # Delete release
        assert ghr.gh_ref_delete(REPO_NAME, "*0.4*", tags=True)
        assert _sorted_ref_list(REPO_NAME) == sorted(
            [
                u"refs/tags/0.1.0"
            ] + branches)


@git_user_email_required
@git_user_name_required
@github_token_required
@integration_test_repo_name_required
def test_delete_keep_pattern(gh_src_dir):
    with push_dir(gh_src_dir):
        _sorted_ref_list(REPO_NAME) == ["refs/heads/master"]

        for tag_name in ["0.0.0", "0.0.1",
                         "1.0.0", "1.0.1",
                         "1.1.0", "1.1.1"]:
            do_commit(release_tag=tag_name, push=True)

        for branch in ["br-0.0.0", "br-0.0.1",
                       "br-1.0.0", "br-1.0.1",
                       "br-1.1.0", "br-1.1.1"]:
            do_commit(branch=branch, push=True)

        # Delete all "1.*" tag references expect the one matching "*1.1.*"
        assert ghr.gh_ref_delete(
            REPO_NAME, "*1.*", tags=True, keep_pattern="*1.1.*")
        assert _sorted_ref_list(REPO_NAME,
                                tags=True) == sorted(
            [
                u"refs/tags/0.0.0",
                u"refs/tags/0.0.1",
                u"refs/tags/1.1.0",
                u"refs/tags/1.1.1"
            ])

        # Delete all "*br-1.*" branch or tag references expect the one
        # matching "*br-1.1.*"
        assert ghr.gh_ref_delete(
            REPO_NAME, "*br-1.*", keep_pattern="*br-1.1.*")
        assert _sorted_ref_list(REPO_NAME) == sorted(
            [
                u"refs/tags/0.0.0",
                u"refs/tags/0.0.1",
                u"refs/tags/1.1.0",
                u"refs/tags/1.1.1",
                u"refs/heads/br-0.0.0",
                u"refs/heads/br-0.0.1",
                u"refs/heads/br-1.1.0",
                u"refs/heads/br-1.1.1",
                u"refs/heads/master"
            ])


@git_user_email_required
@git_user_name_required
@github_token_required
@integration_test_repo_name_required
def test_list(gh_src_dir):
    # gh_src_dir = "/tmp/pytest-of-jcfr/pytest-74/source4/source"
    with push_dir(gh_src_dir):
        assert _sorted_ref_list(REPO_NAME) == ["refs/heads/master"]

        do_commit(release_tag="1.0.0", push=True)  # 2017-01-02
        do_commit(release_tag="1.1.0", push=True)  # 2017-01-03
        do_commit(release_tag="1.1.1", push=True)  # 2017-01-04
        do_commit(branch="maint-1.1.x", push=True)  # 2017-01-05
        do_commit(release_tag="2.0.0", push=True)  # 2017-01-06

        assert _sorted_ref_list(REPO_NAME) == sorted(
            [
                u"refs/heads/master",
                u"refs/heads/maint-1.1.x",
                u"refs/tags/1.0.0",
                u"refs/tags/1.1.0",
                u"refs/tags/1.1.1",
                u"refs/tags/2.0.0"
            ])

        assert _sorted_ref_list(REPO_NAME,
                                pattern="*1.1*") == sorted(
            [
                u"refs/heads/maint-1.1.x",
                u"refs/tags/1.1.0",
                u"refs/tags/1.1.1"
            ])

        assert _sorted_ref_list(REPO_NAME, pattern="*1.1*",
                                tags=True) == sorted(
            [
                u"refs/tags/1.1.0", u"refs/tags/1.1.1"
            ])

        assert _sorted_ref_list(REPO_NAME, tags=True) == sorted(
            [
                u"refs/tags/1.0.0",
                u"refs/tags/1.1.0",
                u"refs/tags/1.1.1",
                u"refs/tags/2.0.0"
            ])
