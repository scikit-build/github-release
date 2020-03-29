
import os

import github_release as ghr

from . import push_env, push_github_api_url


def test_github_api_url():
    with push_github_api_url(ghr, None):
        assert ghr._github_api_url is None

        url = 'https://api.github.com'
        assert ghr.github_api_url() == url
        ghr.set_github_api_url(url)
        assert ghr._github_api_url == url
        assert ghr.github_api_url() == url


def test_github_api_url_env():
    with push_env(GITHUB_API_URL=None), push_github_api_url(ghr, None):
        assert ghr._github_api_url is None
        assert 'GITHUB_API_URL' not in os.environ

        url = 'https://api-github.awesome.com'
        os.environ['GITHUB_API_URL'] = url
        assert ghr.github_api_url() == url
        assert ghr._github_api_url != url
