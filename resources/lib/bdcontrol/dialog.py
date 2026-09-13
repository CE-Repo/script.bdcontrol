# -*- coding: utf-8 -*-
"""The BD Control on-screen display."""
import threading
import time

import xbmc
import xbmcgui

from . import actions, kodiutils, player, theme
from .kodiutils import (PROP_CHAPTER, PROP_OSD_CLOSE, PROP_OSD_OPEN,
                        PROP_OSD_RELOAD, PROP_OSD_TRIGGERED, PROP_PLACED,
                        home_property, localize, log)

# The layouts, and the window file each is drawn from.
MODE_NORMAL = 0
MODE_COMPACT = 1
MODE_SIDEBAR_LEFT = 2
MODE_SIDEBAR_RIGHT = 3
MODE_WHEEL = 4
MODE_SINGLE = 5

XML_FILES = {
    MODE_NORMAL: 'script-bdcontrol-osd.xml',
    MODE_COMPACT: 'script-bdcontrol-osd-compact.xml',
    MODE_SIDEBAR_LEFT: 'script-bdcontrol-osd-sidebar-left.xml',
    MODE_SIDEBAR_RIGHT: 'script-bdcontrol-osd-sidebar-right.xml',
    MODE_WHEEL: 'script-bdcontrol-osd-wheel.xml',
    MODE_SINGLE: 'script-bdcontrol-osd-single.xml',
}

# Both bars are the same stack of buttons; they differ only in which edge
# they rest against and travel from.
SIDEBAR_MODES = (MODE_SIDEBAR_LEFT, MODE_SIDEBAR_RIGHT)

# The layouts narrow enough to be moved sideways as well as up and down. The
# full size panel spans the screen and the sidebars belong to an edge, so for
# those the horizontal setting has nothing to offer and is greyed out.
MOVABLE_MODES = (MODE_COMPACT, MODE_WHEEL, MODE_SINGLE)
SKIN_FOLDER = 'default'
SKIN_RESOLUTION = '1080i'

# Control ids, mirroring resources/skins/default/1080i/script-bdcontrol-osd.xml
GROUP_PANEL = 2
LABEL_TITLE = 100
LABEL_STATUS = 101
LABEL_HINT = 103

# The panel of each mode, as the skin files draw it - the one thing here
# that has to be kept in step with the profiles in tools/genskin.py.
PANEL_SIZE = {
    MODE_NORMAL: (1820, 170),
    MODE_COMPACT: (1365, 128),
    MODE_SIDEBAR_LEFT: (330, 528),
    MODE_SIDEBAR_RIGHT: (330, 528),
    MODE_WHEEL: (560, 592),
    MODE_SINGLE: (700, 128),
}

# The single button layout in the icons-only style: an icon says nothing on
# its own, so that style carries the hint line and the panel is a line
# taller for it. Its window file draws the two heights the same way.
SINGLE_SIZE_WITH_HINT = (700, 150)

# The margin every mode keeps to the screen edge, matching the one the full
# size panel is drawn with.
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_MARGIN = 50


def panel_size(mode):
    """The panel's size, which for one layout depends on the button style."""
    if (mode == MODE_SINGLE
            and effective_button_style(mode) == theme.STYLE_ICONS):
        return SINGLE_SIZE_WITH_HINT
    return PANEL_SIZE[mode]


def panel_bounds(mode):
    """(left, top at 100%, top at 0%) for a mode's panel.

    Everything is derived from the panel's own size rather than written down
    a second time: these numbers went stale the moment a panel was resized,
    which is how the sidebar came to stop short of the bottom of the screen.
    """
    width, height = panel_size(mode)
    if mode in MOVABLE_MODES:
        left = (SCREEN_WIDTH - width) // 2
    elif mode == MODE_SIDEBAR_RIGHT:
        left = SCREEN_WIDTH - width - SCREEN_MARGIN
    else:
        left = SCREEN_MARGIN
    return left, SCREEN_HEIGHT - height - SCREEN_MARGIN, SCREEN_MARGIN


def left_range(mode):
    """How far a movable panel may travel sideways, margin to margin."""
    width = panel_size(mode)[0]
    return SCREEN_MARGIN, SCREEN_WIDTH - width - SCREEN_MARGIN

