# -*- coding: utf-8 -*-
"""Inspection of the running Kodi player, focused on optical disc playback."""
try:
    from urllib.parse import unquote
except ImportError:  # pragma: no cover - Kodi 19+ is always Python 3
    from urllib import unquote  # type: ignore

import xbmc

from . import kodiutils
from .kodiutils import jsonrpc

# Path prefixes Kodi uses for optical media and disc images.
DISC_PREFIXES = ('bluray://', 'dvd://', 'udf://', 'iso9660://')

PLAYER_PROPERTIES = [
    'speed',
    'time',
    'totaltime',
    'percentage',
    'chapter',
    'chaptercount',
    'currentaudiostream',
    'audiostreams',
    'currentsubtitle',
    'subtitles',
    'subtitleenabled',
    'canseek',
    'type',
]


def active_video_player_id():
    """Return the id of the active video player, or None."""
    players = jsonrpc('Player.GetActivePlayers') or []
    for player in players:
        if player.get('type') == 'video':
            return player.get('playerid')
    return None


def get_properties(player_id=None):
    """Return the player properties dict, or an empty dict when idle."""
    if player_id is None:
        player_id = active_video_player_id()
    if player_id is None:
        return {}
    result = jsonrpc('Player.GetProperties', playerid=player_id,
                     properties=PLAYER_PROPERTIES)
    return result or {}


def playing_file():
    """Return the path of the item being played, or an empty string."""
    try:
        player = xbmc.Player()
        if player.isPlaying():
            return player.getPlayingFile() or ''
    except RuntimeError:
        pass
    return ''


def is_playing_video():
    return bool(xbmc.getCondVisibility('Player.HasVideo'))


def is_disc_playback(path=None):
    """True when the current item comes from an optical disc or disc image."""
    if path is None:
        path = playing_file()
    if not path:
        return False
    lowered = path.lower()
    if lowered.startswith(DISC_PREFIXES):
        return True
    # Kodi also plays the raw structure when a disc is mounted as a folder.
    return '/bdmv/' in lowered or '/video_ts/' in lowered


# A DVD is a disc with menus too, but not what this addon is for, so it has to
# be told apart from a Blu-ray before falling back on the menu check below.
DVD_MARKERS = ('dvd://', '/video_ts/', 'video_ts.ifo')


def _is_dvd(lowered):
    return (lowered.startswith('dvd://')
            or any(marker in lowered for marker in DVD_MARKERS[1:]))


def is_bluray_playback(path=None):
    """True when a Blu-ray is playing, as opposed to any other kind of video.

    The path is checked first, but it is not enough on its own: what Kodi
    reports as the playing file for a disc it drives through libbluray varies
    with how playback was started - `bluray://`, a path inside BDMV, a mounted
    folder, a disc image or a raw device node, depending on the source and on
    Kodi's Blu-ray playback mode.

    So when the path does not settle it, Kodi's own report of a disc menu
    driving the input does. A DVD is excluded explicitly, since it sets the
    same flag. Passing `path` only short-circuits the path half; the menu
    check always refers to what is playing now.
    """
    if path is None:
        path = playing_file()
    if not path:
        return False
    lowered = path.lower()
    if lowered.startswith('bluray://') or '/bdmv/' in lowered:
        return True
    if _is_dvd(lowered):
        return False
    return has_disc_menu()


def describe_playback():
    """One line naming the playing file and how it was classified.

    The mapping is written by the service without anything on screen to show
    for it, so this is what the log and the diagnostics page report to make a
    misdetection visible instead of silent.
    """
    path = playing_file()
    if not path:
        return 'nothing playing'
    return ('path=%s bluray=%s hasmenu=%s inmenu=%s'
            % (path, is_bluray_playback(path), has_disc_menu(),
               is_menu_active()))


def has_disc_menu():
    """True when the disc's own menu system is driving playback.

    `VideoPlayer.HasMenu` is set by Kodi while a DVD/Blu-ray menu (HDMV or
    BD-J) is in control of the input, which is exactly the situation where
    the OK button no longer reaches Kodi's OSD.
    """
    return bool(xbmc.getCondVisibility('VideoPlayer.HasMenu'))


