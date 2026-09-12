# -*- coding: utf-8 -*-
"""The BD Control on-screen display."""
import threading
import time

import xbmc
import xbmcgui

from . import actions, kodiutils, player, theme, tools
from .kodiutils import (PROP_CHAPTER, PROP_OSD_CLOSE, PROP_OSD_OPEN,
                        PROP_OSD_TRIGGERED, home_property, localize, log)

XML_FILE = 'script-bdcontrol-osd.xml'
XML_FILE_COMPACT = 'script-bdcontrol-osd-compact.xml'
SKIN_FOLDER = 'default'
SKIN_RESOLUTION = '1080i'

# Control ids, mirroring resources/skins/default/1080i/script-bdcontrol-osd.xml
GROUP_PANEL = 2
LABEL_TITLE = 100
LABEL_STATUS = 101
LABEL_HINT = 103

# Where the panel group sits, per size: left edge, then <top> at 100% and at
# 0% of the "vertical position" slider. The slider reads as how far down the
# screen the OSD sits, so 100% is the bottom - and the default. The compact
# panel is shorter, so its bottom value is lower by the difference: both
# sizes then rest their lower edge on the same line and switching size does
# not move the OSD. The numbers mirror the profiles in tools/genskin.py.
PANEL_LAYOUT = {
    False: (50, 860, 50),
    True: (278, 902, 50),
}

# How far the compact panel may travel sideways: from the screen margin the
# full size panel keeps, to the same margin on the right (1920 - 1365 - 50).
# The midpoint of that range is where the compact panel is centred, so 50%
# leaves it exactly where it sits with no setting at all.
COMPACT_LEFT_MIN = 50
COMPACT_LEFT_MAX = 505

BUTTON_POPUP_MENU = 201
BUTTON_TOP_MENU = 202
BUTTON_KODI_OSD = 203
BUTTON_DIAGNOSTICS = 204
BUTTON_STREAM = 205

# The icons+text style draws its label inside a grouplist next to the icon
# rather than on the button; the skin file numbers those id + offset, one for
# each focus state.
PAIR_LABEL_OFFSET = 100
PAIR_FOCUS_LABEL_OFFSET = 200

# Buttons the skin file lays out square and icon-only, whatever the selected
# button style - they have no label of either kind to fill in.
ICON_ONLY_BUTTONS = (BUTTON_DIAGNOSTICS,)

# Left to right, matching the skin file and the plain-list fallback. The ids
# are not in order here: they were handed out as the buttons were added, the
# row has been arranged since.
BUTTON_ORDER = (BUTTON_KODI_OSD, BUTTON_POPUP_MENU, BUTTON_TOP_MENU,
                BUTTON_STREAM, BUTTON_DIAGNOSTICS)

ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92

CLOSE_ACTIONS = (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK)

TICK_SECONDS = 0.5

# How long the settings "preview" button shows the OSD for.
PREVIEW_SECONDS = 3

# Triggers arriving closer together than this are treated as one press. An IR
# remote that repeats while the button is held would otherwise flip the OSD
# open and shut several times a second.
DEBOUNCE_SECONDS = 0.5


class Command(object):
    """One OSD button: its label, its help line and what it does."""

    def __init__(self, label_id, hint_id, handler, closes=False):
        self.label_id = label_id
        self.hint_id = hint_id
        self.handler = handler
        self.closes = closes

    @property
    def label(self):
        return localize(self.label_id)

    @property
    def hint(self):
        return localize(self.hint_id)


def _build_commands():
    return {
        BUTTON_POPUP_MENU: Command(30114, 30459, actions.disc_popup_menu,
                                   closes=True),
        BUTTON_TOP_MENU: Command(30115, 30460, actions.disc_top_menu,
                                 closes=True),
        BUTTON_KODI_OSD: Command(30028, 30047, actions.kodi_osd, closes=True),
        BUTTON_STREAM: Command(30117, 30462, actions.stream_menu,
                               closes=True),
        BUTTON_DIAGNOSTICS: Command(30034, 30048, tools.show_diagnostics,
                                    closes=True),
    }


