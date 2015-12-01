import argparse
import subprocess
import shutil
import tempfile
import os.path
import os
import glob

from collections import OrderedDict
from subprocess import PIPE, Popen

class SickeningNightmare:
    def log_arch(self, arch, *args):
        print("[%s] %s" % (arch, " ".join(args)))

    def add_arch(self, arch):
        cmd = os.path.join(self.ndk_path,
            'build','tools','make-standalone-toolchain.sh')

        path = os.path.join(self.toolchain_dir.name, arch)
        self.log_arch(arch, "Building toolchain…")

        p = Popen(['sh', cmd,
            '--install-dir=%s' % path,
            '--stl=%s' % self.stl,
            '--arch=%s' % arch],
            stdout=PIPE, stderr=PIPE)

        out, err = p.communicate()
        if p.returncode != 0:
            raise IOError(out.decode())

        self.log_arch(arch, out.decode().split('\n')[0].strip())

        self.log_arch(arch, "Toolchain built!")
        return path

    def __init__(self, ndk_path, archs, platform='android-14', stl='stlport'):
        if not os.path.isdir(ndk_path):
            raise Exception("ndk_path must be to the NDK directory")

        self.ndk_path = ndk_path
        self.stl = stl
        self.archs = OrderedDict()
        self.toolchain_dir = tempfile.TemporaryDirectory()
        self.prefix_dir = tempfile.TemporaryDirectory()

        for arch in archs:
            self.archs[arch] = self.add_arch(arch)

    def get_env(self, arch, prefix=None, env=None):
        path = self.archs[arch]
        host = self.get_host(arch)

        o = os.environ.copy()
        o["PATH"] = "%s:%s" % (os.path.join(path, 'bin'), os.environ['PATH'])

        o["CPP"] = "%s-cpp" % host
        o["AR"] = "%s-ar" % host
        o["NM"] = "%s-nm" % host
        o["CC"] = "%s-gcc" % host
        o["CXX"] = "%s-g++" % host
        o["LD"] = "%s-ld" % host
        o["RANLIB"] = "%s-ranlib" % host
        o["STRIP"] = "%s-strip" % host

        o["PKG_CONFIG_PATH"] = os.path.join(self.prefix_dir.name, 'lib', 'pkgconfig')

        if env:
            o.update(env)

        return o

    def get_toolchain(self, arch):
        return os.path.join(self.archs[arch], 'bin')

    def get_sysroot(self, arch):
        return os.path.join(self.archs[arch], 'sysroot')

    def get_host(self, arch):
        return os.path.basename(glob.glob(os.path.join(
                self.get_toolchain(arch), '*-gcc'))[0].rsplit('-', 1)[0])

    def configure(self, arch, src_dir, *args, env=None):
        toolchain = self.get_toolchain(arch)
        sysroot = self.get_sysroot(arch)
        host = self.get_host(arch)

        env = self.get_env(arch, env)
        env['CPPFLAGS'] = '--sysroot=%s' % sysroot
        env['LDFLAGS'] = '-L%s/usr/lib' % sysroot

        p = Popen(['./configure',
                    '--host', host,
                    '--prefix', self.prefix_dir.name,
                    '--disable-static',
                    '--enable-shared'] + list(args),
                    cwd=src_dir, env=env)
        p.wait()

        if p.returncode != 0:
            raise IOError(p.returncode)

    def make(self, arch, src_dir, *args):
        p = Popen(['make'] + list(args), cwd=src_dir, env=self.get_env(arch))
        p.wait()

        if p.returncode != 0:
            raise IOError(p.returncode)

    def make_install(self, arch, src_dir, *args):
        p = Popen(['make', 'install'] + list(args), cwd=src_dir, env=self.get_env(arch))
        p.wait()

        if p.returncode != 0:
            raise IOError(p.returncode)

    def make_distclean(self, arch, src_dir):
        p = Popen(['make', 'distclean'] + list(args), cwd=src_dir, env=self.get_env(arch))
        p.wait()
        # We don't care if this fails.

    def install_lib(self, libname, libdir):
        libdir = os.path.abspath(libdir)
        shutil.copyfile(os.path.join(self.prefix_dir.name, 'lib', libname),
                        os.path.join(libdir, libname))

    def build(self, arch, src_dir, libname, libdir):
        self.configure(arch, src_dir)
        self.make(arch, src_dir)
        self.make_install(arch, src_dir)
        self.install_lib(libname, libdir)

    def build_archs(self, archs, src_dir, libname, libdir):
        pass
