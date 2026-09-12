# -*- coding: utf-8 -*-
"""The OSD's color theme.

A 1:1 port of script.tinyppi's theming: the same 50-color palettes (plus a
custom HEX color picker) resolve a settings.xml choice to an ARGB hex string,
published as a Home-window (10000) property for the skin to read via
``$INFO[Window(10000).Property(BDControl.<Name>Color)]``. Reusing TinyPPI's
palette values means both add-ons share the same default look out of the box.
"""
import json
import os
import re

import xbmc
import xbmcvfs

from . import kodiutils
from .kodiutils import localize

# Foreground/text palette; index matches the settings.xml <option> order.
_TEXT_COLORS = (
    'FFEDEDED',  # 0  White (default)
    'FFE0E0E0',  # 1  Light gray
    'FFFF8A80',  # 2  Light red
    'FFFFCC80',  # 3  Light orange
    'FFFFFF8D',  # 4  Light yellow
    'FFB9F6CA',  # 5  Light green
    'FF84FFFF',  # 6  Light cyan
    'FF82B1FF',  # 7  Light blue
    'FFE1BEE7',  # 8  Light purple
    'FFFF80AB',  # 9  Light pink
    'FFFF8A65',  # 10 Coral
    'FFFFAB91',  # 11 Salmon
    'FFFFD54F',  # 12 Amber
    'FFFFE082',  # 13 Gold
    'FFCCFF90',  # 14 Lime
    'FFA7FFEB',  # 15 Mint
    'FF80CBC4',  # 16 Teal
    'FF80D8FF',  # 17 Sky blue
    'FF40C4FF',  # 18 Azure
    'FF8C9EFF',  # 19 Indigo
    'FFB388FF',  # 20 Violet
    'FFD1C4E9',  # 21 Lavender
    'FFEA80FC',  # 22 Magenta
    'FFF48FB1',  # 23 Fuchsia
    'FFF06292',  # 24 Rose
    'FFFF5252',  # 25 Crimson
    'FFBCAAA4',  # 26 Brown
    'FFDCE775',  # 27 Olive
    'FFB0BEC5',  # 28 Slate
    'FFCFD8DC',  # 29 Silver
    'FFFFCCBC',  # 30 Peach
    'FFFFB74D',  # 31 Tangerine
    'FFE4C441',  # 32 Mustard
    'FFE6EE9C',  # 33 Chartreuse
    'FF81C784',  # 34 Forest
    'FF69F0AE',  # 35 Emerald
    'FFB2FF59',  # 36 Spring
    'FF18FFFF',  # 37 Aqua
    'FF64FFDA',  # 38 Turquoise
    'FF4FC3F7',  # 39 Cerulean
    'FF536DFE',  # 40 Cobalt
    'FFB39DDB',  # 41 Periwinkle
    'FFCE93D8',  # 42 Plum
    'FFBA68C8',  # 43 Orchid
    'FFFF4081',  # 44 Raspberry
    'FFFF5C8D',  # 45 Watermelon
    'FFFF6E40',  # 46 Scarlet
    'FFD7CCC8',  # 47 Sand
    'FFC5E1A5',  # 48 Pistachio
    'FF90A4AE',  # 49 Cadet
)