BUTTON_POPUP_MENU = 201
BUTTON_TOP_MENU = 202
BUTTON_KODI_OSD = 203
# Was the diagnostics button; it now carries the commands that are not
# worth a button of their own, diagnostics among them.
BUTTON_MORE = 204
BUTTON_STREAM = 205

# The icons+text style draws its label inside a grouplist next to the icon
# rather than on the button; the skin file numbers those id + offset, one for
# each focus state.
PAIR_LABEL_OFFSET = 100
PAIR_FOCUS_LABEL_OFFSET = 200

# The single button layout's one button, and the two copies of the name it
# shows - unfocused and focused, as everywhere else. The button stands for
# whichever command the step is on rather than for one of its own, which is
# why its id is not one of the five.
SINGLE_BUTTON = 210
SINGLE_LABEL = 310
SINGLE_FOCUS_LABEL = 410

# Which command the single button is on, read by its window file to show the
# matching icon.
PROP_STEP = 'BDControl.Step'

# The layouts whose window file has no hint line to write to. The wheel
# names every segment it draws and has no room for a second line.
HINTLESS_MODES = (MODE_WHEEL,)

# The control each layout opens with the remote on. Only the single button
# layout differs: its one button stands for every command, so none of the
# five ids the other layouts use exists in it.
DEFAULT_FOCUS = {MODE_SINGLE: SINGLE_BUTTON}

# Kodi's left and right. In every other layout these move focus from button
# to button; the single button layout has only the one, so they step it.
ACTION_MOVE_LEFT = 1
ACTION_MOVE_RIGHT = 2

# Buttons the wide layouts draw square and icon-only, whatever the selected
# button style - they have no label of either kind to fill in. The sidebar
# stacks them all alike and singles none of them out.
ICON_ONLY_BUTTONS = (BUTTON_MORE,)

