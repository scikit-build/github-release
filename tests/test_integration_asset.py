
from . import (
    check_releases,
    clear_github_release_and_tags,
    github_token_required,
    integration_test_repo_name_required,
    push_dir,
    REPO_NAME
)

import github_release as ghr


def _create_asset(_dir, _name):
    _dir.ensure(_name).write(_name)


@github_token_required
@integration_test_repo_name_required
def test_upload(tmpdir):
    clear_github_release_and_tags()

    tag_name = "0.1.0"

    ghr.gh_release_create(
        REPO_NAME, tag_name, publish=True
    )

    dist_dir = tmpdir.ensure("dist", dir=True)
    _create_asset(dist_dir, "asset_1")
    _create_asset(dist_dir, "asset_2")
    _create_asset(dist_dir, "asset_3")

    with push_dir(tmpdir):
        ghr.gh_asset_upload(REPO_NAME, tag_name, "dist/asset_1")

    assert (check_releases([
        {"tag_name": tag_name,
         "package_pattern": [
             (1, "asset_1"),
         ]}
    ]))

    with push_dir(tmpdir):
        ghr.gh_asset_upload(
            REPO_NAME, tag_name, ["dist/asset_*", "dist/asset_1"])

    assert (check_releases([
        {"tag_name": tag_name,
         "package_pattern": [
             (3, "asset_*"),
         ]}
    ]))


@github_token_required
@integration_test_repo_name_required
def test_delete_simple(tmpdir):
    clear_github_release_and_tags()

    tag_name = "0.1.0"

    ghr.gh_release_create(
        REPO_NAME, tag_name, publish=True
    )

    dist_dir = tmpdir.ensure("dist", dir=True)
    _create_asset(dist_dir, "asset_1_foo")
    _create_asset(dist_dir, "asset_2_foo")
    _create_asset(dist_dir, "asset_3_foo")
    _create_asset(dist_dir, "asset_1_bar")
    _create_asset(dist_dir, "asset_2_bar")
    _create_asset(dist_dir, "asset_3_bar")

    with push_dir(tmpdir):
        ghr.gh_asset_upload(REPO_NAME, tag_name, "dist/*")

    ghr.gh_asset_delete(REPO_NAME, tag_name, "asset_2_foo")

    assert (check_releases([
        {"tag_name": tag_name,
         "package_pattern": [
             (1, "asset_1_foo"),
             (1, "asset_3_foo"),
             (3, "asset_*_bar"),
         ]}
    ]))

    ghr.gh_asset_delete(REPO_NAME, tag_name, "asset_*_bar")

    assert (check_releases([
        {"tag_name": tag_name,
         "package_pattern": [
             (1, "asset_1_foo"),
             (1, "asset_3_foo"),
         ]}
    ]))


@github_token_required
@integration_test_repo_name_required
def test_delete_keep_pattern(tmpdir):
    clear_github_release_and_tags()

    tag_name = "1.0.0"

    ghr.gh_release_create(
        REPO_NAME, tag_name, publish=True
    )

    dist_dir = tmpdir.ensure("dist", dir=True)
    for asset_name in """
awesome-{tag_name}.dev1-cp27-cp27m-macosx_10_11_x86_64.whl
awesome-{tag_name}.dev1-cp27-cp27m-manylinux1_x86_64.whl
awesome-{tag_name}.dev1-cp27-cp27m-win_amd64.whl

awesome-{tag_name}.dev1-cp36-cp36m-macosx_10_11_x86_64.whl
awesome-{tag_name}.dev1-cp36-cp36m-manylinux1_x86_64.whl
awesome-{tag_name}.dev1-cp36-cp36m-win_amd64.whl

awesome-{tag_name}.dev2-cp27-cp27m-macosx_10_11_x86_64.whl
awesome-{tag_name}.dev2-cp27-cp27m-manylinux1_x86_64.whl
awesome-{tag_name}.dev2-cp27-cp27m-win_amd64.whl

awesome-{tag_name}.dev2-cp36-cp36m-macosx_10_11_x86_64.whl
awesome-{tag_name}.dev2-cp36-cp36m-manylinux1_x86_64.whl
awesome-{tag_name}.dev2-cp36-cp36m-win_amd64.whl
    """.strip().format(tag_name=tag_name).splitlines():
        if not asset_name:
            continue
        _create_asset(dist_dir, asset_name)

    with push_dir(tmpdir):
        ghr.gh_asset_upload(REPO_NAME, tag_name, "dist/*")

    assert (check_releases([
        {"tag_name": tag_name,
         "package_pattern": [
             (12, "*"),
         ]}
    ]))

    ghr.gh_asset_delete(REPO_NAME, tag_name,
                        "awesome*manylinux1*",
                        keep_pattern="awesome*dev2*")

    assert (check_releases([
        {"tag_name": tag_name,
         "package_pattern": [
             (10, "*"),
             (2, "awesome-%s.dev1*macosx*" % tag_name),
             (2, "awesome-%s.dev1*win*" % tag_name),
             (6, "awesome-%s.dev2*" % tag_name),
         ]}
    ]))


