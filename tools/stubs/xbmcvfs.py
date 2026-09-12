"""Minimal stand-in for Kodi's xbmcvfs module."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROFILE = os.path.join(ROOT, '.profile')


def translatePath(path):  # noqa: N802
    if path.startswith('special://logpath/'):
        return os.path.join(PROFILE, 'temp')
    if path.startswith('special://profile/'):
        return os.path.join(PROFILE, path[len('special://profile/'):])
    if path.startswith('special://home/'):
        return os.path.join(ROOT, path[len('special://home/'):])
    return path


def exists(path):
    return os.path.exists(path)


def mkdirs(path):
    os.makedirs(path, exist_ok=True)
    return True


def delete(path):
    try:
        os.remove(path)
        return True
    except OSError:
        return False


class File(object):
    def __init__(self, path, mode='r'):
        self._handle = open(path, mode + ('b' if 'b' in mode else ''),
                            encoding=None if 'b' in mode else 'utf-8')

    def read(self):
        return self._handle.read()

    def write(self, data):
        return self._handle.write(data)

    def close(self):
        self._handle.close()
