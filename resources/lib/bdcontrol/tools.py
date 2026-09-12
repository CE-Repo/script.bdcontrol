# -*- coding: utf-8 -*-
"""The diagnostics report."""
import glob
import os

import xbmc
import xbmcaddon
import xbmcvfs

from . import actions, kodiutils, player
from .kodiutils import jsonrpc, localize

# Places a CoreELEC/LibreELEC image or a regular distribution keeps the
# libraries libbluray loads for encrypted discs.
LIBRARY_DIRS = (
    '/usr/lib',
    '/usr/lib64',
    '/usr/local/lib',
    '/usr/lib/aarch64-linux-gnu',
    '/usr/lib/x86_64-linux-gnu',
)

AACS_CONFIG_DIRS = (
    '~/.config/aacs',
    '/storage/.config/aacs',
)

KEYMAP_DIR = 'special://profile/keymaps'
KEYMAP_EDITOR_ID = 'script.keymap'


def _find_library(name):
    """Return the first matching shared object for `name`, or ''."""
    for directory in LIBRARY_DIRS:
        matches = sorted(glob.glob(os.path.join(directory, '%s.so*' % name)))
        if matches:
            return matches[0]
    return ''


def _optical_drives():
    return sorted(glob.glob('/dev/sr[0-9]*'))


def _aacs_keydb():
    """Return (path, size) of the first KEYDB.cfg found, or ('', 0)."""
    for directory in AACS_CONFIG_DIRS:
        path = os.path.join(os.path.expanduser(directory), 'KEYDB.cfg')
        if os.path.isfile(path):
            try:
                return path, os.path.getsize(path)
            except OSError:
                return path, 0
    return '', 0


def _os_release():
    try:
        with open('/etc/os-release', 'r') as handle:
            values = {}
            for line in handle:
                if '=' not in line:
                    continue
                key, _, value = line.partition('=')
                values[key.strip()] = value.strip().strip('"')
        return values.get('PRETTY_NAME') or values.get('NAME') or ''
    except (IOError, OSError):
        return ''


# Amlogic's IR driver only emits repeats - and therefore only lets Kodi see a
# held key - when the remote configuration enables them, which is what the
# long press mappings offered by Keymap Editor depend on.
REMOTE_CONF_PATHS = (
    '/storage/.config/remote.conf',
    '/flash/remote.conf',
    '/etc/amremote/remote.conf',
)

REPEAT_KEYS = ('repeat_enable', 'repeat_delay', 'repeat_peroid',
               'repeat_period')


def _remote_conf_repeat():
    """Return (path, summary) for every remote.conf found."""
    found = []
    for path in REMOTE_CONF_PATHS:
        if not os.path.isfile(path):
            continue
        values = []
        try:
            with open(path, 'r', errors='replace') as handle:
                for line in handle:
                    stripped = line.strip()
                    if stripped.startswith('#'):
                        continue
                    for key in REPEAT_KEYS:
                        if stripped.startswith(key):
                            values.append(' '.join(stripped.split()))
                            break
        except (IOError, OSError) as exc:
            values.append(str(exc))
        found.append((path, ', '.join(values) if values else localize(30129)))
    if not found:
        found.append(('remote.conf', localize(30130)))
    return found


def _keymap_bindings():
    """Return `(file name, line)` for every keymap entry naming this addon.

    Key assignment is the Keymap Editor's job; this only reads back what it
    (or a hand written file) ended up with, so a binding that does not fire
    can be told apart from one that was never written.
    """
    directory = xbmcvfs.translatePath(KEYMAP_DIR)
    bindings = []
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return bindings
    for name in names:
        if not name.lower().endswith('.xml'):
            continue
        try:
            with open(os.path.join(directory, name), 'r',
                      encoding='utf-8', errors='replace') as handle:
                lines = handle.readlines()
        except (IOError, OSError) as exc:
            bindings.append((name, str(exc)))
            continue
        for line in lines:
            if kodiutils.ADDON_ID in line:
                bindings.append((name, ' '.join(line.split())))
    return bindings


