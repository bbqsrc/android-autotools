import shutil
from subprocess import check_output

_patchelf_path = shutil.which('patchelf')
if _patchelf_path is None:
    raise ImportError("'patchelf' could not be found on the PATH.")

def get_soname(path):
    v = check_output([_patchelf_path, '--print-soname', path])
    return v.decode().strip()

def set_soname(path, soname):
    check_output([_patchelf_path, '--set-soname', soname, path])

