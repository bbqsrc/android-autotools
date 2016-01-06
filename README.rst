android-autotools
=================

A solution to the nastiness that is building autotools-based projects
for Android using the NDK.

Installation
------------

::

    pip install android-autotools

**If using Linux:** you will need to install
`patchelf <https://github.com/NixOS/patchelf>`_ to work around an
issue where the ``SONAME`` value is set incorrectly using the NDK with a
Linux host. Building on other host systems does not require this dependency.

Usage
-----

::

    usage: abuild [-h] [--version] [-v] [-a arch] [-o dir] [-R] config

    A wrapper around autotools for Android.

    positional arguments:
      config      build from supplied JSON build file

    optional arguments:
      -h, --help  show this help message and exit
      --version   show program's version number and exit
      -v          verbose output

    build options:
      -a arch     override architectures in provided build file
      -o dir      output directory for build (default: cwd)
      -R          build release (default: debug)

    NDK_HOME must be defined to use this tool.

License
-------

BSD 2-clause. See LICENSE.
