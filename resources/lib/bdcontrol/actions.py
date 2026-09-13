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
import xbmc
import xbmcgui

from . import kodiutils, maps, player
from .player import format_time
from .kodiutils import execute_builtin, jsonrpc, localize

DISC_PLAYBACK_SETTING = 'disc.playback'

# A chapter jump is made of single steps, so it needs a ceiling: without one
# a disc that stops reporting chapter changes would step for ever.
CHAPTER_STEP_LIMIT = 200

# How long a chapter step is given to register before the next one is sent.
CHAPTER_STEP_WAIT = 0.2

# A stream change is not instant: the player has to reopen the stream, so
# it is given a moment before its answer is believed.
SWITCH_CONFIRM_TRIES = 6
SWITCH_CONFIRM_WAIT = 0.25


# --- Kodi windows ---------------------------------------------------------

def kodi_osd():
    """Open Kodi's own player OSD.

    This is the direct answer to "OK does nothing": activating the window by
    name bypasses the disc's grip on the OK button entirely.
    """
    execute_builtin('ActivateWindow(videoosd)')


def _codec_name(codec, subtitle=False):
    """(format name, extension) for a codec id; either half may be empty."""
    codec = (codec or '').strip().lower()
    if not codec:
        return '', ''
    table = maps.SUBTITLE_CODEC_MAP if subtitle else maps.AUDIO_CODEC_MAP
    name = table.get(codec)
    if name is None:
        # An unmapped id still reads acceptably in capitals - "WMAPRO" rather
        # than a blank where the format should be.
        return codec.replace('_', ' ').upper(), ''
    if isinstance(name, tuple):
        return name
    return name, ''


def _language_label(language):
    """A language code as a short uppercase tag: "ger" and "de" both -> "DE".

    Discs are inconsistent about which ISO 639 form they use, so the code is
    put through Kodi's own language table to reach the two letter form. That
    table does not know every code and answers with an empty string when it
    does not, which is when the code is used as it came.
    """
    language = (language or '').strip()
    if not language:
        return ''
    try:
        short = xbmc.convertLanguage(language, xbmc.ISO_639_1)
    except Exception:  # pylint: disable=broad-except
        short = ''
    return (short or language).upper()


def stream_menu():
    """The Stream button: choose what to change, then open that chooser.

    The choosers come back with True when the user asked to step back out of
    them, which is what makes this a menu rather than a one-way door. This
    menu heads its own list with the same step back, out to the OSD it was
    opened from: every chooser under it offers one, and a menu that can only
    be left by backing out of the dialog reads as a dead end beside them.
    """
    entries = [(localize(30118), audio_menu),
               (localize(30119), subtitle_menu),
               (localize(30116), chapter_list)]
    preselect = 0
    while True:
        choice = xbmcgui.Dialog().select(
            localize(30117),
            [localize(30164)] + [label for label, _ in entries],
            preselect=preselect + 1)
        # The first entry steps back to the OSD, which is still standing
        # behind this menu; backing out of the dialog lands there too.
        if choice <= 0:
            return
        preselect = choice - 1
        if not entries[preselect][1]():
            return


def _channel_label(channels):
    """A channel count as its layout, e.g. 8 -> 7.1.

    An unlisted count keeps the bare number, which is still true even if it
    is not a layout anyone names.
    """
    try:
        channels = int(channels)
    except (TypeError, ValueError):
        return ''
    if channels < 1:
        return ''
    return maps.CHANNELS_MAP.get(channels, '%dch' % channels)


def _stream_label(stream, fallback_number, subtitle=False):
    """Name one audio or subtitle stream as compactly as it allows.

    What Kodi fills in varies with the source - a disc often gives a language
    code and nothing else, a remux a full name - so the parts are collected
    and whatever is missing simply leaves no gap. The language code is the
    one part that is always shorthand, so it is set in capitals to read as
    the tag it is rather than as a word.
    """
    parts = []
    language = _language_label(stream.get('language'))
    if language:
        parts.append(language)
    name = (stream.get('name') or '').strip()
    if name and name.upper() not in [part.upper() for part in parts]:
        parts.append(name)
    codec, extension = _codec_name(stream.get('codec'), subtitle)
    detail = ' '.join(part for part in
                      (codec, _channel_label(stream.get('channels'))) if part)
    if extension:
        # After the layout, not welded to the format name: "Dolby TrueHD 7.1
        # (Atmos)" says which bed carries the objects.
        detail = ('%s (%s)' % (detail, extension)).strip()
    if detail:
        parts.append(detail)
    return '  -  '.join(parts) or localize(30163, fallback_number)


def _selected_index(streams, index):
    """Where `index` sits in `streams`, or 0 when it is not among them."""
    for position, stream in enumerate(streams):
        if stream.get('index') == index:
            return position
    return 0


def _choose(heading, labels, preselect):
    """Show a chooser whose first entry steps back to the Stream menu.

    Returns the picked entry's position in `labels`, or None when the user
    left the chooser - by picking that first entry or by backing out of the
    dialog, which differ only in where they land afterwards.
    """
    choice = xbmcgui.Dialog().select(heading, [localize(30164)] + labels,
                                     preselect=preselect + 1)
    if choice < 0:
        return None, False
    if choice == 0:
        return None, True
    return choice - 1, True


