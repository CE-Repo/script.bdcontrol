# -*- coding: utf-8 -*-
"""The BD Control on-screen display."""
import threading
import time

import xbmc
import xbmcgui

from . import actions, kodiutils, player, tools
from .kodiutils import (PROP_OSD_CLOSE, PROP_OSD_OPEN, home_property, localize,
                        log)

XML_FILE = 'script-bdcontrol-osd.xml'
SKIN_FOLDER = 'default'
SKIN_RESOLUTION = '1080i'

# Control ids, mirroring resources/skins/default/1080i/script-bdcontrol-osd.xml
LABEL_TITLE = 100
LABEL_STATUS = 101
PROGRESS = 102
LABEL_HINT = 103

BUTTON_DISC_MENU = 201
BUTTON_PLAY_PAUSE = 202
BUTTON_STOP = 203
BUTTON_CHAPTER_PREV = 204
BUTTON_CHAPTER_NEXT = 205
BUTTON_SEEK_BACK = 206
BUTTON_SEEK_FORWARD = 207

BUTTON_KODI_OSD = 301
BUTTON_AUDIO = 302
BUTTON_SUBTITLES = 303
BUTTON_VIDEO_SETTINGS = 304
BUTTON_CODEC_INFO = 305
BUTTON_TITLES = 306
BUTTON_MORE = 307

ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92
ACTION_STOP = 13
ACTION_PLAYER_PLAY = 79
ACTION_PAUSE = 12

CLOSE_ACTIONS = (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK)

TICK_SECONDS = 0.5


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
        BUTTON_DISC_MENU: Command(30020, 30040, actions.disc_menu, closes=True),
        BUTTON_PLAY_PAUSE: Command(30021, 30041, actions.play_pause),
        BUTTON_STOP: Command(30022, 30042, actions.stop, closes=True),
        BUTTON_CHAPTER_PREV: Command(30023, 30043, actions.chapter_previous),
        BUTTON_CHAPTER_NEXT: Command(30024, 30044, actions.chapter_next),
        BUTTON_SEEK_BACK: Command(30025, 30045, actions.seek_backward),
        BUTTON_SEEK_FORWARD: Command(30027, 30046, actions.seek_forward),
        BUTTON_KODI_OSD: Command(30028, 30047, actions.kodi_osd, closes=True),
        BUTTON_AUDIO: Command(30030, 30048, actions.choose_audio),
        BUTTON_SUBTITLES: Command(30031, 30049, actions.choose_subtitle),
        BUTTON_VIDEO_SETTINGS: Command(30029, 30050, actions.video_settings,
                                       closes=True),
        BUTTON_CODEC_INFO: Command(30051, 30052, actions.process_info,
                                   closes=True),
        BUTTON_TITLES: Command(30032, 30053, actions.browse_titles,
                               closes=True),
        BUTTON_MORE: Command(30026, 30054, None),
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

    # -- lifecycle --------------------------------------------------------

    def onInit(self):
        for control_id, command in self.commands.items():
            self._set_label(control_id, command.label)
        self._refresh()
        self._touch()
        if self._worker is None:
            self._worker = threading.Thread(target=self._tick_loop)
            self._worker.daemon = True
            self._worker.start()

    def close(self):
        if self._closing:
            return
        self._closing = True
        self._stop.set()
        super(BDControlDialog, self).close()

    def wait_for_worker(self):
        self._stop.set()
        if self._worker is not None and self._worker.is_alive():
            self._worker.join(2.0)
        self._worker = None

    # -- input ------------------------------------------------------------

    def onAction(self, action):
        action_id = action.getId()
        self._touch()
        if action_id in CLOSE_ACTIONS:
            self.close()
            return
        if action_id in (ACTION_STOP,):
            self.close()
            actions.stop()
            return
        if action_id in (ACTION_PAUSE, ACTION_PLAYER_PLAY):
            actions.play_pause()
            self._refresh()
            return

    def onClick(self, control_id):
        self._touch()
        command = self.commands.get(control_id)
        if command is None:
            return
        if control_id == BUTTON_MORE:
            tools.more_menu(closer=self.close)
            if not self._closing:
                self._refresh()
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

    def _touch(self):
        self._last_input = time.time()

    def _set_label(self, control_id, text):
        try:
            self.getControl(control_id).setLabel(text)
        except Exception:  # pylint: disable=broad-except
            # The control is gone once the window closes; nothing to do.
            pass

    def _set_progress(self, percentage):
        try:
            self.getControl(PROGRESS).setPercent(float(percentage))
        except Exception:  # pylint: disable=broad-except
            pass

    def _refresh(self):
        state = player.PlayerState()
        self._set_label(LABEL_TITLE, state.title())
        self._set_label(LABEL_STATUS, state.describe())
        self._set_progress(state.percentage)
        self._set_label(
            BUTTON_PLAY_PAUSE,
            localize(30021) if not state.paused else localize(30056))
        step = max(kodiutils.get_setting_int('seek_step', 30), 1)
        self._set_label(BUTTON_SEEK_BACK, localize(30025, step))
        self._set_label(BUTTON_SEEK_FORWARD, localize(30027, step))
        if not state.playing:
            # Playback ended while the OSD was open - there is nothing to
            # control any more.
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


