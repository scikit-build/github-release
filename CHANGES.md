1.5.7
=====

Features (CLI and Python API)
-----------------------------

* ``release`` command:

  * ``edit``:

    * Add ``--publish`` flag having opposite effect of ``--draft``
    * Add ``--release`` flag having opposite effect of ``--prerelease``

Python API
----------

* Add ``gh_commit_get`` allowing to commit properties or check if a commit exists.

1.5.6
=====

Issues (CLI and Python API)
---------------------------

* ``release`` command:

  * ``edit``: If any, remove leftover temporary tag and
    avoid ``Release with tag_name latest-tmp not found`` exception.


1.5.5
=====

Features (CLI and Python API)
-----------------------------

* Support projects having more than 30 assets, releases or refs.

  * Introduce dependency to [LinkHeader](https://pypi.python.org/pypi/LinkHeader/) python
    package to handle [GitHub pagination information](https://developer.github.com/v3/guides/traversing-with-pagination/).


1.5.4
=====

Features (CLI and Python API)
-----------------------------

* ``ref`` command:

  * ``list``: Consolidate tags listing using [refs and refs/tags](https://developer.github.com/v3/git/refs/#get-all-references)
    endpoints. In practice, we observed that tags can be listed with one or the other.


1.5.3
=====

Python API
----------

* Update ``gh_ref_delete`` to return True if references were removed.

* Ensure ``gh_ref_list`` return list of references.

Testing
-------

* Add test for references.

1.5.2
=====

Features (CLI and Python API)
-----------------------------

* ``asset`` command:

  * ``list``:

    * Explicitly support listing of release assets. This will list assets independently of
      their state (*uploaded* or *new*).

    * If an asset has its state set to *new*, it means a problem occurred during a previous
    upload and the asset can safely be deleted. See [here](https://developer.github.com/v3/repos/releases/#response-for-upstream-failure)
    for more details.

  * ``delete``:

    * Support deleting asset independently of their state.

  * ``upload``:

    * Automatically delete existing asset if name matches and if its
      state is "new". This will happen if a previous upload was interrupted
      and the asset on the server has been created but is incomplete.

    * Retry to upload if server returns a 502 error.

1.5.1
=====

CLI
---

* In addition of setting `GITHUB_TOKEN` environment variable or using `netrc` file, the CLI
  now accepts a ``--github-token`` argument. More details [here](https://github.com/j0057/github-release/blob/master/README.md#configuring).

* If called from a terminal, report download or upload progress. Passing ``--no-progress``
  allows to explicitly disable progress reporting.

* Fix asset download command argument parsing. `tag_name` and `pattern` are
  effectively optional positional arguments.

* ``asset`` command:

  * ``upload``: Support upload of multiple files or globing patterns

* Deprecate asset erase command. It doesn't show up in the help and usage
  output. It will be removed in version 1.6.0.

* Backward incompatible changes:

  * Consistently accept ``--keep-pattern`` instead of ``--keep_pattern``.

  * Change ``--tag_name`` into ``--tag-name``.

  * Change ``--target_commitish`` into ``--target-commitish``.

Features (CLI and Python API)
-----------------------------

* Check that credentials (either `GITHUB_TOKEN` environment variable or `netrc` file)
  are properly set for commands requiring them. Thanks [@rwols](https://github.com/rwols)
  for suggesting the change. See [PR #17](https://github.com/j0057/github-release/pull/17).

* ``release`` command:

  * ``create``:

    * Support upload of arbitrary number of assets on release creation.

    * Support ``--dry-run``.

Python API
----------

* Backward incompatible changes:

  * Rename ``gh_asset_erase`` into ``gh_asset_delete``.

* Internal

  * Simplify code using [click](http://pocco-click.readthedocs.io) for argument parsing.

Testing
-------

* Add test checking that expected command line arguments do not cause failure.

* Completely ignore 4xx errors associated with ``clear_github_release_and_tags``.

* Relocate test repositories under [github-release-bot](https://github.com/github-release-bot) user.

Build System
------------

* Latest packages are now published

  * Packages generated from master branch are available at https://github.com/j0057/github-release/releases/tag/latest

  * They can be installed using `pip intall githubrelease -f https://github.com/j0057/github-release/releases/tag/latest`

Documentation
-------------

* Update [maintainers: how to make a release ?](https://github.com/j0057/github-release/blob/master/README.md#maintainers-how-to-make-a-release-) section
  to include update of *CHANGES.md* and creation of a [github release](https://github.com/j0057/github-release/releases).

1.5.0
=====

This release is a significant milestone in the project.

It improves ``release`` management by supporting update of the tag associated
with an existing release.
 
It improves the ``erase`` command supporting ``--keep-pattern``. This allows
to exclude a subset of the packages already matched by the provided selection 
``pattern``.

It drastically improves the command-line user experience (support ``--help``) and
the documentation.

It also adds a new ``reference`` command to create, delete and list tags
and branches.

In addition of the original author [@j0057](https://github.com/j0057), the core
team now includes [@jcfr](https://github.com/jcfr).

License
-------

* Associate code with [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0.html)
  license. See [PR #7](https://github.com/j0057/github-release/pull/7).
  
Features (CLI)
-------------

* Distribute a new executable ``githubrelease`` allowing to invoke any
  command (e.g ``release``, ``asset``, ...) from a unified interface.

* Significantly improve the user experience by adding first class
  support for argument parsing. ``--help`` argument is now available.
  Fix issue [#2](https://github.com/j0057/github-release/issue/2).

Features (CLI and Python API)
-----------------------------

The changes listed below apply to both the command line interface and the
Python API.

* Support authentication through ``GITHUB_TOKEN``.
  
* Add support for release ``edit`` with summary of changed attributes.

* Add support for listing/creating/deleting references

* Improve logging associated with release, assets and references.

* Add support for `--verbose` and `--dry-run` for most of the commands.

* ``release`` command:

  * ``create``:
 
    * Support optional parameter `--prerelease`. This allows to directly create a pre-release.

    * Support optional parameter `--publish`. This allows to directly create a published release.
   
    * Gracefully return if release already exists.
   
    * Support optional parameter `--target_commitish`.
 
  * ``publish``: Support additional parameter `--prerelease`.
 
  * ``unpublish``: Support additional parameter `--prerelease`.
  
  * ``list``: Display `download_count`.


* ``asset`` command:

  * ``erase``: 
  
    * Display a message if no files matching `pattern` are found.
 
    * Add support for optional argument `--keep-pattern`.
      When specified, matching packages will be excluded from the subset
      already matched by the provided selection ``pattern``.

  * ``upload``:
  
    * Gracefully handle already uploaded assets having the same name.
 
    * Display `browser_download_url` returned by GitHub API.

Features (Python API)
---------------------

The changes listed below apply to only the Python API.

* ``asset`` command: Add support for list of patterns.

Backward compatibility
----------------------

* Executables `github-release` and `github-asset` have been
  deprecated but are still distributed.

Build System
------------

* Setup continuous integration on TravisCI to run style and integration
  tests with each pull requests.

* Clean and simplify ``setup.py``.

* Add ``setuptools-version-command`` to `requirements-dev.txt`.

* Add `setup.cfg` to mark the wheels as `universal`.


Documentation
-------------

* Re-organize and improve [README.md](https://github.com/j0057/github-release/blob/master/README.md#table-of-contents).

* Add [maintainers: how to make a release ?](https://github.com/j0057/github-release/blob/master/README.md#maintainers-how-to-make-a-release-) section.

* Add [CONTRIBUTING](https://github.com/j0057/github-release/blob/master/CONTRIBUTING.md#contributing) guidelines.