# Left to right, matching the skin file and the plain-list fallback. The ids
# are not in order here: they were handed out as the buttons were added, the
# row has been arranged since.
BUTTON_ORDER = (BUTTON_KODI_OSD, BUTTON_STREAM, BUTTON_POPUP_MENU,
                BUTTON_TOP_MENU, BUTTON_MORE)

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
        # The one command that leaves the OSD standing: its menu offers a way
        # back, and a way back needs something to come back to.
        BUTTON_STREAM: Command(30117, 30462, actions.stream_menu),
        # Leaves the OSD standing, as the Stream button does: its menu
        # offers a way back, and a way back needs something to come back to.
        BUTTON_MORE: Command(30238, 30463, actions.more_menu),
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
        # Which command the single button layout is on, as an index into
        # BUTTON_ORDER. The other layouts show all five at once and leave it
        # alone.
        self._step = 0
        # Set while a command of ours is running. One that leaves the OSD
        # open puts a menu of its own on top, and the OSD sees no input for
        # as long as that menu is up - which the idle timeout would read as
        # an idle user and close the OSD out from under it.
        self._in_command = False
        # Which of the window files this instance was built from - the panel
        # geometry differs per mode, so _apply_position has to know.
        self._mode = osd_mode()
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
            return
        if self._mode != MODE_SINGLE:
            return
        # One button, so left and right have no neighbour to move to; they
        # step the button through the commands instead. The button's own
        # navigation leads back to itself, so focus never leaves it and the
        # action arrives here.
        if action.getId() == ACTION_MOVE_LEFT:
            self._set_step(self._step - 1)
        elif action.getId() == ACTION_MOVE_RIGHT:
            self._set_step(self._step + 1)

    def onClick(self, control_id):
        self._touch()
        if self.preview_mode:
            # Sample data only - a click must not run a real player command.
            return
        command = self.commands.get(self._command_id(control_id))
        if command is None:
            return
        if command.closes:
            self.close()
        self._in_command = True
        # A command that leaves the OSD standing still puts a menu of its own
        # on top of it, and two menus over each other is one too many. The
        # panel goes off the screen the same way it came on - by way of the
        # property it hangs off - and comes back when the command is done,
        # which is what the menu's own way back leads to.
        steps_aside = not command.closes
        if steps_aside:
            home_property(PROP_PLACED, '')
        try:
            command.handler()
        except Exception as exc:  # pylint: disable=broad-except
            kodiutils.log_error('command %s failed: %s' % (control_id, exc))
            kodiutils.notify(localize(30055))
        finally:
            self._in_command = False
            self._touch()
            if steps_aside and not self._closing:
                home_property(PROP_PLACED, '1')
        if home_property(PROP_OSD_RELOAD) == '1':
            # Settings were changed, and this window was built from the old
            # ones. It closes; show() opens one built from the new ones.
            self.close()
            return
        if not self._closing:
            self._refresh()

    def onFocus(self, control_id):
        self._touch()
        command = self.commands.get(self._command_id(control_id))
        if (self._mode in HINTLESS_MODES
                or effective_button_style(self._mode) != theme.STYLE_ICONS):
            # The hint line explains an icon that carries no words of its
            # own, so the skin files show it for that style alone - and the
            # wheel, which names every segment it draws, has no such control
            # to write to at all.
            return
        self._set_label(LABEL_HINT, command.hint if command else '')

    # -- rendering --------------------------------------------------------

    def _apply_position(self):
        """Move the panel to the configured vertical position.

        100% is the bottom of the screen and the default; 0% moves it to a
        small margin below the top edge. Sideways only the panels narrower
        than the screen can move: the full size one spans it, and a sidebar
        that has left its edge is no longer a sidebar.
        """
        left, bottom, ceiling = panel_bounds(self._mode)
        percent = max(0, min(100, kodiutils.get_setting_int('osd_position_y', 100)))
        top = ceiling + round((bottom - ceiling) * percent / 100)
        if self._mode in MOVABLE_MODES:
            across = max(0, min(100,
                                kodiutils.get_setting_int('osd_position_x', 50)))
            leftmost, rightmost = left_range(self._mode)
            left = leftmost + round((rightmost - leftmost) * across / 100)
        try:
            self.getControl(GROUP_PANEL).setPosition(left, top)
        except Exception:  # pylint: disable=broad-except
            pass
        # Only now is the panel where the settings want it, so only now may
        # it be drawn: the window file knows one position, and every other
        # one would show there for a frame and then jump. The skin file
        # hides the panel until this says otherwise and opens it from here.
        home_property(PROP_PLACED, '1')
        # The panel was hidden while the window handed out its default
        # focus, so that focus went nowhere; it has to be given again - and
        # to the button this layout actually has. Left unfocused, the button
        # draws itself in the unfocused colours, which is what gave the
        # single button layout the wrong text colour on opening.
        try:
            self.setFocusId(DEFAULT_FOCUS.get(self._mode, BUTTON_KODI_OSD))
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
        style = effective_button_style(self._mode)
        wordless = style == theme.STYLE_ICONS
        if self._mode == MODE_SINGLE:
            # One button, one name: the step decides which, and writing it
            # out is the same work as moving to it.
            self._set_step(self._step)
            return
        if self._mode == MODE_WHEEL:
            # Every segment carries its own name, the diagnostics one too:
            # the wheel gives each the same wedge, and an unnamed icon among
            # four named ones reads as a mistake. The name is a label of its
            # own rather than the button's, in a focused and an unfocused
            # copy, since a label control has no colour of its own to switch.
            for control_id, command in self.commands.items():
                self._set_label(control_id, '')
                self._set_label(control_id + PAIR_LABEL_OFFSET, command.label)
                self._set_label(control_id + PAIR_FOCUS_LABEL_OFFSET,
                                command.label)
            return
        if self._mode in SIDEBAR_MODES:
            # Stacked, the icon is an overlay on the left and the button
            # draws its own centred label, so one label carries both text
            # styles and there is no grouplist pair to fill.
            for control_id, command in self.commands.items():
                self._set_label(control_id, '' if wordless else command.label)
            return
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

    def _command_id(self, control_id):
        """The command a clicked or focused control stands for.

        Every layout but one has a button per command, and the control id is
        the answer; the single button layout has one button standing for
        whichever command its step is on.
        """
        if control_id == SINGLE_BUTTON:
            return BUTTON_ORDER[self._step % len(BUTTON_ORDER)]
        return control_id

    def _set_step(self, step):
        """Move the single button to another command and show it.

        The step wraps: five commands in a ring is what makes one button
        enough, and a step that stopped at either end would leave the user
        pressing against nothing.
        """
        self._step = step % len(BUTTON_ORDER)
        command = self.commands[BUTTON_ORDER[self._step]]
        home_property(PROP_STEP, str(self._step))
        # The name goes wherever the chosen style shows it: on the button
        # itself when it stands alone, in the grouplist when it is paired
        # with the icon, and nowhere at all for icons only. Same division of
        # labour as the wide layouts, for one button rather than five.
        style = effective_button_style(self._mode)
        self._set_label(SINGLE_BUTTON,
                        command.label if style == theme.STYLE_TEXT else '')
        paired = command.label if style == theme.STYLE_ICONS_AND_TEXT else ''
        self._set_label(SINGLE_LABEL, paired)
        self._set_label(SINGLE_FOCUS_LABEL, paired)
        # Icons only: the panel grows a line for what the command does, since
        # an icon on its own says nothing. The other styles name it already.
        self._set_label(LABEL_HINT,
                        command.hint if style == theme.STYLE_ICONS else '')

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
            if (self._timeout and not self._in_command
                    and time.time() - self._last_input > self._timeout):
                log('closing OSD after %ds without input' % self._timeout)
                self.close()
                break
            self._refresh()


