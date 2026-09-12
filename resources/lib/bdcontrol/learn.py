# -*- coding: utf-8 -*-
"""Finding out which button a remote actually sends.

Long press mappings only fire when the input driver reports a held key, and
not every remote on CoreELEC does.  Rather than guessing, these two tools let
the user pin the trigger down:

* `learn_button()` captures the button code of a real key press and stores it,
  so the keymap can bind that exact code with `<key id="...">`.
* `recent_keys()` reads the same `HandleKey:` lines out of kodi.log that the
  manual procedure asks people to look for over SSH.

Both work regardless of whether the button arrives from a keyboard, an IR
remote or CEC: Kodi merges every keymap section into one map keyed by the
numeric button code, so binding the code directly sidesteps the question of
which section the button belongs to.
"""
import os
import re

import xbmcgui
import xbmcvfs

from . import kodiutils
from .kodiutils import localize, log, log_info

XML_FILE = 'script-bdcontrol-learn.xml'
SKIN_FOLDER = 'default'
SKIN_RESOLUTION = '1080i'

LABEL_HEADING = 100
LABEL_DETAIL = 101
LABEL_HINT = 102

ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92
CANCEL_ACTIONS = (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK)

# "HandleKey: menu (0xf04d, obc...) pressed, action is ActivateWindow(Home)"
KEY_LINE = re.compile(
    r'(?:HandleKey|OnKey):\s*(?P<name>\S+)\s*'
    r'\((?P<codes>[^)]*)\)\s*pressed'
    r'(?:,\s*action is\s*(?P<action>.*?))?\s*$')
HEX_CODE = re.compile(r'0x([0-9a-fA-F]+)')


class LearnDialog(xbmcgui.WindowXMLDialog):
    """Waits for one button press and remembers its code."""

    def __init__(self, *args, **kwargs):
        super(LearnDialog, self).__init__(*args, **kwargs)
        self.button_code = 0
        self.action_id = 0
        self.cancelled = False

    def onInit(self):
        self._set_label(LABEL_HEADING, localize(30117))
        self._set_label(LABEL_DETAIL, localize(30118))
        self._set_label(LABEL_HINT, '')

    def onAction(self, action):
        if action.getId() in CANCEL_ACTIONS:
            self.cancelled = True
            self.close()
            return
        code = action.getButtonCode()
        if not code:
            # Mouse movement and similar carry no button; keep waiting.
            return
        self.button_code = code
        self.action_id = action.getId()
        log_info('learned button code %d (action %d)' % (code, action.getId()))
        self.close()

    def onClick(self, control_id):
        pass

    def _set_label(self, control_id, text):
        try:
            self.getControl(control_id).setLabel(text)
        except Exception:  # pylint: disable=broad-except
            pass


def learn_button():
    """Ask the user to press a button, then offer to use it as the trigger."""
    try:
        dialog = LearnDialog(XML_FILE, kodiutils.addon_path(), SKIN_FOLDER,
                             SKIN_RESOLUTION)
    except Exception as exc:  # pylint: disable=broad-except
        kodiutils.log_error('could not create the learn window: %s' % exc)
        kodiutils.ok_dialog(localize(30120))
        return 0
    dialog.doModal()
    code = dialog.button_code
    cancelled = dialog.cancelled
    del dialog

    if cancelled:
        return 0
    if not code:
        kodiutils.ok_dialog(localize(30120))
        return 0

    if not kodiutils.yes_no('%s\n\n%s' % (localize(30119, code), localize(30123))):
        return 0

    # Import here: keymap imports nothing from this module, and this keeps the
    # dependency one-directional.
    from . import keymap
    kodiutils.set_setting('km_custom_code', str(code))
    kodiutils.set_setting_bool('km_custom', True)
    keymap.sync()
    kodiutils.notify(localize(30070))
    return code


def log_path():
    return os.path.join(xbmcvfs.translatePath('special://logpath/'), 'kodi.log')


def _read_log_tail(max_bytes=2000000):
    """Return the tail of kodi.log, or '' when it cannot be read."""
    path = log_path()
    if not os.path.isfile(path):
        log('no kodi.log at %s' % path)
        return ''
    try:
        size = os.path.getsize(path)
        with open(path, 'r', encoding='utf-8', errors='replace') as handle:
            if size > max_bytes:
                handle.seek(size - max_bytes)
                handle.readline()  # discard the partial line
            return handle.read()
    except (IOError, OSError) as exc:
        kodiutils.log_error('could not read %s: %s' % (path, exc))
        return ''


def recent_keys(limit=25):
    """Return the most recent distinct key presses seen in kodi.log.

    Each entry is (name, button_code, action) with button_code as the decimal
    number a `<key id="...">` mapping expects.
    """
    entries = []
    seen = set()
    for line in reversed(_read_log_tail().splitlines()):
        match = KEY_LINE.search(line)
        if not match:
            continue
        name = match.group('name')
        codes = HEX_CODE.findall(match.group('codes') or '')
        code = int(codes[0], 16) if codes else 0
        action = (match.group('action') or '').strip()
        key = (name, code)
        if key in seen:
            continue
        seen.add(key)
        entries.append((name, code, action))
        if len(entries) >= limit:
            break
    return entries


def show_recent_keys():
    """Show the key presses from the log, and offer to bind one of them."""
    entries = recent_keys()
    if not entries:
        kodiutils.textviewer(localize(30122), localize(30121), monospace=False)
        return

    labels = []
    for name, code, action in entries:
        label = '%s  (id %d)' % (name, code) if code else name
        if action:
            label = '%s  ->  %s' % (label, action)
        labels.append(label)

    choice = xbmcgui.Dialog().select(localize(30121), labels)
    if choice < 0:
        return
    name, code, _action = entries[choice]
    if not code:
        kodiutils.ok_dialog(localize(30120))
        return
    if not kodiutils.yes_no('%s\n\n%s' % (localize(30119, code),
                                          localize(30123))):
        return
    from . import keymap
    kodiutils.set_setting('km_custom_code', str(code))
    kodiutils.set_setting_bool('km_custom', True)
    keymap.sync()
    kodiutils.notify(localize(30070))


def custom_code():
    """The button code the user picked, or 0."""
    try:
        return int(kodiutils.get_setting('km_custom_code', '0') or '0')
    except (TypeError, ValueError):
        return 0