def _keymap_editor_version():
    """Return the installed Keymap Editor's version, or None."""
    try:
        return xbmcaddon.Addon(KEYMAP_EDITOR_ID).getAddonInfo('version')
    except Exception:  # pylint: disable=broad-except
        return None


def _debug_logging():
    value = jsonrpc('Settings.GetSettingValue', setting='debug.showloginfo')
    return bool((value or {}).get('value', False))


def _disc_playback_mode_label():
    current, options = actions.disc_playback_options()
    for value, label in options:
        if value == current:
            return '%s (%s)' % (label, current)
    if current is None:
        return localize(30066)
    return str(current)


def _yes_no(flag):
    return localize(30080) if flag else localize(30081)


def diagnostics_text():
    """Build the plain text diagnostics report."""
    lines = []

    def section(title):
        lines.append('')
        lines.append('== %s ==' % title)

    lines.append('%s %s' % (localize(30000), kodiutils.addon_version()))

    section(localize(30090))  # System
    lines.append('Kodi: %s' % xbmc.getInfoLabel('System.BuildVersion'))
    os_name = _os_release()
    if os_name:
        lines.append('OS: %s' % os_name)
    lines.append('%s: %s' % (localize(30091),
                             xbmc.getInfoLabel('System.FriendlyName')))

    section(localize(30092))  # Optical drive
    drives = _optical_drives()
    lines.append('%s: %s' % (localize(30093),
                             ', '.join(drives) if drives else _yes_no(False)))
    lines.append('%s: %s' % (localize(30094),
                             _yes_no(xbmc.getCondVisibility('System.HasMediaDVD'))))

    section(localize(30095))  # Blu-ray libraries
    for name in ('libbluray', 'libaacs', 'libbdplus'):
        found = _find_library(name)
        lines.append('%s: %s' % (name, found or _yes_no(False)))
    keydb, size = _aacs_keydb()
    if keydb:
        lines.append('KEYDB.cfg: %s (%d KiB)' % (keydb, size // 1024))
    else:
        lines.append('KEYDB.cfg: %s' % _yes_no(False))
    lines.append(localize(30096))  # hint about AACS being needed for encrypted discs

    section(localize(30097))  # Kodi disc settings
    lines.append('%s: %s' % (localize(30098), _disc_playback_mode_label()))

    section(localize(30099))  # Keymap
    version = _keymap_editor_version()
    lines.append('%s: %s' % (localize(30132), version or localize(30133)))
    bindings = _keymap_bindings()
    if bindings:
        lines.append('%s:' % localize(30137))
        for name, line in bindings:
            lines.append('  %s: %s' % (name, line))
    else:
        lines.append(localize(30138))

    section(localize(30128))  # Remote configuration
    for path, value in _remote_conf_repeat():
        lines.append('%s: %s' % (path, value))
    lines.append('%s: %s' % (localize(30125), _yes_no(_debug_logging())))

    section(localize(30101))  # Playback
    state = player.PlayerState()
    if not state.playing:
        lines.append(localize(30102))
    else:
        lines.append('%s: %s' % (localize(30103), state.title()))
        lines.append('%s: %s' % (localize(30104), state.path))
        lines.append('%s: %s' % (localize(30105), _yes_no(state.is_disc)))
        lines.append('%s: %s' % (localize(30106), _yes_no(state.has_menu)))
        lines.append('%s: %s' % (localize(30107), _yes_no(state.can_seek)))
        lines.append('%s: %d/%d' % (localize(30108), state.chapter,
                                    state.chapter_count))
        lines.append('%s: %d' % (localize(30109), len(state.audio_streams)))
        lines.append('%s: %d' % (localize(30110), len(state.subtitles)))
        lines.append('%s: %s' % (localize(30111),
                                 xbmc.getInfoLabel('Player.Process(videowidth)')
                                 + 'x'
                                 + xbmc.getInfoLabel('Player.Process(videoheight)')))

    return '\n'.join(lines)


def show_diagnostics():
    kodiutils.textviewer(diagnostics_text(), localize(30034))
