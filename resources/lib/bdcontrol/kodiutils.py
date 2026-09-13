# -*- coding: utf-8 -*-
"""Thin wrappers around the Kodi Python API used throughout the addon."""
import hashlib
import json
import os

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

ADDON_ID = 'script.bdcontrol'

# Window properties are stored on the Home window so every instance of the
# script (and the service) can see them.
HOME_WINDOW = 10000

PROP_OSD_OPEN = 'bdcontrol.osd.open'
PROP_OSD_CLOSE = 'bdcontrol.osd.close'
PROP_OSD_TRIGGERED = 'bdcontrol.osd.triggered'
# Set when the OSD has to be built again rather than carried on with - a
# layout picked in the settings names a different window file, and a window
# cannot become another one. Read by show() once the command that set it has
# returned; nothing can reopen the window it is running inside.
PROP_OSD_RELOAD = 'bdcontrol.osd.reload'

# Read by the skin file rather than by us: the chapter tab takes its text
# from here and hides itself while it is empty.
PROP_CHAPTER = 'BDControl.Chapter'

# Also read by the skin file: the panel stays hidden until onInit has moved
# it to the configured position. A window file can only name one position,
# and any other setting would show for a frame there before the move.
PROP_PLACED = 'BDControl.Placed'


def addon():
    """Return a fresh Addon object (settings are cached per instance)."""
    return xbmcaddon.Addon(ADDON_ID)


def addon_path():
    return xbmcvfs.translatePath(addon().getAddonInfo('path'))


def addon_profile():
    return xbmcvfs.translatePath(addon().getAddonInfo('profile'))


def addon_version():
    return addon().getAddonInfo('version')


def localize(string_id, *args):
    """Return a localised string, optionally formatted with `args`."""
    text = addon().getLocalizedString(string_id)
    if not text:
        text = str(string_id)
    if args:
        try:
            text = text % args
        except (TypeError, ValueError):
            pass
    return text


def get_setting(setting_id, default=''):
    try:
        return addon().getSetting(setting_id)
    except Exception:  # pylint: disable=broad-except
        return default


def get_setting_bool(setting_id, default=False):
    try:
        return addon().getSettingBool(setting_id)
    except Exception:  # pylint: disable=broad-except
        value = get_setting(setting_id)
        if value in ('true', 'false'):
            return value == 'true'
        return default


def get_setting_int(setting_id, default=0):
    try:
        return addon().getSettingInt(setting_id)
    except Exception:  # pylint: disable=broad-except
        try:
            return int(get_setting(setting_id))
        except (TypeError, ValueError):
            return default


def settings_fingerprint():
    """What the addon's settings look like right now, as one value.

    Everything the OSD is drawn from lives in these two files - the settings
    Kodi writes, and the custom colours the HEX picker keeps beside them -
    so the same value before and after the settings dialog means nothing the
    OSD cares about has moved. Missing files count as empty, which is what a
    first run looks like.
    """
    digest = hashlib.md5()
    for name in ('settings.xml', 'custom_colors.json'):
        try:
            with open(os.path.join(addon_profile(), name), 'rb') as handle:
                digest.update(handle.read())
        except OSError:
            pass
        digest.update(b'|')
    return digest.hexdigest()


def open_settings():
    """Open this addon's own settings dialog."""
    addon().openSettings()


def log(message, level=xbmc.LOGDEBUG):
    """Log to kodi.log. Debug lines are only written when enabled."""
    if level == xbmc.LOGDEBUG and not get_setting_bool('debug_log', False):
        return
    xbmc.log('[%s] %s' % (ADDON_ID, message), level)


def log_info(message):
    log(message, xbmc.LOGINFO)


def log_error(message):
    log(message, xbmc.LOGERROR)


def notify(message, heading=None, icon=None, time=5000):
    if heading is None:
        heading = localize(30000)
    if icon is None:
        icon = addon().getAddonInfo('icon')
    xbmcgui.Dialog().notification(heading, message, icon, time)


def textviewer(text, heading=None, monospace=True):
    try:
        xbmcgui.Dialog().textviewer(heading or localize(30000), text,
                                    usemono=monospace)
    except TypeError:  # usemono was added in Kodi 19
        xbmcgui.Dialog().textviewer(heading or localize(30000), text)


def execute_builtin(builtin, block=False):
    log('executebuiltin: %s' % builtin)
    xbmc.executebuiltin(builtin, block)


def jsonrpc(method, **params):
    """Call a JSON-RPC method and return the `result` payload.

    Returns None and logs on error, so callers can stay free of try/except.
    """
    request = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': method,
        'params': params,
    }
    try:
        raw = xbmc.executeJSONRPC(json.dumps(request))
        response = json.loads(raw)
    except (ValueError, TypeError) as exc:
        log_error('JSON-RPC %s failed to decode: %s' % (method, exc))
        return None
    if 'error' in response:
        # An error here empties every field the caller asked for, so it is
        # logged unconditionally rather than only with debug logging on.
        log_error('JSON-RPC %s returned an error: %s'
                  % (method, response['error']))
        return None
    return response.get('result')


def home_property(name, value=None):
    """Read (value=None) or write a property on the Home window."""
    window = xbmcgui.Window(HOME_WINDOW)
    if value is None:
        return window.getProperty(name)
    if value == '':
        window.clearProperty(name)
    else:
        window.setProperty(name, value)
    return value
