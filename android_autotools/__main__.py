#!/usr/bin/env python3

import argparse
import os
import sys
import json
import os.path
import android_autotools

def main():
    a = argparse.ArgumentParser(prog='abuild',
            description='A wrapper around autotools for Android.',
            epilog='NDK_HOME must be defined to use this tool.')

    a.add_argument('-v', '--version', action='version',
            version="%(prog)s (android_autotools) {}".format(
                android_autotools.__version__))
    a.add_argument('-a', metavar='arch', action='append',
            help="override architectures in provided build file")
    a.add_argument('-o', metavar='dir', dest='output_dir',
            default='.', help="output directory for build (default: cwd)")
    a.add_argument('-R', action='store_true',
            help="build release (default: debug)")
    a.add_argument('config', type=argparse.FileType('r'),
            help='build from supplied JSON build file')

    args = a.parse_args()

    conf = json.load(args.config)
    args.config.close()

    if 'NDK_HOME' not in os.environ:
        print("ERROR: NDK_HOME must be defined.")
        sys.exit(1)

    output_dir = os.path.abspath(args.output_dir[0])
    conf_dir = os.path.dirname(args.config.name)

    build = android_autotools.BuildSet(os.environ['NDK_HOME'],
            output_dir,
            release=args.release,
            archs=args.arch or conf.get('archs', android_autotools.ARCHS))

    for t in conf['targets']:
        build.add(os.path.join(conf_dir, t['path']),
            t['output'],
            *t['configure'],
            inject=t.get('inject', None),
            cpp=t.get('c++', False))

    build.run()

if __name__ == "__main__":
    main()