def is_menu_active():
    """True while the disc menu itself is on screen (not the feature)."""
    return bool(xbmc.getCondVisibility('VideoPlayer.IsInMenu'))


def disc_root(path=None):
    """Derive the `bluray://` root of the disc from a playing path.

    Kodi plays single titles as
    `bluray://<encoded source>/BDMV/PLAYLIST/00800.mpls`; cutting the path at
    `/BDMV` yields the root that `Files.GetDirectory` can list.  Returns an
    empty string when the path does not belong to a Blu-ray.
    """
    if path is None:
        path = playing_file()
    if not path:
        return ''
    lowered = path.lower()
    index = lowered.find('/bdmv')
    if index != -1:
        root = path[:index + 1]
    elif lowered.startswith('bluray://'):
        root = path
    else:
        return ''
    if not root.endswith('/'):
        root += '/'
    if not root.lower().startswith('bluray://'):
        # A mounted disc folder: wrap it so Kodi's Blu-ray directory handles it.
        try:
            from urllib.parse import quote
        except ImportError:  # pragma: no cover
            from urllib import quote  # type: ignore
        root = 'bluray://' + quote(root, safe='')
    return root


def disc_label(path=None):
    """A human readable name for the disc behind `path`."""
    if path is None:
        path = playing_file()
    label = xbmc.getInfoLabel('VideoPlayer.Title') or ''
    if label:
        return label
    root = disc_root(path)
    if root:
        cleaned = unquote(root[len('bluray://'):]).rstrip('/')
        return cleaned.rsplit('/', 1)[-1] or cleaned
    return ''


def format_time(seconds):
    """Format a number of seconds as H:MM:SS (or M:SS below an hour)."""
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return '--:--'
    if seconds < 0:
        seconds = 0
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return '%d:%02d:%02d' % (hours, minutes, secs)
    return '%d:%02d' % (minutes, secs)


def time_dict_to_seconds(value):
    if not isinstance(value, dict):
        return 0
    return (value.get('hours', 0) * 3600
            + value.get('minutes', 0) * 60
            + value.get('seconds', 0))


class PlayerState(object):
    """A snapshot of everything the OSD needs to render itself."""

    def __init__(self):
        self.player_id = active_video_player_id()
        self.properties = get_properties(self.player_id)
        self.path = playing_file()
        self.playing = self.player_id is not None
        self.paused = self.properties.get('speed', 1) == 0
        self.position = time_dict_to_seconds(self.properties.get('time'))
        self.duration = time_dict_to_seconds(self.properties.get('totaltime'))
        self.percentage = self.properties.get('percentage', 0) or 0
        self.chapter = self.properties.get('chapter', 0) or 0
        self.chapter_count = self.properties.get('chaptercount', 0) or 0
        self.can_seek = bool(self.properties.get('canseek', False))
        self.has_menu = has_disc_menu()
        self.in_menu = is_menu_active()
        self.is_disc = is_disc_playback(self.path)

    @property
    def audio_streams(self):
        return self.properties.get('audiostreams') or []

    @property
    def subtitles(self):
        return self.properties.get('subtitles') or []

    @property
    def current_audio_index(self):
        return (self.properties.get('currentaudiostream') or {}).get('index', -1)

    @property
    def current_subtitle_index(self):
        return (self.properties.get('currentsubtitle') or {}).get('index', -1)

    @property
    def subtitles_enabled(self):
        return bool(self.properties.get('subtitleenabled', False))

    def title(self):
        label = xbmc.getInfoLabel('VideoPlayer.Title')
        if label:
            return label
        return disc_label(self.path) or kodiutils.localize(30000)

    def describe(self):
        """A short status line: position, duration and chapter."""
        parts = []
        if self.duration:
            parts.append('%s / %s' % (format_time(self.position),
                                      format_time(self.duration)))
        elif self.position:
            parts.append(format_time(self.position))
        if self.chapter_count:
            parts.append(kodiutils.localize(30010, self.chapter,
                                            self.chapter_count))
        if self.has_menu:
            parts.append(kodiutils.localize(30011))
        return '  ·  '.join(parts)