def _download_test_prerequisites(tmpdir):
    clear_github_release_and_tags()

    ghr.gh_release_create(
        REPO_NAME, "1.0.0", publish=True
    )
    ghr.gh_release_create(
        REPO_NAME, "2.0.0", publish=True
    )

    dist_dir = tmpdir.ensure("dist", dir=True)
    _create_asset(dist_dir, "asset_1_a")
    _create_asset(dist_dir, "asset_1_boo")
    _create_asset(dist_dir, "asset_1_bar")
    _create_asset(dist_dir, "asset_2_a")
    _create_asset(dist_dir, "asset_2_boo")
    _create_asset(dist_dir, "asset_2_bar")

    with push_dir(tmpdir):
        ghr.gh_asset_upload(REPO_NAME, "1.0.0", "dist/asset_1_*")
        ghr.gh_asset_upload(REPO_NAME, "2.0.0", "dist/asset_2_*")


@github_token_required
@integration_test_repo_name_required
def test_download_all(tmpdir):
    _download_test_prerequisites(tmpdir)

    with push_dir(tmpdir):
        download_count = ghr.gh_asset_download(REPO_NAME)
        assert download_count == 6

    for asset_name in [
        "asset_1_a", "asset_1_boo", "asset_1_bar",
        "asset_2_a", "asset_2_boo", "asset_2_bar"
    ]:
        asset_file = tmpdir.join(asset_name)
        assert asset_file.check()
        assert asset_file.read() == asset_name


@github_token_required
@integration_test_repo_name_required
def test_download_all_tag(tmpdir):
    _download_test_prerequisites(tmpdir)

    with push_dir(tmpdir):
        download_count = ghr.gh_asset_download(REPO_NAME, "2.0.0")
        assert download_count == 3

    for asset_name in ["asset_2_a", "asset_2_boo", "asset_2_bar"]:
        asset_file = tmpdir.join(asset_name)
        assert asset_file.check()
        assert asset_file.read() == asset_name


@github_token_required
@integration_test_repo_name_required
def test_download_all_pattern(tmpdir):
    _download_test_prerequisites(tmpdir)

    with push_dir(tmpdir):
        download_count = ghr.gh_asset_download(REPO_NAME, pattern="*_b*")
        assert download_count == 4

    for asset_name in [
        "asset_1_boo", "asset_1_bar",
        "asset_2_boo", "asset_2_bar"
    ]:
        asset_file = tmpdir.join(asset_name)
        assert asset_file.check()
        assert asset_file.read() == asset_name


@github_token_required
@integration_test_repo_name_required
def test_download_tag_pattern(tmpdir):
    _download_test_prerequisites(tmpdir)

    with push_dir(tmpdir):
        download_count = ghr.gh_asset_download(
            REPO_NAME, tag_name="2.0.0", pattern="*_b*"
        )
        assert download_count == 2

    for asset_name in [
        "asset_2_boo", "asset_2_bar"
    ]:
        asset_file = tmpdir.join(asset_name)
        assert asset_file.check()
        assert asset_file.read() == asset_name


@github_token_required
@integration_test_repo_name_required
def test_download_twice(tmpdir):
    _download_test_prerequisites(tmpdir)

    with push_dir(tmpdir):
        download_count = ghr.gh_asset_download(
            REPO_NAME, tag_name="1.0.0", pattern="asset_1_a"
        )
        assert download_count == 1

        download_count = ghr.gh_asset_download(
            REPO_NAME, tag_name="1.0.0", pattern="asset_1_a"
        )
        assert download_count == 0
