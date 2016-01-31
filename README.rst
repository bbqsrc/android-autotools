android-autotools
=================

A solution to the nastiness that is building autotools-based projects
for Android using the NDK.

Installation
------------

::

    pip install android-autotools

Usage
-----

::

    usage: abuild [-h] [--version] [-v] [-a arch] [-o dir] [-R] [-f CONFIG]

    A wrapper around autotools for Android.

    optional arguments:
      -h, --help  show this help message and exit
      --version   show program's version number and exit
      -v          verbose output
      -f CONFIG   build from supplied JSON build file

    build options:
      -a arch     override architectures in provided build file
      -o dir      output directory for build (default: cwd)
      -R          build release (default: debug)

    NDK_HOME must be defined to use this tool.

License
-------

BSD 2-clause. See LICENSE.
