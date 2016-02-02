#!/usr/bin/env python3

import argparse
import os
import sys
import json
import os.path
import subprocess

import android_autotools

def main():
    a = argparse.ArgumentParser(prog='abuild',
            description='A wrapper around autotools for Android.',
            epilog='NDK_HOME must be defined to use this tool.')

    a.add_argument('--version', action='version',
            version="%(prog)s (android_autotools) {}".format(
                android_autotools.__version__))
    a.add_argument('-v', dest='verbose', action='store_true',
            help="verbose output")

    g = a.add_argument_group('build options')
    g.add_argument('-a', dest='arch', metavar='arch', action='append',
            help="override architectures in provided build file")
    g.add_argument('-o', metavar='dir', dest='output_dir',
            default='.', help="output directory for build (default: cwd)")
    g.add_argument('-R', dest='release', action='store_true',
            help="build release (default: debug)")
    a.add_argument('-f', dest='config', default='abuild.json',
            type=argparse.FileType('r'),
            help='build from supplied JSON build file')

    args = a.parse_args()

    conf = json.load(args.config)
    args.config.close()

    if 'NDK_HOME' not in os.environ:
        print("ERROR: NDK_HOME must be defined.")
        return 1

    output_dir = os.path.abspath(args.output_dir)
    conf_dir = os.path.dirname(args.config.name)

    build = android_autotools.BuildSet(
                os.environ['NDK_HOME'],
                output_dir,
                release=args.release,
                archs=args.arch or conf.get('archs', android_autotools.ARCHS),
                verbose=args.verbose)

    for t in conf['targets']:
        build.add(os.path.join(conf_dir, t['path']),
            t['output'],
            *t['configure'],
            inject=t.get('inject', None),
            cpp=t.get('c++', False))

    try:
        res = build.run()
        return 0 if res is not False else 1
    except Exception as e:
        if args.verbose:
            raise e
        print(e)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