# Background palette (panel / screen dim); index matches settings.xml.
_BACKGROUND_COLORS = (
    'FA15181A',  # 0  Charcoal (default)
    'E6000000',  # 1  Black
    'FA1A0E0E',  # 2  Dark red
    'FA1A130A',  # 3  Dark orange
    'FA1A180A',  # 4  Dark yellow
    'FA0E1A0E',  # 5  Dark green
    'FA0A1A1A',  # 6  Dark cyan
    'FA0E121A',  # 7  Dark blue
    'FA140E1A',  # 8  Dark purple
    'FA242424',  # 9  Dark gray
    'FA0A1A18',  # 10 Dark teal
    'FA0A151A',  # 11 Dark sky
    'FA10121F',  # 12 Dark indigo
    'FA17101F',  # 13 Dark violet
    'FA1A0E1A',  # 14 Dark magenta
    'FA1F0E16',  # 15 Dark pink
    'FA1F0E12',  # 16 Dark rose
    'FA1A130F',  # 17 Dark brown
    'FA15170A',  # 18 Dark olive
    'FA121A0A',  # 19 Dark lime
    'FA0A1A14',  # 20 Dark mint
    'FA0A171F',  # 21 Dark azure
    'FA12171A',  # 22 Dark slate
    'FA0A0E1A',  # 23 Dark navy
    'FA1F0A0A',  # 24 Dark maroon
    'FA0D0D14',  # 25 Midnight
    'FA1A1410',  # 26 Espresso
    'FA121212',  # 27 Onyx
    'FA1C1C1E',  # 28 Graphite
    'FA1A1D20',  # 29 Steel
    'FA1F1410',  # 30 Dark peach
    'FA1F1608',  # 31 Dark tangerine
    'FA1C1808',  # 32 Dark mustard
    'FA181C0A',  # 33 Dark chartreuse
    'FA0E1A10',  # 34 Dark forest
    'FA0A1A12',  # 35 Dark emerald
    'FA101C0A',  # 36 Dark spring
    'FA0A1C1C',  # 37 Dark aqua
    'FA0A1C18',  # 38 Dark turquoise
    'FA0A161F',  # 39 Dark cerulean
    'FA0E1020',  # 40 Dark cobalt
    'FA15101F',  # 41 Dark periwinkle
    'FA1A0F1C',  # 42 Dark plum
    'FA180E1A',  # 43 Dark orchid
    'FA1F0A14',  # 44 Dark raspberry
    'FA1F0A12',  # 45 Dark watermelon
    'FA1F0E0A',  # 46 Dark scarlet
    'FA1A1714',  # 47 Dark sand
    'FA141A0E',  # 48 Dark pistachio
    'FA12171A',  # 49 Dark cadet
)

# Focused-button background: pure white by default, same hues otherwise.
_FOCUS_COLORS = ('FFFFFFFF',) + _TEXT_COLORS[1:]

# Focused-button text: black by default, then white and the same hues.
_FOCUS_TEXT_COLORS = ('FF000000', 'FFFFFFFF') + _TEXT_COLORS[1:]

# Setting option marking a color as a custom HEX value; the actual 8-digit
# ARGB hex lives in the JSON file below (Kodi rejects free-text list values).
_CUSTOM_INDEX = '999'

# Palette index each color setting falls back to when its custom HEX is
# cleared/invalid, or the setting itself is unset. Unlisted settings default
# to 0.
_DEFAULT_COLOR_INDEX = {
    'osd_dim_color': 1,   # Black
    'osd_text_color': 1,  # Light gray
}

# Opacity slider defaults (percent), mirroring the settings.xml <default>.
_DEFAULT_OPACITY = {
    'osd_panel_color_opacity': 98,  # matches TinyPPI's dialog_background_color
    'osd_dim_color_opacity': 47,
}

# Custom HEX colors (8-digit ARGB), keyed by setting id, persisted as JSON in
# the addon profile directory - mirrors script.tinyppi's custom_colors.json.
_CUSTOM_FILE = 'special://profile/addon_data/script.bdcontrol/custom_colors.json'

_HEX6_RE = re.compile(r'^[0-9A-Fa-f]{6}$')
_HEX8_RE = re.compile(r'^[0-9A-Fa-f]{8}$')

# Suffix of the per-color "HEX color" action button; its value (a swatch +
# HEX) is shown as the row's label2 so the custom color previews live.
_CUSTOM_BTN_SUFFIX = '_custom_btn'

# property name, palette, color setting id. The opacity setting id is always
# ``<color setting id>_opacity``.
_PROPERTIES = (
    ('BDControl.PanelColor', _BACKGROUND_COLORS, 'osd_panel_color'),
    ('BDControl.DimColor', _BACKGROUND_COLORS, 'osd_dim_color'),
    ('BDControl.TitleColor', _TEXT_COLORS, 'osd_title_color'),
    ('BDControl.TextColor', _TEXT_COLORS, 'osd_text_color'),
    ('BDControl.ProgressColor', _TEXT_COLORS, 'osd_progress_color'),
    ('BDControl.FocusColor', _FOCUS_COLORS, 'osd_focus_color'),
    ('BDControl.FocusTextColor', _FOCUS_TEXT_COLORS, 'osd_focus_text_color'),
)


