
import pytest


def test_main():
    import github_release as ghr
    with pytest.raises(SystemExit) as exc_info:
        ghr.main()
        assert exc_info.code == 0