def effective_button_style(mode):
    """The button style a layout draws with.

    The sidebars prescribe icons with text and ignore the setting: their
    buttons are as wide as the bar, which leaves an icon alone stranded in a
    corner and a label alone with an empty stripe beside it. The wheel
    prescribes icons with text for the same kind of reason: a wedge is not a
    stripe either, and the name belongs under the icon. The setting is greyed
    out for those layouts, and this is what makes that true rather than
    merely advertised.
    """
    if mode in SIDEBAR_MODES:
        return theme.STYLE_ICONS_AND_TEXT
    if mode == MODE_WHEEL:
        # A segment is roomy enough for the icon with the name under it, and
        # a wheel whose segments are unnamed makes the icons guesswork.
        return theme.STYLE_ICONS_AND_TEXT
    return theme.button_style()


def osd_mode():
    """The selected layout, falling back to compact - the default.

    An unknown value means a settings file from a newer version than this
    code, so it is treated as the default rather than crashing the OSD.
    """
    mode = kodiutils.get_setting_int('osd_mode', MODE_COMPACT)
    return mode if mode in XML_FILES else MODE_COMPACT


def xml_file():
    """The window file matching the selected layout."""
    return XML_FILES[osd_mode()]


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
    # Usually one window and done. Settings changed from inside the OSD ask
    # for another one: the layout decides which file the window is built
    # from, and the colours are written to its properties as it opens, so
    # neither reaches a window that is already standing. Opening the new one
    # has to happen out here, after the command that asked has returned.
    while True:
        home_property(PROP_OSD_RELOAD, '')
        _show_once()
        if home_property(PROP_OSD_RELOAD) != '1':
            return
        log('settings changed - opening the OSD again')


def _show_once():
    """One run of the OSD window, from opening it to cleaning up after it."""
    theme.apply_theme(effective_button_style(osd_mode()))
    try:
        dialog = BDControlDialog(xml_file(), kodiutils.addon_path(),
                                 SKIN_FOLDER, SKIN_RESOLUTION)
    except Exception as exc:  # pylint: disable=broad-except
        kodiutils.log_error('could not create the OSD window: %s' % exc)
        fallback()
        return
    home_property(PROP_OSD_OPEN, '1')
    home_property(PROP_PLACED, '')
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
        # PROP_PLACED is deliberately left standing: the panel hangs off it,
        # and clearing it here would take the panel off the screen while the
        # closing animation is still playing it out. The next OSD clears it
        # before it opens, which is the only moment it has to be false.
        del dialog
    if failed:
        fallback()


def preview():
    """Show the OSD with sample data for a few seconds.

    Lets a color, style or position change made in the settings be checked
    without needing something to be playing, or disturbing real playback if
    there is.
    """
    theme.apply_theme(effective_button_style(osd_mode()))
    try:
        preview_dialog = BDControlDialog(xml_file(), kodiutils.addon_path(),
                                         SKIN_FOLDER, SKIN_RESOLUTION)
    except Exception as exc:  # pylint: disable=broad-except
        kodiutils.log_error('could not create the preview OSD window: %s' % exc)
        return
    preview_dialog.preview_mode = True
    home_property(PROP_PLACED, '')
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
