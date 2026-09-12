# -*- coding: utf-8 -*-
"""Argument handling for RunScript(script.bdcontrol, ...)."""
import xbmcgui

from . import actions, dialog, keymap, kodiutils, learn, tools
from .kodiutils import localize, log


def parse_args(argv):
    """Turn `['action=toggle', 'seconds=30']` into a dict.

    A bare first argument is accepted as the action as well, so both
    `RunScript(script.bdcontrol,toggle)` and
    `RunScript(script.bdcontrol,action=toggle)` work.
    """
    args = {}
    for position, raw in enumerate(argv):
        if not raw:
            continue
        if '=' in raw:
            key, _, value = raw.partition('=')
            args[key.strip().lower()] = value.strip()
        elif position == 0:
            args['action'] = raw.strip().lower()
    return args


def main_menu():
    """The menu shown when the addon is started from the Kodi UI."""
    entries = [
        (localize(30001), dialog.show),
        (localize(30028), actions.kodi_osd),
        (localize(30032), actions.browse_titles),
        (localize(30033), actions.disc_playback_mode),
        (localize(30002), keymap.install),
        (localize(30003), keymap.uninstall),
        (localize(30116), learn.learn_button),
        (localize(30121), learn.show_recent_keys),
        (localize(30034), tools.show_diagnostics),
        (localize(30004), kodiutils.open_settings),
    ]
    choice = xbmcgui.Dialog().select(localize(30000),
                                     [entry[0] for entry in entries])
    if choice < 0:
        return
    entries[choice][1]()


HANDLERS = {
    'toggle': dialog.toggle,
    'show': dialog.show,
    'osd': actions.kodi_osd,
    'menu': main_menu,
    'discmenu': actions.disc_menu,
    'popupmenu': actions.disc_popup_menu,
    'topmenu': actions.disc_top_menu,
    'playpause': actions.play_pause,
    'stop': actions.stop,
    'nextchapter': actions.chapter_next,
    'previouschapter': actions.chapter_previous,
    'audio': actions.choose_audio,
    'subtitles': actions.choose_subtitle,
    'titles': actions.browse_titles,
    'discmode': actions.disc_playback_mode,
    'eject': actions.eject,
    'learn': learn.learn_button,
    'keylog': learn.show_recent_keys,
    'diagnostics': tools.show_diagnostics,
    'logdiagnostics': tools.copy_diagnostics_to_log,
    'install_keymap': keymap.install,
    'remove_keymap': keymap.uninstall,
    'settings': kodiutils.open_settings,
}


def run(argv):
    args = parse_args(argv)
    action = args.get('action', 'menu')
    log('run: action=%s args=%s' % (action, args))

    if action == 'seek':
        try:
            seconds = int(args.get('seconds', 30))
        except (TypeError, ValueError):
            seconds = 30
        actions.seek(seconds)
        return

    handler = HANDLERS.get(action)
    if handler is None:
        kodiutils.log_error('unknown action "%s"' % action)
        kodiutils.notify(localize(30057, action))
        return
    handler()
