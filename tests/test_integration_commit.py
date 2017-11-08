
from . import (
    do_commit,
    github_token_required,
    git_user_email_required,
    git_user_name_required,
    integration_test_repo_name_required,
    push_dir,
    REPO_NAME
)

import github_release as ghr


@git_user_email_required
@git_user_name_required
@github_token_required
@integration_test_repo_name_required
def test_get(gh_src_dir):
    with push_dir(gh_src_dir):
        expected_sha = do_commit(push=True)
        response = ghr.gh_commit_get(REPO_NAME, expected_sha)
        assert 'sha' in response
        assert response['sha'] == expected_sha

        assert ghr.gh_commit_get(REPO_NAME, "invalid") is None
