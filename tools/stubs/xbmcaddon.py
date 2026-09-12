"""Minimal stand-in for Kodi's xbmcaddon module."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SETTINGS = {
    'show_hint': True,
    'auto_open': False,
    'osd_timeout': 10,
    'seek_step': 30,
    'keymap_enabled': True,
    'extended_disc_menus': False,
    'key_osd_code': '',
    'key_osd_longpress': False,
    'key_menu_code': '',
    'key_menu_longpress': False,
    'debug_log': True,
}

_PO = re.compile(r'msgctxt "#(\d+)"\nmsgid "((?:[^"\\]|\\.)*)"', re.MULTILINE)


def _load_strings():
    path = os.path.join(ROOT, 'resources', 'language',
                        'resource.language.en_gb', 'strings.po')
    with open(path, encoding='utf-8') as handle:
        text = handle.read()
    return {int(key): value.replace('\\"', '"')
            for key, value in _PO.findall(text)}


STRINGS = _load_strings()


# Addons other than our own that the stub pretends are installed.
FOREIGN_SETTINGS = {}


class Addon(object):
    def __init__(self, addon_id='script.bdcontrol'):
        if addon_id != 'script.bdcontrol' and addon_id not in FOREIGN_SETTINGS:
            raise RuntimeError('addon %s is not installed' % addon_id)
        self.id = addon_id

    def getAddonInfo(self, key):  # noqa: N802
        if self.id != 'script.bdcontrol':
            return FOREIGN_SETTINGS[self.id].get(key, '')
        return {
            'path': ROOT,
            'profile': os.path.join(ROOT, '.profile'),
            'version': '1.0.0',
            'icon': os.path.join(ROOT, 'resources', 'icon.png'),
            'id': self.id,
        }.get(key, '')

    def getLocalizedString(self, string_id):  # noqa: N802
        return STRINGS.get(string_id, '')

    def getSetting(self, setting_id):  # noqa: N802
        if self.id != 'script.bdcontrol':
            return FOREIGN_SETTINGS[self.id].get(setting_id, '')
        value = SETTINGS.get(setting_id, '')
        if isinstance(value, bool):
            return 'true' if value else 'false'
        return str(value)

    def getSettingBool(self, setting_id):  # noqa: N802
        if setting_id not in SETTINGS:
            raise TypeError('unknown setting %s' % setting_id)
        return bool(SETTINGS[setting_id])

    def getSettingInt(self, setting_id):  # noqa: N802
        if setting_id not in SETTINGS:
            raise TypeError('unknown setting %s' % setting_id)
        return int(SETTINGS[setting_id])

    def setSetting(self, setting_id, value):  # noqa: N802
        SETTINGS[setting_id] = value

    def setSettingBool(self, setting_id, value):  # noqa: N802
        SETTINGS[setting_id] = bool(value)

    def openSettings(self):  # noqa: N802
        pass