def is_open():
    return home_property(PROP_OSD_OPEN) == '1'


def request_close():
    """Ask a dialog opened by another script instance to close itself."""
    home_property(PROP_OSD_CLOSE, '1')


FALLBACK_ORDER = (
    BUTTON_KODI_OSD,
    BUTTON_PLAY_PAUSE,
    BUTTON_STOP,
    BUTTON_DISC_MENU,
    BUTTON_CHAPTER_PREV,
    BUTTON_CHAPTER_NEXT,
    BUTTON_SEEK_BACK,
    BUTTON_SEEK_FORWARD,
    BUTTON_AUDIO,
    BUTTON_SUBTITLES,
    BUTTON_VIDEO_SETTINGS,
    BUTTON_CODEC_INFO,
    BUTTON_TITLES,
    BUTTON_MORE,
)


def fallback():
    """A plain list version of the OSD.

    Used when the windowed OSD cannot be created - for instance because a
    third party skin ships an incompatible control set.  It relies only on
    Kodi's own select dialog, so it works everywhere.
    """
    commands = _build_commands()
    order = list(FALLBACK_ORDER)
    labels = []
    for control_id in order:
        command = commands[control_id]
        label = command.label
        if control_id in (BUTTON_SEEK_BACK, BUTTON_SEEK_FORWARD):
            label = localize(command.label_id,
                             max(kodiutils.get_setting_int('seek_step', 30), 1))
        labels.append(label)
    choice = xbmcgui.Dialog().select(localize(30000), labels)
    if choice < 0:
        return
    control_id = order[choice]
    if control_id == BUTTON_MORE:
        tools.more_menu()
        return
    try:
        commands[control_id].handler()
    except Exception as exc:  # pylint: disable=broad-except
        kodiutils.log_error('command %s failed: %s' % (control_id, exc))
        kodiutils.notify(localize(30055))


def show():
    """Open the OSD (blocking until it closes)."""
    if is_open():
        log('OSD already open - closing it instead')
        request_close()
        return
    if not player.is_playing_video():
        # There is nothing to control, and the OSD would close itself again
        # on its first refresh.
        kodiutils.notify(localize(30102))
        return
    try:
        dialog = BDControlDialog(XML_FILE, kodiutils.addon_path(), SKIN_FOLDER,
                                 SKIN_RESOLUTION)
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
        del dialog
    if failed:
        fallback()


def toggle():
    """Open the OSD, or close it when it is already showing."""
    if is_open():
        request_close()
        return
    show()
