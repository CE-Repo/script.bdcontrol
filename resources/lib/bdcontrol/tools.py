# -*- coding: utf-8 -*-
"""Extra tools: the "More" menu and the diagnostics report."""
import glob
import os

import xbmc
import xbmcaddon
import xbmcgui

from . import actions, keymap, kodiutils, learn, player
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


# Amlogic's IR driver only emits repeats - and therefore only lets Kodi see a
# held key - when the remote configuration enables them, which is what long
# press mappings depend on.
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


KEYMAP_EDITOR_ID = 'script.keymap'


def _keymap_editor_status():
    """Report whether Keymap Editor is installed and set to co-exist.

    Its "enable_multifile" setting decides whether saving renames every other
    keymap file - ours included - to *.xml.bak.N.  It defaults to off.
    """
    try:
        editor = xbmcaddon.Addon(KEYMAP_EDITOR_ID)
    except Exception:  # pylint: disable=broad-except
        return None, False, ''
    try:
        multifile = editor.getSetting('enable_multifile') == 'true'
    except Exception:  # pylint: disable=broad-except
        multifile = False
    try:
        filename = editor.getSetting('keymap_editor_filename') or 'gen'
    except Exception:  # pylint: disable=broad-except
        filename = 'gen'
    return editor.getAddonInfo('version'), multifile, '%s.xml' % filename


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
    lines.append('%s: %s' % (localize(30223),
                             _yes_no(actions.extended_disc_menus())))

    section(localize(30099))  # Keymap
    lines.append('%s: %s' % (localize(30100),
                             keymap.keymap_path() if keymap.is_installed()
                             else _yes_no(False)))
    for line in keymap.describe():
        lines.append('  %s' % line)
    if keymap.is_installed():
        lines.append('')
        lines.append('%s:' % localize(30126))
        for line in keymap.read_existing().splitlines():
            if line.strip().startswith('<!--') or line.strip().startswith('-->'):
                continue
            lines.append('  %s' % line)

    version, multifile, filename = _keymap_editor_status()
    lines.append('')
    if version is None:
        lines.append('%s: %s' % (localize(30132), localize(30133)))
    else:
        lines.append('%s: %s (%s)' % (localize(30132), version, filename))
        lines.append('  %s: %s' % (localize(30134), _yes_no(multifile)))
        if not multifile:
            lines.append('  %s' % localize(30136))
    copies = keymap.disabled_copies()
    if copies:
        lines.append('%s:' % localize(30135))
        for path in copies:
            lines.append('  %s' % path)

    section(localize(30128))  # Remote configuration
    for path, value in _remote_conf_repeat():
        lines.append('%s: %s' % (path, value))
    lines.append('%s: %s' % (localize(30125), _yes_no(_debug_logging())))
    keys = learn.recent_keys(limit=8)
    if keys:
        lines.append('%s:' % localize(30121))
        for name, code, action in keys:
            lines.append('  %s (id %d)%s'
                         % (name, code, '  ->  %s' % action if action else ''))
    else:
        lines.append(localize(30122))

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
    # The popup/top disc-menu buttons live directly in the OSD instead of
    # here once extended_disc_menus is on - see dialog._build_commands().
    entries = [
        (localize(30030), actions.choose_audio, False),
        (localize(30031), actions.choose_subtitle, False),
        (localize(30037), actions.toggle_subtitles, True),
        (localize(30038), actions.next_audio_language, True),
        (localize(30033), actions.disc_playback_mode, False),
        (localize(30039), actions.eject, True),
        (localize(30116), lambda: learn.assign('osd'), False),
        (localize(30121), learn.show_recent_keys, False),
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
