# -*- coding: utf-8 -*-
"""Commands BD Control can run on behalf of the user.

While a disc menu drives playback, Kodi routes navigation actions (including
OK) to the disc, which is why the regular OSD cannot be opened.  The commands
below deliberately use two different mechanisms:

* Builtins such as `PlayerControl` and `Seek` act on the player directly and
  work no matter which window has focus.
* `Action(...)` and `ActivateWindow(...)` are delivered to the *active* window,
  so anything that has to reach the disc or replace our OSD must be run after
  the BD Control dialog has closed.  Those commands are marked `closes=True`
  in the command table and the dialog closes itself before running them.
"""
import xbmcgui

from . import kodiutils, player
from .kodiutils import execute_builtin, jsonrpc, localize, log

DISC_PLAYBACK_SETTING = 'disc.playback'


# --- playback -------------------------------------------------------------

def play_pause():
    execute_builtin('PlayerControl(Play)')


def stop():
    execute_builtin('PlayerControl(Stop)')


def chapter_next():
    execute_builtin('PlayerControl(Next)')


def chapter_previous():
    execute_builtin('PlayerControl(Previous)')


def _seek_step():
    return max(kodiutils.get_setting_int('seek_step', 30), 1)


def seek(seconds):
    """Seek relative to the current position.

    Discs may forbid seeking (a "user operation prohibited" flag), in which
    case Kodi simply ignores the request; we surface that as a notification so
    the user knows the button was not swallowed by the addon.
    """
    state = player.PlayerState()
    if not state.playing:
        return
    if not state.can_seek:
        kodiutils.notify(localize(30060))
        return
    result = None
    if state.player_id is not None:
        result = jsonrpc('Player.Seek', playerid=state.player_id,
                         value={'seconds': int(seconds)})
    if result is None:
        # Older JSON-RPC versions reject the `seconds` form; the builtin takes
        # the same relative offset.
        execute_builtin('Seek(%d)' % int(seconds))


def seek_forward():
    seek(_seek_step())


def seek_backward():
    seek(-_seek_step())


# --- Kodi windows ---------------------------------------------------------

def kodi_osd():
    """Open Kodi's own player OSD.

    This is the direct answer to "OK does nothing": activating the window by
    name bypasses the disc's grip on the OK button entirely.
    """
    execute_builtin('ActivateWindow(videoosd)')


def video_settings():
    execute_builtin('ActivateWindow(osdvideosettings)')


def audio_settings():
    execute_builtin('ActivateWindow(osdaudiosettings)')


def subtitle_settings():
    execute_builtin('ActivateWindow(osdsubtitlesettings)')


def process_info():
    """The codec/HDR overlay - handy for verifying a UHD disc plays as UHD."""
    execute_builtin('ActivateWindow(playerprocessinfo)')


# --- disc ----------------------------------------------------------------

def disc_menu():
    """Ask the player to show the disc menu.

    `PlayerControl(ShowVideoMenu)` goes straight to the player rather than to
    the active window, so unlike `Action(showvideomenu)` it does not depend on
    which window has focus.  Kodi turns it into libbluray's menu call, which
    tries the in-movie popup menu first and falls back to the root menu, so a
    single button behaves like a standalone player's POPUP MENU / TOP MENU.
    """
    execute_builtin('PlayerControl(ShowVideoMenu)')


def extended_disc_menus():
    """True when the user has enabled the popup/top menu variants.

    Upstream Kodi matches the builtin parameter exactly (`paramlow ==
    "showvideomenu"`), so `ShowVideoMenu(popup)` is silently ignored there.
    Builds carrying the ShowVideoMenu(popup|top) patch - SamuriHL's CoreELEC
    build among them - accept the argument.  There is no way to probe for it,
    hence the setting.
    """
    return kodiutils.get_setting_bool('extended_disc_menus', False)


def disc_popup_menu():
    """Open the in-movie popup menu only (no fallback to the root menu)."""
    execute_builtin('PlayerControl(ShowVideoMenu(popup))')


def disc_top_menu():
    """Open the disc's top/root menu only."""
    execute_builtin('PlayerControl(ShowVideoMenu(top))')


def eject():
    execute_builtin('EjectTray()')


def _stream_label(stream, fallback_index=0):
    name = stream.get('language') or ''
    codec = stream.get('codec') or ''
    channels = stream.get('channels') or 0
    title = stream.get('name') or ''
    parts = [part for part in (name.upper(), title, codec.upper()) if part]
    if channels:
        parts.append('%d.0ch' % channels if channels < 3
                     else '%d.1ch' % (channels - 1))
    if not parts:
        parts.append('#%d' % (fallback_index + 1))
    return ' · '.join(parts)


