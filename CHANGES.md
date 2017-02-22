Next Release
============

CLI
---

* Fix asset download command argument parsing. `tag_name` and `pattern` are
  effectively optional positional arguments.

* Deprecate asset erase command. It doesn't show up in the help and usage
  output. It will be removed in version 1.6.0.

* Backward incompatible changes:

  * Consistently accept ``--keep-pattern`` instead of ``--keep_pattern``.

  * Change ``--tag_name`` into ``--tag-name``.

  * Change ``--target_commitish`` into ``--target-commitish``.

Python API
----------

* Backward incompatible changes:

  * Rename ``gh_asset_erase`` into ``gh_asset_delete``.

Testing
-------

* Add test checking that expected command line arguments do not cause failure.


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

* Re-organize and improve [README.md](https://github.com/j0057/github-release/tree/add-changes-md#table-of-contents).

* Add [maintainers: how to make a release ?](https://github.com/j0057/github-release/tree/add-changes-md#maintainers-how-to-make-a-release-) section.

* Add [CONTRIBUTING](https://github.com/j0057/github-release/blob/master/CONTRIBUTING.md#contributing) guidelines.
