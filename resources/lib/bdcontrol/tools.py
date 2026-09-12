# -*- coding: utf-8 -*-
"""Extra tools: the "More" menu and the diagnostics report."""
import glob
import os

import xbmc
import xbmcgui

from . import actions, keymap, kodiutils, player
from .kodiutils import localize

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


def _find_library(name):
    """Return the first matching shared object for `name`, or ''."""
    for directory in LIBRARY_DIRS:
        matches = sorted(glob.glob(os.path.join(directory, '%s.so*' % name)))
        if matches:
            return matches[0]
    return ''


def _optical_drives():
    drives = sorted(glob.glob('/dev/sr[0-9]*'))
    return drives


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
    lines.append('%s: %s' % (localize(30100),
                             keymap.keymap_path() if keymap.is_installed()
                             else _yes_no(False)))
    for line in keymap.describe():
        lines.append('  %s' % line)

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


def copy_diagnostics_to_log():
    for line in diagnostics_text().splitlines():
        kodiutils.log_info(line)
    kodiutils.notify(localize(30112))


def more_menu(closer=None):
    """The overflow menu reached from the "More" button of the OSD.

    `closer` closes the BD Control dialog; entries that open another Kodi
    window or take over playback call it first so they are not stacked on top
    of our own OSD.
    """
    entries = [
        (localize(30035), actions.audio_settings, True),
        (localize(30036), actions.subtitle_settings, True),
        (localize(30037), actions.toggle_subtitles, True),
        (localize(30038), actions.next_audio_language, True),
        (localize(30033), actions.disc_playback_mode, False),
        (localize(30039), actions.eject, True),
        (localize(30034), show_diagnostics, False),
        (localize(30113), copy_diagnostics_to_log, False),
        (localize(30004), actions.open_settings, True),
    ]
    choice = xbmcgui.Dialog().select(localize(30026),
                                     [entry[0] for entry in entries])
    if choice < 0:
        return
    _label, handler, needs_close = entries[choice]
    if needs_close and closer is not None:
        closer()
    handler()