def _custom_btn_label(raw6):
    """Return the ``label2`` markup previewing a 6-digit HEX color."""
    return '[COLOR=FF%s]●[/COLOR] #%s' % (raw6, raw6)


def _load_custom():
    """Return the stored custom colors mapping, or an empty dict."""
    path = xbmcvfs.translatePath(_CUSTOM_FILE)
    try:
        with open(path, encoding='utf-8') as handle:
            data = json.load(handle)
    except Exception:  # pylint: disable=broad-except  (no file yet, or corrupt)
        return {}
    return data if isinstance(data, dict) else {}


def _save_custom(data):
    """Persist the custom colors mapping to the profile directory."""
    path = xbmcvfs.translatePath(_CUSTOM_FILE)
    directory = os.path.dirname(path)
    if not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(data, handle)


def _pick(palette, index):
    """Return ``palette[index]``, falling back to index 0 on bad input."""
    try:
        return palette[int(index)]
    except (ValueError, TypeError, IndexError):
        return palette[0]


def _opacity_alpha(setting_id):
    """Return the 2-digit hex alpha for a 0-100% opacity slider."""
    percent = kodiutils.get_setting_int(setting_id, _DEFAULT_OPACITY.get(setting_id, 100))
    percent = max(0, min(100, percent))
    return '%02X' % int(round(percent * 255 / 100))


def _resolve(palette, setting_id, custom):
    """Resolve a color setting to an ARGB hex string (without its alpha).

    The custom marker (999) uses the stored 8-digit hex from ``custom``,
    falling back to the palette default when it is invalid or missing.
    """
    value = kodiutils.get_setting(setting_id)
    if value == _CUSTOM_INDEX:
        stored = str(custom.get(setting_id, '')).strip().upper()
        if _HEX8_RE.match(stored):
            return stored
        return _pick(palette, _DEFAULT_COLOR_INDEX.get(setting_id, 0))
    if not value:
        # Unset - a setting newer than the profile that stores it.
        value = _DEFAULT_COLOR_INDEX.get(setting_id, 0)
    return _pick(palette, value)


def apply_theme():
    """Read the appearance settings and publish them as Home-window
    properties. Call before opening the OSD so the skin can resolve every
    color as soon as the window appears."""
    custom = _load_custom()
    for prop_name, palette, color_id in _PROPERTIES:
        value = _resolve(palette, color_id, custom)
        alpha = _opacity_alpha(color_id + '_opacity')
        kodiutils.home_property(prop_name, alpha + value[2:])


def custom_color(setting_id):
    """Prompt for a custom 6-digit HEX color and store it for ``setting_id``.

    Valid input is saved to the JSON file and switches the setting to the
    custom marker (999). Invalid input notifies and falls back to the
    default. Cancelling leaves the selection untouched. Invoked via
    ``RunScript(script.bdcontrol,action=customcolor,id=<setting_id>)``.
    """
    if not setting_id:
        return

    keyboard = xbmc.Keyboard('', localize(30445))
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return

    raw = keyboard.getText().strip().lstrip('#').upper()
    addon = kodiutils.addon()
    custom = _load_custom()

    if not _HEX6_RE.match(raw):
        fallback = str(_DEFAULT_COLOR_INDEX.get(setting_id, 0))
        custom.pop(setting_id, None)
        _save_custom(custom)
        addon.setSetting(setting_id, fallback)
        addon.setSetting(setting_id + _CUSTOM_BTN_SUFFIX, '')
        kodiutils.notify(localize(30446))
    else:
        custom[setting_id] = 'FF' + raw
        _save_custom(custom)
        addon.setSetting(setting_id, _CUSTOM_INDEX)
        addon.setSetting(setting_id + _CUSTOM_BTN_SUFFIX, _custom_btn_label(raw))
        kodiutils.notify(localize(30447))