class BDControlDialog(xbmcgui.WindowXMLDialog):
    """A player OSD that stays reachable while a disc menu owns the remote."""

    def __init__(self, *args, **kwargs):
        super(BDControlDialog, self).__init__(*args, **kwargs)
        self.commands = _build_commands()
        self._stop = threading.Event()
        self._worker = None
        self._last_input = time.time()
        self._timeout = max(kodiutils.get_setting_int('osd_timeout', 10), 0)
        self._closing = False
        # Which of the two window files this instance was built from - the
        # panel geometry differs, so _apply_position has to know.
        self._compact = compact_mode()
        # Set by preview() before doModal(): shows sample data and auto-closes
        # after PREVIEW_SECONDS instead of following real playback.
        self.preview_mode = False

    # -- lifecycle --------------------------------------------------------

    def onInit(self):
        self._apply_position()
        self._apply_labels()
        if self.preview_mode:
            self._show_preview_content()
        else:
            self._refresh()
        self._touch()
        if self._worker is None:
            target = (self._preview_loop if self.preview_mode
                      else self._tick_loop)
            self._worker = threading.Thread(target=target)
            self._worker.daemon = True
            self._worker.start()

    def close(self):
        if self._closing:
            return
        self._closing = True
        # The tab reads this straight from the window, so a stale value would
        # outlive the OSD and reappear with the next one.
        home_property(PROP_CHAPTER, '')
        self._stop.set()
        super(BDControlDialog, self).close()

    def wait_for_worker(self):
        self._stop.set()
        if self._worker is not None and self._worker.is_alive():
            self._worker.join(2.0)
        self._worker = None

    # -- input ------------------------------------------------------------

    def onAction(self, action):
        self._touch()
        if action.getId() in CLOSE_ACTIONS:
            self.close()

    def onClick(self, control_id):
        self._touch()
        if self.preview_mode:
            # Sample data only - a click must not run a real player command.
            return
        command = self.commands.get(control_id)
        if command is None:
            return
        if command.closes:
            self.close()
        try:
            command.handler()
        except Exception as exc:  # pylint: disable=broad-except
            kodiutils.log_error('command %s failed: %s' % (control_id, exc))
            kodiutils.notify(localize(30055))
        if not self._closing:
            self._refresh()

    def onFocus(self, control_id):
        self._touch()
        command = self.commands.get(control_id)
        self._set_label(LABEL_HINT, command.hint if command else '')

    # -- rendering --------------------------------------------------------

    def _apply_position(self):
        """Move the panel to the configured vertical position.

        100% is the bottom of the screen and the default; 0% moves it to a
        small margin below the top edge. Sideways only the compact panel can
        move: the full size one spans the screen and has nowhere to go.
        """
        left, bottom, ceiling = PANEL_LAYOUT[self._compact]
        percent = max(0, min(100, kodiutils.get_setting_int('osd_position_y', 100)))
        top = ceiling + round((bottom - ceiling) * percent / 100)
        if self._compact:
            across = max(0, min(100,
                                kodiutils.get_setting_int('osd_position_x', 50)))
            left = COMPACT_LEFT_MIN + round(
                (COMPACT_LEFT_MAX - COMPACT_LEFT_MIN) * across / 100)
        try:
            self.getControl(GROUP_PANEL).setPosition(left, top)
        except Exception:  # pylint: disable=broad-except
            pass

    def _apply_labels(self):
        """Put each command's name where the selected button style shows it.

        Text on its own is the button's own centred label. Paired with an
        icon it is a label inside the skin file's grouplist instead, which is
        what keeps the two a fixed distance apart whatever the word's length;
        that one comes in a focused and an unfocused copy, since a label
        control has no colour of its own to switch. The icons-only style
        needs neither.
        """
        style = theme.button_style()
        for control_id, command in self.commands.items():
            if control_id in ICON_ONLY_BUTTONS:
                # Square and wordless in every style, icon only - no label of
                # either kind to fill in.
                self._set_label(control_id, '')
                continue
            self._set_label(control_id,
                            command.label if style == theme.STYLE_TEXT else '')
            paired = command.label if style == theme.STYLE_ICONS_AND_TEXT else ''
            self._set_label(control_id + PAIR_LABEL_OFFSET, paired)
            self._set_label(control_id + PAIR_FOCUS_LABEL_OFFSET, paired)

    def _touch(self):
        self._last_input = time.time()

    def _set_label(self, control_id, text):
        try:
            self.getControl(control_id).setLabel(text)
        except Exception as exc:  # pylint: disable=broad-except
            # Usually the control is gone because the window is closing, and
            # there is nothing to do - but an empty label with no explanation
            # anywhere is the one failure this addon cannot afford to hide.
            if not self._closing:
                log('could not set label %s: %s' % (control_id, exc))

    def _refresh(self):
        try:
            state = player.PlayerState()
        except Exception as exc:  # pylint: disable=broad-except
            kodiutils.log_error('could not read the player state: %s' % exc)
            return
        self._set_label(LABEL_TITLE, state.title())
        self._set_label(LABEL_STATUS, state.describe())
        home_property(PROP_CHAPTER, state.chapter_text())
        if not state.playing:
            # Playback ended while the OSD was open - there is nothing to
            # control any more.
            self.close()

    def _show_preview_content(self):
        """Fill the labels with sample data for the settings' preview button.

        Lets a color or position change be checked without anything needing
        to be playing.
        """
        self._set_label(LABEL_TITLE, localize(30451))
        self._set_label(LABEL_STATUS, '0:42:17 / 1:58:03')
        home_property(PROP_CHAPTER, localize(30010, 3, 24))

    def _preview_loop(self):
        """Close the preview after PREVIEW_SECONDS, unless closed sooner."""
        if not xbmc.Monitor().waitForAbort(PREVIEW_SECONDS):
            if not self._stop.is_set():
                self.close()

    def _tick_loop(self):
        """Keep the labels live and close the OSD after the idle timeout."""
        monitor = xbmc.Monitor()
        while not self._stop.is_set():
            if monitor.waitForAbort(TICK_SECONDS):
                break
            if self._stop.is_set():
                break
            if home_property(PROP_OSD_CLOSE) == '1':
                home_property(PROP_OSD_CLOSE, '')
                self.close()
                break
            if (self._timeout
                    and time.time() - self._last_input > self._timeout):
                log('closing OSD after %ds without input' % self._timeout)
                self.close()
                break
            self._refresh()


