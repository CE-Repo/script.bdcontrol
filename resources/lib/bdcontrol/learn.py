# -*- coding: utf-8 -*-
"""Finding out which button a remote actually sends.

Long press mappings only fire when the input driver reports a held key, and
not every remote on CoreELEC does.  Rather than guessing, these two tools let
the user pin the trigger down:

* `assign()` captures the button code of a real key press, asks whether it
  should need a long press, and stores both so the keymap can bind that exact
  code with `<key id="...">`.
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


def _capture():
    """Show the "press a button" dialog and return its code, or 0."""
    try:
        dialog = LearnDialog(XML_FILE, kodiutils.addon_path(), SKIN_FOLDER,
                             SKIN_RESOLUTION)
    except Exception as exc:  # pylint: disable=broad-except
        kodiutils.log_error('could not create the learn window: %s' % exc)
        return 0
    dialog.doModal()
    code = 0 if dialog.cancelled else dialog.button_code
    del dialog
    return code


def _ask_longpress(code):
    """The question asked once a button has been picked.

    Returns True for a long press binding, False for a normal one, and None
    when the user backed out.
    """
    message = '%s\n\n%s' % (localize(30119, code), localize(30142))
    return kodiutils.yes_no(message,
                            yeslabel=localize(30143),
                            nolabel=localize(30144))


def assign(slot_name):
    """Assign a button to one of the keymap slots.

    Asks for the button first and for the kind of press afterwards, then
    writes the keymap straight away so the binding is live without a restart.
    """
    from . import keymap
    target = keymap.slot(slot_name)
    if target is None:
        kodiutils.log_error('unknown keymap slot "%s"' % slot_name)
        return 0

    code = _capture()
    if not code:
        # A button with no mapping anywhere produces no action at all and
        # never reaches the dialog; the log still records the press.
        if not kodiutils.yes_no(localize(30149)):
            return 0
        code = _pick_from_log()
    if not code:
        return 0

    clash = keymap.assigned_slot_for(code)
    if clash is not None and clash.name != target.name:
        kodiutils.ok_dialog(localize(30150, clash.label))
        return 0

    longpress = _ask_longpress(code)
    if longpress is None:
        return 0

    target.assign(code, longpress)
    if not kodiutils.get_setting_bool('keymap_enabled', True):
        kodiutils.set_setting_bool('keymap_enabled', True)
    keymap.sync()
    log_info('assigned button %d to %s (longpress=%s)'
             % (code, target.name, longpress))
    kodiutils.notify(target.describe())
    if longpress:
        kodiutils.ok_dialog(localize(30151))
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


def _pick_from_log():
    """Let the user choose one of the key presses recorded in kodi.log."""
    entries = recent_keys()
    if not entries:
        kodiutils.textviewer(localize(30122), localize(30121), monospace=False)
        return 0
    labels = []
    for name, code, action in entries:
        label = '%s  (id %d)' % (name, code) if code else name
        if action:
            label = '%s  ->  %s' % (label, action)
        labels.append(label)
    choice = xbmcgui.Dialog().select(localize(30121), labels)
    if choice < 0:
        return 0
    code = entries[choice][1]
    if not code:
        kodiutils.ok_dialog(localize(30120))
        return 0
    return code


def show_recent_keys():
    """Read-only view of the key presses in kodi.log."""
    entries = recent_keys()
    if not entries:
        kodiutils.textviewer(localize(30122), localize(30121), monospace=False)
        return
    lines = []
    for name, code, action in entries:
        line = '%s (id %d)' % (name, code) if code else name
        if action:
            line = '%s  ->  %s' % (line, action)
        lines.append(line)
    kodiutils.textviewer('\n'.join(lines), localize(30121))
