#!/usr/bin/env python3

import argparse
import os
import sys
import json
import os.path
import android_autotools

a = argparse.ArgumentParser()

a.add_argument('-R', '--release', action='store_true')
a.add_argument('-c', '--config', nargs='?', type=argparse.FileType('r'),
                help='build from supplied config JSON')
a.add_argument('-a', '--arch', action='append', help="architectures")
a.add_argument('output_dir', nargs=1, default=['.'])

args = a.parse_args()

if args.config is None:
    print("ERROR: please provide a .json config file.")
    sys.exit(1)

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
