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

from . import kodiutils, player
from .player import format_time
from .kodiutils import execute_builtin, jsonrpc, localize

DISC_PLAYBACK_SETTING = 'disc.playback'

# A chapter jump is made of single steps, so it needs a ceiling: without one
# a disc that stops reporting chapter changes would step for ever.
CHAPTER_STEP_LIMIT = 200

# How long a chapter step is given to register before the next one is sent.
CHAPTER_STEP_WAIT = 0.2


# --- Kodi windows ---------------------------------------------------------

def kodi_osd():
    """Open Kodi's own player OSD.

    This is the direct answer to "OK does nothing": activating the window by
    name bypasses the disc's grip on the OK button entirely.
    """
    execute_builtin('ActivateWindow(videoosd)')


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
    """Let the user pick a chapter from a list, and jump to it.

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
        return
    labels = chapter_labels(marks, state.chapter_count, state.duration)
    choice = xbmcgui.Dialog().select(localize(30116), labels,
                                     preselect=max(state.chapter - 1, 0))
    if choice < 0:
        return
    if marks:
        seek_percentage(marks[choice])
    else:
        seek_chapter(choice + 1)


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
