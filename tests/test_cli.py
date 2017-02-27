
import pytest

import github_release as ghr

from . import push_argv


@pytest.mark.parametrize("command,action,args", [
    # asset
    # ("asset", "upload", []),
    ("asset", "upload", ["1.0.0", "dist/foo"]),
    # ("asset", "download", []),
    ("asset", "download", ["1.0.0"]),
    ("asset", "download", ["1.0.0", "dist/foo"]),
    ("asset", "delete", ["1.0.0", "*foo*"]),
    ("asset", "delete", ["1.0.0", "*foo*", "--keep-pattern", "*bar*"]),
    ("asset", "delete", ["1.0.0", "*foo*"]),
    ("asset", "delete", ["1.0.0", "*foo*", "--keep-pattern", "*bar*"]),
    # # ref
    ("ref", "create", ["tags/1.0.0", "1234567"]),
    ("ref", "delete", ["tags/1.0.0"]),
    ("ref", "delete", ["tags/1*", "--tags"]),
    ("ref", "delete", ["tags/1.0.0", "--tags", "--keep-pattern", "*1*"]),
    ("ref", "delete", ["tags/1.0.0", "--keep-pattern", "*1*"]),
    ("ref", "list", []),
    ("ref", "list", ["--tags"]),
    ("ref", "list", ["--tags", "--pattern", "*heads/*foo*"]),
    ("ref", "list", ["--pattern", "*heads/*foo*"]),
    # # release
    ("release", "list", []),
    ("release", "info", ["1.0.0"]),
    ("release", "create", ["1.0.0"]),
    ("release", "create", ["1.0.0", "*foo*"]),
    ("release", "create", ["1.0.0", "--name", "name"]),
    ("release", "create", ["1.0.0", "--name", "name", "*foo*"]),
    ("release", "create", ["1.0.0", "--publish"]),
    ("release", "create", ["1.0.0", "--prerelease"]),
    ("release", "create", ["1.0.0", "--target-commitish", "1234567"]),
    ("release", "edit", ["1.0.0", "--tag-name", "new_tag"]),
    ("release", "edit", ["1.0.0", "--target-commitish", "1234567"]),
    ("release", "edit", ["1.0.0", "--name", "new_name"]),
    ("release", "edit", ["1.0.0", "--body", "new_body"]),
    ("release", "edit", ["1.0.0", "--draft"]),
    ("release", "edit", ["1.0.0", "--prerelease"]),
    ("release", "edit", ["1.0.0", "--tag-name", "new_tag",
                                  "--target-commitish", "1234567",
                                  "--name", "new_name",
                                  "--body", "new_body"]),
    ("release", "delete", ["1.0.0"]),
    ("release", "delete", ["*a", "--keep-pattern", "1*"]),
    ("release", "publish", ["1.0.0"]),
    ("release", "publish", ["1.0.0", "--prerelease"]),
    ("release", "unpublish", ["1.0.0"]),
    ("release", "unpublish", ["1.0.0", "--prerelease"]),
    ("release", "release-notes", ["1.0.0"]),
])
def test_cli_arguments(mocker, command, action, args):

    command_dict = getattr(ghr, "%s_COMMANDS" % command.upper())

    def mocked_action(*action_args, **action_kwargs):
        pass

    mocked_action.description = command_dict[action].description
    mocker.patch.dict(command_dict, {action: mocked_action})
    args.insert(0, action)
    args.insert(0, "org/user")
    args.insert(0, command)
    args.insert(0, "githubrelease")
    with push_argv(args):
        ghr.main()
