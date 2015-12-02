import argparse
import subprocess
import shutil
import tempfile
import os.path
import os
import glob
import json
import copy
import multiprocessing
import datetime

from collections import OrderedDict
from subprocess import PIPE, Popen

fpath = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(fpath, "data.json")) as f:
    config = json.load(f, object_pairs_hook=OrderedDict)

def abi_to_arch(abi):
    for arch, o in config['archs'].items():
        if abi in o['abis']:
            return arch
    raise Exception("Unknown ABI: '%s'" % abi)

def abis_for_arch(arch):
    return tuple(config['archs'][arch]['abis'])

def all_abis():
    x = []
    for o in config['archs'].values():
        x += list(o['abis'])
    return tuple(x)

def log_tag(tag, *args):
    print("{} [{}] {}".format(str(datetime.datetime.now()), tag, " ".join(args)))

class SharedLibrary:
    def __init__(self, toolchain, src_dir, name, lib_path):
        self.toolchain = toolchain
        self.name = name
        self.path = lib_path
        self.src_dir = src_dir

    def build(self, *args, inject=None):
        t = self.toolchain
        s = self.src_dir
        t.make_distclean(s)

        log_tag(t.abi, "%s: ./configure" % self.name)
        t.configure(s, *args)

        if inject:
            log_tag(t.abi, "%s: injecting header content" % self.name)
            t.inject(s, inject)

        log_tag(t.abi, "%s: make" % self.name)
        t.make(s)

        log_tag(t.abi, "%s: make install" % self.name)
        t.make_install(s)

        log_tag(t.abi, "%s -> %s/%s (shared library)" % (self.name, self.path, t.abi))
        t.install_lib(self.name, self.path)

class Toolchain:
    def __init__(self, path, prefix, arch, abi):
        self.arch = arch
        self.abi = abi
        self.path = path
        self.prefix = prefix

    def get_toolchain(self):
        return os.path.join(self.path, 'bin')

    def get_sysroot(self):
        return os.path.join(self.path, 'sysroot')

    def get_host(self):
        return os.path.basename(glob.glob(os.path.join(
                self.get_toolchain(), '*-gcc'))[0].rsplit('-', 1)[0])

    def get_env(self):
        host = self.get_host()
        sysroot = self.get_sysroot()

        o = os.environ.copy()
        o["PATH"] = "%s:%s" % (self.get_toolchain(), os.environ['PATH'])

        o["CPP"] = "%s-cpp" % host
        o["AR"] = "%s-ar" % host
        o["NM"] = "%s-nm" % host
        o["CC"] = "%s-gcc" % host
        o["CXX"] = "%s-g++" % host
        o["LD"] = "%s-ld" % host
        o["RANLIB"] = "%s-ranlib" % host
        o["STRIP"] = "%s-strip" % host

        o["PKG_CONFIG_PATH"] = os.path.join(self.prefix, 'lib', 'pkgconfig')

        cflags = copy.copy(config['cflags'])
        cxxflags = copy.copy(config['cxxflags'])
        ldflags = copy.copy(config['ldflags'])

        cflags.append('--sysroot=%s -I%s/usr/include -I%s/include' % (sysroot, sysroot, self.prefix))
        cxxflags.append('--sysroot=%s -I%s/usr/include -I%s/include' % (sysroot, sysroot, self.prefix))
        ldflags.append('-L%s/usr/lib -L%s/lib' % (sysroot, self.prefix))

        abiflags = config['archs'][self.arch]['abis'][self.abi]

        if 'cflags' in abiflags:
            cflags += abiflags['cflags']

        if 'cxxflags' in abiflags:
            cxxflags += abiflags['cxxflags']

        if 'ldflags' in abiflags:
            ldflags += abiflags['ldflags']

        o['CFLAGS'] = " ".join(cflags)
        o['CXXFLAGS'] = " ".join(cxxflags)
        o['LDFLAGS'] = " ".join(ldflags)

        return o

    def configure(self, src_dir, *args):
        toolchain = self.get_toolchain()
        sysroot = self.get_sysroot()
        host = self.get_host()
        env = self.get_env()

        p = Popen(['./configure',
                    '--host', host,
                    '--prefix', self.prefix,
                    '--disable-static',
                    '--enable-shared',
                    '--with-sysroot=%s' % sysroot] + list(args),
                    cwd=src_dir, env=env, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()

        if p.returncode != 0:
            raise IOError(err.decode())

    def make(self, src_dir):
        j = str(multiprocessing.cpu_count())

        p = Popen(['make', '-j', j],
            cwd=src_dir, env=self.get_env(), stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()

        if p.returncode != 0:
            raise IOError(err.decode())

    def make_install(self, src_dir):

        p = Popen(['make', 'install'], cwd=src_dir, env=self.get_env(),
             stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()

        if p.returncode != 0:
            raise IOError(err.decode())

    def make_distclean(self, src_dir):
        p = Popen(['make', 'distclean'], cwd=src_dir, env=self.get_env(),
            stdout=PIPE, stderr=PIPE)
        p.wait()
        # We don't care if this fails.

    def install_lib(self, libname, libdir):
        libdir = os.path.join(os.path.abspath(libdir), self.abi)
        os.makedirs(libdir, exist_ok=True)

        src = os.path.join(self.prefix, 'lib', libname)
        dest = os.path.join(libdir, libname)

        shutil.copyfile(src, dest)

    def inject(self, src_dir, code):
        with open(os.path.join(src_dir, 'config.h'), 'a') as f:
            f.write('\n' + code.strip() + '\n')

class SickeningNightmare:
    def add_toolchain(self, arch):
        cmd = os.path.join(self.ndk_path,
            'build', 'tools', 'make-standalone-toolchain.sh')

        path = os.path.join(self.toolchain_dir.name, arch)
        log_tag(arch, "Building toolchain…")

        p = Popen(['sh', cmd,
            '--install-dir=%s' % path,
            '--stl=%s' % self.stl,
            '--arch=%s' % arch],
            stdout=PIPE, stderr=PIPE)

        out, err = p.communicate()
        if p.returncode != 0:
            raise IOError(out.decode())

        log_tag(arch, out.decode().split('\n')[0].strip())

        abis = abis_for_arch(arch)
        log_tag(arch, "Supported ABIs: %s" % ", ".join(abis))

        for abi in abis:
            self.toolchains[abi] = Toolchain(path, self.prefix_dir.name, arch, abi)

    def __init__(self, ndk_path, archs=list(config['archs'].keys()),
                platform='android-14', stl='stlport'):
        if not os.path.isdir(ndk_path):
            raise Exception("ndk_path must be to the NDK directory")

        self.ndk_path = ndk_path
        self.stl = stl
        self.toolchains = OrderedDict()
        self.toolchain_dir = tempfile.TemporaryDirectory()
        self.prefix_dir = tempfile.TemporaryDirectory()

        for arch in archs:
            self.add_toolchain(arch)

    def build(self, src_dir, libname, libdir, *args, inject=None, abis=None):
        if abis is None:
            abis = self.toolchains.keys()

        log_tag("***", "Beginning builds!")


        for abi in abis:
            toolchain = self.toolchains[abi]
            SharedLibrary(toolchain, src_dir, libname, libdir).build(*args, inject=inject)