def _confirm_switch(what, wanted, read_current):
    """Check that a stream change actually took, and say so when it did not.

    A player that will not change streams answers the request with a plain
    OK and then carries on as before - which is how this looked like nothing
    happening at all. Reading the value back turns that silence into
    something the user and the log can see.
    """
    monitor = xbmc.Monitor()
    for _ in range(SWITCH_CONFIRM_TRIES):
        if monitor.waitForAbort(SWITCH_CONFIRM_WAIT):
            return True
        if read_current() == wanted:
            return True
    kodiutils.log_error('%s stream %s was accepted but never applied'
                        % (what, wanted))
    kodiutils.notify(localize(30165))
    return False


def audio_menu():
    """Pick the audio track. True when the Stream menu should come back."""
    state = player.PlayerState()
    streams = state.audio_streams
    if not streams:
        kodiutils.notify(localize(30160))
        return True
    labels = [_stream_label(stream, number)
              for number, stream in enumerate(streams, 1)]
    choice, back = _choose(localize(30118), labels,
                           _selected_index(streams, state.current_audio_index))
    if choice is None or state.player_id is None:
        return back
    wanted = streams[choice].get('index', choice)
    jsonrpc('Player.SetAudioStream', playerid=state.player_id, stream=wanted)
    _confirm_switch('audio', wanted,
                    lambda: player.PlayerState().current_audio_index)
    return False


def subtitle_menu():
    """Pick the subtitle track or switch it off. True to return to Stream."""
    state = player.PlayerState()
    streams = state.subtitles
    if not streams:
        kodiutils.notify(localize(30161))
        return True
    # "Off" heads the tracks, so a pick is one ahead of the stream list.
    labels = [localize(30162)] + [_stream_label(stream, number, True)
                                  for number, stream in enumerate(streams, 1)]
    preselect = 0
    if state.subtitles_enabled:
        preselect = _selected_index(streams, state.current_subtitle_index) + 1
    choice, back = _choose(localize(30119), labels, preselect)
    if choice is None or state.player_id is None:
        return back
    if choice == 0:
        jsonrpc('Player.SetSubtitle', playerid=state.player_id, subtitle='off')
        return False
    # Picking a track has to turn subtitles on as well: setting the track
    # alone leaves them hidden if they were switched off.
    wanted = streams[choice - 1].get('index', choice - 1)
    jsonrpc('Player.SetSubtitle', playerid=state.player_id, subtitle=wanted,
            enable=True)
    _confirm_switch('subtitle', wanted,
                    lambda: player.PlayerState().current_subtitle_index)
    return False


def chapter_labels(marks, count, duration):
    """The list entries: numbered chapters, timestamped when the marks allow."""
    labels = []
    for number in range(1, (len(marks) or count) + 1):
        label = localize(30012, number)
        if marks:
            # Rounded, not truncated: a mark is a position on a percentage
            # scale, so cutting the fraction off would read a second early
            # about half the time.
            seconds = int(round(marks[number - 1] * duration / 100.0))
            label = '%s  -  %s' % (label, format_time(seconds))
        labels.append(label)
    return labels


def chapter_list():
    """Pick a chapter and jump to it. True to return to the Stream menu.

    Two different jumps hide behind the one list. When Kodi publishes the
    chapter marks, the entries are those marks and picking one seeks straight
    to its position - exact and immediate. Without them all we have is the
    chapter count, and the only movement left is the single step the disc
    menu cannot block, walked one chapter at a time.
    """
    state = player.PlayerState()
    marks = player.chapter_marks(state.chapter_count) if state.duration else []
    if not marks and state.chapter_count < 2:
        kodiutils.notify(localize(30158))
        return True
    labels = chapter_labels(marks, state.chapter_count, state.duration)
    choice, back = _choose(localize(30116), labels, max(state.chapter - 1, 0))
    if choice is None:
        return back
    if marks:
        seek_percentage(marks[choice])
    else:
        seek_chapter(choice + 1)
    return False


def seek_percentage(percent):
    """Seek to a position given as a percentage of the running time."""
    player_id = player.active_video_player_id()
    if player_id is None:
        return
    jsonrpc('Player.Seek', playerid=player_id, value={'percentage': percent})


def seek_chapter(target):
    """Step to chapter `target`.

    Kodi has no "go to chapter N": neither JSON-RPC nor the builtins offer
    one, and the chapter times that would allow a plain seek are not exposed
    either. What does work on a disc is the single step that survives the
    disc menu's grip on the remote - PlayerControl rather than Action, so it
    reaches the player whatever window has focus.

    So the jump is walked one chapter at a time, re-reading the chapter after
    each step instead of trusting the count: a step that does not register
    would otherwise silently shift every following one.
    """
    monitor = xbmc.Monitor()
    for _ in range(CHAPTER_STEP_LIMIT):
        current = player.PlayerState().chapter
        if current == target or current == 0:
            return
        execute_builtin('PlayerControl(%s)'
                        % ('Next' if current < target else 'Previous'))
        if monitor.waitForAbort(CHAPTER_STEP_WAIT):
            return
        if player.PlayerState().chapter == current:
            # The player is not following any more - stop rather than hammer
            # it with steps that go nowhere.
            kodiutils.log_error('chapter step from %d towards %d had no effect'
                                % (current, target))
            return
    kodiutils.log_error('gave up stepping to chapter %d' % target)


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
