import os
import shutil
import sys
import tempfile

_patchelf_path = shutil.which('patchelf')
if _patchelf_path is None:
    raise ImportError("'patchelf' could not be found on the PATH.")

from ctypes import *

_lib = CDLL(_patchelf_path)

def _parse_args(args):
    cls = c_char_p * len(args)
    return len(args), cls(*[c_char_p(arg.encode()) for arg in args])

def _return_stdout(func):
    def wrapped(*args):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        fdo = os.dup(old_stdout.fileno())
        fde = os.dup(old_stderr.fileno())

        sys.stdout = tempfile.TemporaryFile()
        sys.stderr = tempfile.TemporaryFile()
        os.dup2(sys.stdout.fileno(), 1)
        os.dup2(sys.stderr.fileno(), 2)

        pid = os.fork()
        if pid == 0:
            sys.exit(func(*args))
        else:
            pid, return_code = os.wait()

        sys.stdout.flush()
        sys.stderr.flush()
        sys.stdout.seek(0)
        sys.stderr.seek(0)

        out = sys.stdout.read().decode()
        err = sys.stderr.read().decode()

        sys.stdout.close()
        sys.stderr.close()

        os.dup2(fdo, 1)
        os.dup2(fde, 2)

        sys.stdout = old_stdout
        sys.stderr = old_stderr

        if return_code > 0:
            raise OSError(return_code, err.strip())

        return out, err
    return wrapped

@_return_stdout
def _patchelf(*args):
    parsed = _parse_args(['patchelf'] + list(args))
    _lib.main(*parsed)

def get_soname(path):
    return _patchelf('--print-soname', path)[0].strip()

def set_soname(path, soname):
    _patchelf('--set-soname', soname, path)

