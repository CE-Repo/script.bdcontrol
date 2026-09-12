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

# Only names from Player.Property.Name belong here: Kodi rejects the whole
# request when one is unknown, so a single bad entry empties every field at
# once. Chapters have no Player property at all - they come from the
# Player.Chapter* info labels below.
PLAYER_PROPERTIES = [
    'speed',
    'time',
    'totaltime',
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


def is_fullscreen_video():
    """True while the fullscreen video window is the active one.

    The OSD is a fullscreen-video overlay. A Blu-ray can still be technically
    "playing" - and therefore pass is_bluray_playback() - after the user has
    left that window for the home screen, a file browser or another addon,
    with playback merely continuing in the background; opening the OSD there
    would show player controls over the wrong screen.
    """
    return bool(xbmc.getCondVisibility('Window.IsActive(fullscreenvideo)'))


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
    """Format a number of seconds always as H:MM:SS."""
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return '--:--:--'

    if seconds < 0:
        seconds = 0

    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    return '%d:%02d:%02d' % (hours, minutes, secs)



def time_dict_to_seconds(value):
    if not isinstance(value, dict):
        return 0
    return (value.get('hours', 0) * 3600
            + value.get('minutes', 0) * 60
            + value.get('seconds', 0))


def _infolabel_seconds(name):
    """Parse a Kodi H:MM:SS / MM:SS info label into seconds, or 0."""
    parts = (xbmc.getInfoLabel(name) or '').split(':')
    try:
        parts = [int(part) for part in parts]
    except ValueError:
        return 0
    seconds = 0
    for part in parts:
        seconds = seconds * 60 + part
    return seconds


def _infolabel_int(name):
    try:
        return int(xbmc.getInfoLabel(name) or 0)
    except (TypeError, ValueError):
        return 0


def chapter_marks(count):
    """Chapter start positions as percentages of the running time, or [].

    Kodi keeps chapter start times out of both the Python API and JSON-RPC.
    `Player.Chapters` is the one place it publishes them at all, built for a
    skin's Ranges control - one range per chapter, reaching from the previous
    chapter's end to this one's, so the flat list has to be read two values
    at a time. Read as a row of starts it puts each chapter at roughly half
    its real position.

    The ranges also stop one short of the chapters: `n` ranges draw `n + 1`
    boundaries, and the last of them - the end of the final range - is where
    the last chapter begins. Taking every boundary and keeping as many as
    Kodi counts chapters covers both, whether or not that final range is
    published.
    """
    raw = xbmc.getInfoLabel('Player.Chapters') or ''
    values = []
    for part in raw.replace(';', ',').split(','):
        try:
            values.append(float(part))
        except ValueError:
            continue
    if len(values) < 2:
        return []
    paired = (len(values) % 2 == 0
              and all(values[i] == values[i + 1]
                      for i in range(1, len(values) - 1, 2)))
    if paired:
        boundaries = values[0::2] + [values[-1]]
    else:
        boundaries = values
    if count > 0:
        boundaries = boundaries[:count]
    return boundaries


def _chapter_number(name):
    """Read a Player.Chapter* info label as a count, or 0.

    Kodi answers -1 rather than 0 when the player has no chapter markers, and
    an unknown info label comes back as its own name; neither may reach the
    OSD as a number, so anything that is not positive counts as "unknown".
    """
    value = _infolabel_int(name)
    return value if value > 0 else 0


class PlayerState(object):
    """A snapshot of everything the OSD needs to render itself."""

    def __init__(self):
        self.player_id = active_video_player_id()
        self.properties = get_properties(self.player_id)
        self.path = playing_file()
        self.playing = self.player_id is not None
        self.paused = self.properties.get('speed', 1) == 0
        # Player.GetProperties reports 0 for the time fields while a
        # Blu-ray or DVD menu structure is loaded - a known Kodi limitation
        # that does not affect the equivalent GUI info labels, which read the
        # same values through a different path and stay correct throughout
        # disc playback. The JSON-RPC value is used first since it needs no
        # string parsing; the info label only fills the gap it leaves on
        # discs.
        self.position = (time_dict_to_seconds(self.properties.get('time'))
                         or _infolabel_seconds('Player.Time'))
        self.duration = (time_dict_to_seconds(self.properties.get('totaltime'))
                         or _infolabel_seconds('Player.Duration'))
        self.chapter = _chapter_number('Player.Chapter')
        self.chapter_count = _chapter_number('Player.ChapterCount')
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
        """The item's name, with its release year appended when Kodi knows it.

        `VideoPlayer.Year` is only filled for an item Kodi has in its library,
        which a disc played straight from the drive is not, so the year is
        treated as a bonus rather than something to leave a gap for.
        """
        label = (xbmc.getInfoLabel('VideoPlayer.Title')
                 or disc_label(self.path)
                 or kodiutils.localize(30000))
        year = _infolabel_int('VideoPlayer.Year')
        if year > 0:
            label = '%s (%d)' % (label, year)
        return label

    def chapter_text(self):
        """The chapter line, or an empty string when there is no chapter.

        Kept out of describe() because the OSD puts it in a line of its own,
        away from the running time.
        """
        if self.chapter_count > 1:
            return kodiutils.localize(30010, self.chapter, self.chapter_count)
        if self.chapter:
            # Menu-driven disc playback often knows which chapter is running
            # without ever reporting how many there are; dropping the entry
            # over the missing total left the line looking broken.
            return kodiutils.localize(30012, self.chapter)
        return ''

    def describe(self):
        """A short status line: position and duration."""
        parts = []
        if self.duration:
            parts.append('%s / %s' % (format_time(self.position),
                                      format_time(self.duration)))
        elif self.position:
            parts.append(format_time(self.position))
        return '  ·  '.join(parts)