def compact_mode():
    """True when the OSD should be drawn at the smaller size - the default.

    The fallback matches settings.xml: a profile written before this setting
    existed has no value stored for it, and should still open compact.
    """
    return kodiutils.get_setting_bool('osd_compact', True)


def xml_file():
    """The window file matching the selected size."""
    return XML_FILE_COMPACT if compact_mode() else XML_FILE


def is_open():
    return home_property(PROP_OSD_OPEN) == '1'


def request_close():
    """Ask a dialog opened by another script instance to close itself."""
    home_property(PROP_OSD_CLOSE, '1')


def fallback():
    """A plain list version of the OSD.

    Used when the windowed OSD cannot be created - for instance because a
    third party skin ships an incompatible control set.  It relies only on
    Kodi's own select dialog, so it works everywhere.
    """
    commands = _build_commands()
    labels = [commands[control_id].label for control_id in BUTTON_ORDER]
    choice = xbmcgui.Dialog().select(localize(30000), labels)
    if choice < 0:
        return
    try:
        commands[BUTTON_ORDER[choice]].handler()
    except Exception as exc:  # pylint: disable=broad-except
        kodiutils.log_error('command %s failed: %s'
                            % (BUTTON_ORDER[choice], exc))
        kodiutils.notify(localize(30055))


def show():
    """Open the OSD (blocking until it closes)."""
    if is_open():
        log('OSD already open - closing it instead')
        request_close()
        return
    if not player.is_bluray_playback():
        # There is no disc to control, and the OSD would close itself again
        # on its first refresh.
        kodiutils.notify(localize(30139))
        return
    if not player.is_fullscreen_video():
        # The disc plays on, but the user has left the video screen for the
        # home screen, a file browser or another addon - not somewhere the
        # OSD belongs.
        kodiutils.notify(localize(30156))
        return
    theme.apply_theme()
    try:
        dialog = BDControlDialog(xml_file(), kodiutils.addon_path(),
                                 SKIN_FOLDER, SKIN_RESOLUTION)
    except Exception as exc:  # pylint: disable=broad-except
        kodiutils.log_error('could not create the OSD window: %s' % exc)
        fallback()
        return
    home_property(PROP_OSD_OPEN, '1')
    failed = False
    try:
        dialog.doModal()
    except Exception as exc:  # pylint: disable=broad-except
        kodiutils.log_error('the OSD window failed: %s' % exc)
        failed = True
    finally:
        dialog.wait_for_worker()
        home_property(PROP_OSD_OPEN, '')
        home_property(PROP_OSD_CLOSE, '')
        home_property(PROP_CHAPTER, '')
        del dialog
    if failed:
        fallback()


def preview():
    """Show the OSD with sample data for a few seconds.

    Lets a color, style or position change made in the settings be checked
    without needing something to be playing, or disturbing real playback if
    there is.
    """
    theme.apply_theme()
    try:
        preview_dialog = BDControlDialog(xml_file(), kodiutils.addon_path(),
                                         SKIN_FOLDER, SKIN_RESOLUTION)
    except Exception as exc:  # pylint: disable=broad-except
        kodiutils.log_error('could not create the preview OSD window: %s' % exc)
        return
    preview_dialog.preview_mode = True
    try:
        preview_dialog.doModal()
    except Exception as exc:  # pylint: disable=broad-except
        kodiutils.log_error('the preview OSD window failed: %s' % exc)
    finally:
        preview_dialog.wait_for_worker()
        del preview_dialog


def _repeated_trigger():
    """True when this trigger follows the last one too closely to be a new one.

    The timestamp lives on the Home window rather than in this process: every
    key press starts its own copy of the script, so there is nothing else the
    two could share.
    """
    now = time.time()
    try:
        last = float(home_property(PROP_OSD_TRIGGERED) or 0)
    except (TypeError, ValueError):
        last = 0.0
    home_property(PROP_OSD_TRIGGERED, '%f' % now)
    return 0 < now - last < DEBOUNCE_SECONDS


def toggle():
    """Open the OSD, or close it when it is already showing."""
    if _repeated_trigger():
        log('ignoring a repeated trigger')
        return
    if is_open():
        request_close()
        return
    show()
