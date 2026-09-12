# -*- coding: utf-8 -*-
"""Background service: says that BD Control is there once a disc menu takes
over the remote.

That hangs on recognising the Blu-ray, which is not something that can be done
once when playback starts: libbluray needs a moment before Kodi reports a disc
menu, and for some sources that report is the only thing that identifies the
disc at all.  So the check is repeated on every tick until it succeeds, and
once it has, it stays true until playback ends.

Everything here has to cope with one thing a Blu-ray menu does that no other
kind of video does: it swaps titles constantly, and every swap produces
another round of Kodi playback callbacks plus a moment in which Kodi reports
no video at all.  Treating any of that as "a new item" or as "playback ended"
makes the service announce itself over and over, so a session begins and ends
exactly once - see `on_playback_started` and `_evaluate`.
"""
import time

import xbmc

from . import dialog, kodiutils, player
from .kodiutils import execute_builtin, localize, log_info

TICK_SECONDS = 0.5

# How long Kodi has to report no video before the session counts as over.
# Title swaps inside a disc menu produce gaps well under a second.
STOP_GRACE_SECONDS = 5.0


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
        self.monitor = xbmc.Monitor()
        self.player = BDPlayer(self)
        self._current_path = ''
        self._announced = False
        self._is_bluray = False
        self._idle_since = 0.0

    # -- playback ---------------------------------------------------------

    def on_playback_started(self):
        path = player.playing_file()
        if not path:
            return
        if self._current_path:
            # A session is already running. Every title a disc menu jumps to
            # calls back in here again; that is the same disc, not a new item,
            # and re-announcing on each one is what makes the OSD reappear the
            # moment the user closes it.
            self._current_path = path
            return
        self._current_path = path
        self._announced = False
        self._is_bluray = False
        self._idle_since = 0.0
        log_info('playback started: %s' % player.describe_playback())
        self._evaluate()

    def on_playback_stopped(self):
        if self._current_path:
            log_info('playback stopped')
        self._current_path = ''
        self._announced = False
        self._is_bluray = False
        self._idle_since = 0.0
        if dialog.is_open():
            dialog.request_close()

    def _evaluate(self):
        """Recognise the Blu-ray, then announce once its menu takes over.

        Only ever latches on: `is_bluray_playback()` partly rests on Kodi
        reporting a disc menu, and that comes and goes while the disc plays.
        """
        if not self._current_path:
            return
        if not player.is_playing_video():
            # Not necessarily the end: Kodi reports no video for a moment on
            # every title swap inside a disc menu. Only a sustained gap means
            # playback really finished without a callback reaching us.
            now = time.time()
            if not self._idle_since:
                self._idle_since = now
            elif now - self._idle_since > STOP_GRACE_SECONDS:
                self.on_playback_stopped()
            return
        self._idle_since = 0.0
        if not self._is_bluray:
            if not player.is_bluray_playback():
                return
            self._is_bluray = True
            log_info('recognised as a Blu-ray: %s'
                     % player.describe_playback())
        if not self._announced and player.has_disc_menu():
            self._announced = True
            self._announce()

    def _announce(self):
        if dialog.is_open():
            # Never talk over an OSD the user opened themselves.
            return
        if kodiutils.get_setting_bool('auto_open', False):
            # Run as a separate script so the service loop stays responsive
            # while the modal OSD is up.
            execute_builtin('RunScript(script.bdcontrol)')
        elif kodiutils.get_setting_bool('show_hint', False):
            kodiutils.notify(localize(30058), time=7000)

    # -- main loop --------------------------------------------------------

    def run(self):
        log_info('BD Control %s service started' % kodiutils.addon_version())
        while not self.monitor.abortRequested():
            if self.monitor.waitForAbort(TICK_SECONDS):
                break
            self._evaluate()
        log_info('BD Control service stopped')


def main():
    Service().run()
