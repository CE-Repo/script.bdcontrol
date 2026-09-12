# -*- coding: utf-8 -*-
"""Argument handling for RunScript(script.bdcontrol, ...)."""
from . import actions, dialog, kodiutils, theme, tools
from .kodiutils import localize, log


def parse_args(argv):
    """Turn `['action=osd']` into a dict.

    A bare first argument is accepted as the action as well, so both
    `RunScript(script.bdcontrol,popupmenu)` and
    `RunScript(script.bdcontrol,action=popupmenu)` work.
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


# The commands BD Control offers. `auto` is what a bare
# `RunScript(script.bdcontrol)` runs, which is how Keymap Editor's "Add-ons"
# category writes a binding, and how the addon is started from the Kodi UI.
HANDLERS = {
    'auto': dialog.toggle,
    'osd': actions.kodi_osd,
    'popupmenu': actions.disc_popup_menu,
    'topmenu': actions.disc_top_menu,
    'diagnostics': tools.show_diagnostics,

    # Internal, used by the buttons in the addon's own settings dialog.
    'previewosd': dialog.preview,
}


def run(argv):
    args = parse_args(argv)
    action = args.get('action') or 'auto'
    log('run: action=%s args=%s' % (action, args))

    if action == 'customcolor':
        # Internal: the HEX colour picker behind each appearance setting.
        theme.custom_color(args.get('id', ''))
        return

    handler = HANDLERS.get(action)
    if handler is None:
        kodiutils.log_error('unknown action "%s"' % action)
        kodiutils.notify(localize(30057, action))
        return
    handler()
