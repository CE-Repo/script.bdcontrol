# -*- coding: utf-8 -*-
"""Commands BD Control can run on behalf of the user.

While a disc menu drives playback, Kodi routes navigation actions (including
OK) to the disc, which is why the regular OSD cannot be opened.  The commands
below deliberately use two different mechanisms:

* Builtins such as `PlayerControl` act on the player directly and work no
  matter which window has focus.
* `ActivateWindow(...)` is delivered to the *active* window, so anything that
  has to replace our OSD must be run after the BD Control dialog has closed.
  Those commands are marked `closes=True` in the dialog's command table.
"""
from .kodiutils import execute_builtin, jsonrpc

DISC_PLAYBACK_SETTING = 'disc.playback'


# --- Kodi windows ---------------------------------------------------------

def kodi_osd():
    """Open Kodi's own player OSD.

    This is the direct answer to "OK does nothing": activating the window by
    name bypasses the disc's grip on the OK button entirely.
    """
    execute_builtin('ActivateWindow(videoosd)')


# --- disc ----------------------------------------------------------------

def disc_popup_menu():
    """Open the in-movie popup menu.

    `PlayerControl(...)` goes straight to the player rather than to the active
    window, so unlike `Action(showvideomenu)` it does not depend on which
    window has focus.

    Note that upstream Kodi matches the builtin parameter exactly (`paramlow
    == "showvideomenu"`), so the argument form is *silently ignored* there:
    telling the popup and the top menu apart needs a build carrying the
    ShowVideoMenu(popup|top) patch - SamuriHL's CoreELEC build among them.
    There is no way to probe for the patch from a script.
    """
    execute_builtin('PlayerControl(ShowVideoMenu(popup))')


def disc_top_menu():
    """Open the disc's top/root menu."""
    execute_builtin('PlayerControl(ShowVideoMenu(top))')


# --- Kodi settings --------------------------------------------------------

def disc_playback_options():
    """Return (current_value, [(value, label), ...]) for `disc.playback`.

    Read-only; the diagnostics report names the mode Kodi is in, because
    playing discs without their menus is the permanent way out of the problem
    BD Control works around.
    """
    value = jsonrpc('Settings.GetSettingValue', setting=DISC_PLAYBACK_SETTING)
    current = (value or {}).get('value')

    definition = None
    result = jsonrpc('Settings.GetSettings', level='expert',
                     filter={'section': 'player', 'category': 'discs'})
    for setting in (result or {}).get('settings') or []:
        if setting.get('id') == DISC_PLAYBACK_SETTING:
            definition = setting
            break
    if definition is None:
        result = jsonrpc('Settings.GetSettings', level='expert')
        for setting in (result or {}).get('settings') or []:
            if setting.get('id') == DISC_PLAYBACK_SETTING:
                definition = setting
                break
    options = []
    for option in (definition or {}).get('options') or []:
        options.append((option.get('value'), option.get('label')))
    return current, options