def choose_audio():
    """Pick an audio track from a native select dialog."""
    state = player.PlayerState()
    streams = state.audio_streams
    if not state.playing or not streams:
        kodiutils.notify(localize(30061))
        return
    labels = []
    preselect = 0
    for position, stream in enumerate(streams):
        label = _stream_label(stream, position)
        if stream.get('index') == state.current_audio_index:
            preselect = position
            label = '* ' + label
        labels.append(label)
    choice = xbmcgui.Dialog().select(localize(30030), labels,
                                     preselect=preselect)
    if choice < 0:
        return
    jsonrpc('Player.SetAudioStream', playerid=state.player_id,
            stream=streams[choice].get('index', choice))


def choose_subtitle():
    """Pick a subtitle track (including "off") from a native select dialog."""
    state = player.PlayerState()
    if not state.playing:
        return
    subtitles = state.subtitles
    labels = [localize(30062)]  # Disabled
    preselect = 0 if not state.subtitles_enabled else -1
    for position, stream in enumerate(subtitles):
        label = _stream_label(stream, position)
        if (state.subtitles_enabled
                and stream.get('index') == state.current_subtitle_index):
            preselect = position + 1
            label = '* ' + label
        labels.append(label)
    if len(labels) == 1:
        kodiutils.notify(localize(30063))
        return
    choice = xbmcgui.Dialog().select(localize(30031), labels,
                                     preselect=max(preselect, 0))
    if choice < 0:
        return
    if choice == 0:
        jsonrpc('Player.SetSubtitle', playerid=state.player_id, subtitle='off')
        return
    jsonrpc('Player.SetSubtitle', playerid=state.player_id,
            subtitle=subtitles[choice - 1].get('index', choice - 1),
            enable=True)


def browse_titles():
    """List the playlists on the disc and play one without the disc menu.

    Playing a single title puts Kodi back in charge of playback, so the OSD,
    seeking and resume all behave normally again.
    """
    root = player.disc_root()
    if not root:
        kodiutils.notify(localize(30064))
        return
    log('browsing disc titles below %s' % root)
    result = jsonrpc('Files.GetDirectory', directory=root, media='video',
                     properties=['title', 'duration', 'file'])
    files = (result or {}).get('files') or []
    entries = [item for item in files if item.get('file')]
    if not entries:
        kodiutils.notify(localize(30065))
        return
    labels = []
    for item in entries:
        label = item.get('label') or item.get('title') or item.get('file')
        duration = item.get('duration') or 0
        if duration:
            label = '%s  (%s)' % (label, player.format_time(duration))
        labels.append(label)
    choice = xbmcgui.Dialog().select(localize(30032), labels)
    if choice < 0:
        return
    target = entries[choice]
    if target.get('filetype') == 'directory':
        # "Titles" is a folder on some discs - descend into it once.
        result = jsonrpc('Files.GetDirectory', directory=target['file'],
                         media='video', properties=['title', 'duration', 'file'])
        sub_entries = [item for item in (result or {}).get('files') or []
                       if item.get('file')]
        if not sub_entries:
            kodiutils.notify(localize(30065))
            return
        sub_labels = []
        for item in sub_entries:
            label = item.get('label') or item.get('file')
            duration = item.get('duration') or 0
            if duration:
                label = '%s  (%s)' % (label, player.format_time(duration))
            sub_labels.append(label)
        sub_choice = xbmcgui.Dialog().select(localize(30032), sub_labels)
        if sub_choice < 0:
            return
        target = sub_entries[sub_choice]
    jsonrpc('Player.Open', item={'file': target['file']})


def disc_playback_options():
    """Return (current_value, [(value, label), ...]) for `disc.playback`."""
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


def disc_playback_mode():
    """Let the user switch Kodi's Blu-ray playback mode.

    Choosing the non-menu mode is the permanent way out of the problem for
    people who never want the disc to take over the remote.
    """
    current, options = disc_playback_options()
    if not options:
        kodiutils.notify(localize(30066))
        return
    labels = []
    preselect = 0
    for position, (value, label) in enumerate(options):
        if value == current:
            preselect = position
            label = '* %s' % label
        labels.append(label)
    choice = xbmcgui.Dialog().select(localize(30033), labels,
                                     preselect=preselect)
    if choice < 0:
        return
    new_value = options[choice][0]
    if new_value == current:
        return
    jsonrpc('Settings.SetSettingValue', setting=DISC_PLAYBACK_SETTING,
            value=new_value)
    kodiutils.notify(localize(30067))


def open_settings():
    kodiutils.open_settings()


def send_action(action_name):
    """Forward a Kodi action to whatever window is active (i.e. the disc)."""
    execute_builtin('Action(%s)' % action_name)


def reload_keymaps():
    execute_builtin('Action(reloadkeymaps)')


def toggle_subtitles():
    execute_builtin('Action(showsubtitles)')


def next_audio_language():
    execute_builtin('Action(audionextlanguage)')
