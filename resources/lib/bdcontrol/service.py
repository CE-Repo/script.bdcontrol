# -*- coding: utf-8 -*-
"""Background service: keeps the keymap in sync and watches disc playback."""
import time

import xbmc

from . import dialog, keymap, kodiutils, player
from .kodiutils import execute_builtin, localize, log, log_info

# libbluray needs a moment after playback starts before Kodi reports that a
# disc menu is driving the input, so the check is retried for a few seconds.
MENU_CHECK_TIMEOUT = 6.0
TICK_SECONDS = 0.5
# Another addon can rename our keymap out of the way at any time; checking for
# that is one os.listdir, so half a minute is frequent enough.
CONFLICT_CHECK_SECONDS = 30.0


class BDMonitor(xbmc.Monitor):
    """Reacts to settings changes."""

    def __init__(self, service):
        super(BDMonitor, self).__init__()
        self._service = service

    def onSettingsChanged(self):
        log('settings changed')
        self._service.request_keymap_sync()


class BDPlayer(xbmc.Player):
    """Reacts to playback starting and stopping."""

    def __init__(self, service):
        super(BDPlayer, self).__init__()
        self._service = service

    def onAVStarted(self):
        self._service.on_playback_started()

    def onPlayBackStarted(self):
        # Some builds only emit onPlayBackStarted; the service ignores the
        # second call for the same item.
        self._service.on_playback_started()

    def onPlayBackStopped(self):
        self._service.on_playback_stopped()

    def onPlayBackEnded(self):
        self._service.on_playback_stopped()


class Service(object):
    """Everything here is driven from the service thread.

    The Kodi player callbacks only record what happened; the work is done in
    `run()` so a slow check or a dialog never blocks Kodi's own callback
    thread.
    """

    def __init__(self):
        self.monitor = BDMonitor(self)
        self.player = BDPlayer(self)
        self._announced_for = ''
        self._pending_path = ''
        self._pending_until = 0.0
        self._keymap_dirty = False
        self._conflict_warned = False
        self._next_conflict_check = 0.0

    # -- keymap -----------------------------------------------------------

    def request_keymap_sync(self):
        self._keymap_dirty = True

    def _sync_keymap(self):
        self._keymap_dirty = False
        try:
            keymap.sync()
        except Exception as exc:  # pylint: disable=broad-except
            kodiutils.log_error('keymap sync failed: %s' % exc)

    def _check_keymap_conflict(self):
        """Restore our keymap if another addon renamed it away.

        Keymap Editor moves every other keymap file aside when it saves, which
        silently takes the BD Control trigger with it.  The setting is the
        source of truth, so put the file back and say what happened - the
        diagnostics page explains how to stop it recurring.
        """
        if not kodiutils.get_setting_bool('keymap_enabled', True):
            return
        if keymap.is_installed():
            self._conflict_warned = False
            return
        copies = keymap.disabled_copies()
        if not copies:
            return
        if not self._conflict_warned:
            self._conflict_warned = True
            log_info('keymap was renamed away by another addon: %s'
                     % ', '.join(copies))
            kodiutils.notify(localize(30131), time=9000)
        self._sync_keymap()

    # -- playback ---------------------------------------------------------

    def on_playback_started(self):
        path = player.playing_file()
        if not path or path == self._announced_for:
            return
        if not player.is_disc_playback(path):
            return
        self._announced_for = path
        self._pending_path = path
        self._pending_until = time.time() + MENU_CHECK_TIMEOUT
        log_info('disc playback started: %s' % path)

    def on_playback_stopped(self):
        self._announced_for = ''
        self._pending_path = ''
        if dialog.is_open():
            dialog.request_close()

    def _process_pending(self):
        """Announce BD Control once a disc menu has taken over the remote."""
        if not self._pending_path:
            return
        if not player.is_playing_video():
            self._pending_path = ''
            return
        if player.has_disc_menu():
            self._pending_path = ''
            self._announce()
            return
        if time.time() > self._pending_until:
            log('no disc menu reported for this item')
            self._pending_path = ''

    def _announce(self):
        if kodiutils.get_setting_bool('auto_open', False):
            # Run as a separate script so the service loop stays responsive
            # while the modal OSD is up.
            execute_builtin('RunScript(script.bdcontrol,action=show)')
        elif kodiutils.get_setting_bool('show_hint', True):
            kodiutils.notify(self._hint_text(), time=7000)

    def _hint_text(self):
        """Tell the user how to open BD Control, given what is assigned."""
        osd = keymap.slot('osd')
        if not kodiutils.get_setting_bool('keymap_enabled', True) or not osd.code:
            return localize(30058)
        return localize(30059) if osd.longpress else localize(30152)

    # -- main loop --------------------------------------------------------

    def run(self):
        log_info('BD Control %s service started' % kodiutils.addon_version())
        keymap.migrate_old_settings()
        self._sync_keymap()
        while not self.monitor.abortRequested():
            if self.monitor.waitForAbort(TICK_SECONDS):
                break
            if self._keymap_dirty:
                self._sync_keymap()
            now = time.time()
            if now >= self._next_conflict_check:
                self._next_conflict_check = now + CONFLICT_CHECK_SECONDS
                self._check_keymap_conflict()
            self._process_pending()
        log_info('BD Control service stopped')


def main():
    Service().run()
