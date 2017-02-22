
import pytest

import github_release as ghr

from . import push_argv


@pytest.mark.parametrize("command,action,args", [
    # asset
    # ("asset", "upload", ["asset", "org/user"]),
    # ("asset", "upload", ["asset", "org/user", "upload"]),
    ("asset", "upload", ["asset", "org/user", "upload", "1.0.0", "dist/foo"]),
    # ("asset", "download", ["asset", "org/user"]),
    ("asset", "download", ["asset", "org/user", "download", "--tag_name", "1.0.0"]),
    ("asset", "download", ["asset", "org/user", "download", "--tag_name", "1.0.0", "--pattern", "dist/foo"]),
    ("asset", "delete", ["asset", "org/user", "delete", "1.0.0", "*foo*"]),
    ("asset", "delete", ["asset", "org/user", "delete", "1.0.0", "*foo*", "--keep-pattern", "*bar*"]),
    # # ref
    ("ref", "create", ["ref", "org/user", "create", "tags/1.0.0", "1234567"]),
    ("ref", "delete", ["ref", "org/user", "delete", "tags/1.0.0"]),
    ("ref", "delete", ["ref", "org/user", "delete", "tags/1*", "--tags"]),
    ("ref", "delete", ["ref", "org/user", "delete", "tags/1.0.0", "--tags", "--keep-pattern", "*1*"]),
    ("ref", "delete", ["ref", "org/user", "delete", "tags/1.0.0", "--keep-pattern", "*1*"]),
    ("ref", "list", ["ref", "org/user", "list"]),
    ("ref", "list", ["ref", "org/user", "list", "--tags"]),
    ("ref", "list", ["ref", "org/user", "list", "--tags", "--pattern", "*heads/*foo*"]),
    ("ref", "list", ["ref", "org/user", "list", "--pattern", "*heads/*foo*"]),
    # # release
    ("release", "list", ["release", "org/user", "list"]),
    ("release", "info", ["release", "org/user", "info", "1.0.0"]),
    ("release", "create", ["release", "org/user", "create", "1.0.0"]),
    ("release", "create", ["release", "org/user", "create", "1.0.0", "--name", "name"]),
    ("release", "create", ["release", "org/user", "create", "1.0.0", "--publish"]),
    ("release", "create", ["release", "org/user", "create", "1.0.0", "--prerelease"]),
    ("release", "create", ["release", "org/user", "create", "1.0.0", "--target_commitish", "1234567"]),
    ("release", "edit", ["release", "org/user", "edit", "1.0.0", "--tag_name", "new_tag"]),
    ("release", "edit", ["release", "org/user", "edit", "1.0.0", "--target_commitish", "1234567"]),
    ("release", "edit", ["release", "org/user", "edit", "1.0.0", "--name", "new_name"]),
    ("release", "edit", ["release", "org/user", "edit", "1.0.0", "--body", "new_body"]),
    ("release", "edit", ["release", "org/user", "edit", "1.0.0", "--draft"]),
    ("release", "edit", ["release", "org/user", "edit", "1.0.0", "--prerelease"]),
    ("release", "edit", ["release", "org/user", "edit", "1.0.0", "--tag_name", "new_tag",
                                                                 "--target_commitish", "1234567",
                                                                 "--name", "new_name",
                                                                 "--body", "new_body"]),
    ("release", "delete", ["release", "org/user", "delete", "1.0.0"]),
    ("release", "delete", ["release", "org/user", "delete", "*a", "--keep-pattern", "1*"]),
    ("release", "publish", ["release", "org/user", "publish", "1.0.0"]),
    ("release", "publish", ["release", "org/user", "publish", "1.0.0", "--prerelease"]),
    ("release", "unpublish", ["release", "org/user", "unpublish", "1.0.0"]),
    ("release", "unpublish", ["release", "org/user", "unpublish", "1.0.0", "--prerelease"]),
    ("release", "release-notes", ["release", "org/user", "release-notes", "1.0.0"]),
])
def test_cli_arguments(mocker, command, action, args):

    command_dict = getattr(ghr, "%s_COMMANDS" % command.upper())

    def mocked_action(*action_args, **action_kwargs):
        pass

    mocked_action.description = command_dict[action].description
    mocker.patch.dict(command_dict, {action: mocked_action})
    args.insert(0, "githubrelease")
    with push_argv(args):
        ghr.main()
