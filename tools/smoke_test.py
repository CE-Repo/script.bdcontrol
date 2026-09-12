#!/usr/bin/env python3
"""Exercise the addon logic against stubbed Kodi modules.

    python3 tools/smoke_test.py

This is not a substitute for testing on a real box, but it catches import
errors, typos and broken string formatting before the addon ever reaches
Kodi.
"""
import os
import shutil
import sys
import xml.dom.minidom

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

sys.path.insert(0, os.path.join(HERE, 'stubs'))
sys.path.insert(0, os.path.join(ROOT, 'resources', 'lib'))

import xbmc  # noqa: E402
import xbmcaddon  # noqa: E402
import xbmcgui  # noqa: E402

from bdcontrol import (actions, dialog, keymap, kodiutils, main, player,  # noqa: E402
                       service, tools)

FAILURES = []


def check(condition, description):
    if condition:
        print('  ok   %s' % description)
    else:
        print('  FAIL %s' % description)
        FAILURES.append(description)


def section(title):
    print('\n== %s ==' % title)


def test_localisation():
    section('localisation')
    check(kodiutils.localize(30000) == 'BD Control', 'addon name resolves')
    check(kodiutils.localize(30010, 3, 24) == 'Chapter 3/24',
          'chapter status formats two numbers')
    check(kodiutils.localize(30025, 30) == '- 30 s',
          'seek-back label formats the step')
    check(kodiutils.localize(30057, 'nope') == 'Unknown action "nope"',
          'unknown action message formats')
    # Every button label and hint must resolve to real text.
    commands = dialog._build_commands()  # noqa: SLF001
    empty = [cid for cid, cmd in commands.items()
             if not cmd.label or not cmd.hint]
    check(not empty, 'every OSD button has a label and a hint (%d buttons)'
          % len(commands))


def test_arguments():
    section('argument parsing')
    check(main.parse_args(['action=toggle']) == {'action': 'toggle'},
          'key=value form')
    check(main.parse_args(['toggle']) == {'action': 'toggle'},
          'bare form')
    check(main.parse_args(['action=seek', 'seconds=60'])
          == {'action': 'seek', 'seconds': '60'}, 'extra parameters')
    check(main.parse_args([]) == {}, 'no arguments')
    unknown = set(main.HANDLERS) - {'seek'}
    check(all(callable(handler) for handler in main.HANDLERS.values()),
          'every handler is callable (%d actions)' % len(unknown))


def test_keymap():
    section('keymap generation')
    content = keymap.build()
    check(content.startswith('<?xml'), 'keymap starts with an XML declaration')
    xml.dom.minidom.parseString(content)
    check(True, 'keymap is well-formed XML')
    check('mod="longpress"' in content, 'long press modifier is written')
    check('RunScript(script.bdcontrol,action=toggle)' in content,
          'the toggle command is wired up')
    check('<FullscreenVideo>' in content,
          'only the fullscreen video window is touched')
    check(content.count('<keyboard>') == 1 and content.count('<remote>') == 1,
          'one keyboard and one remote block')

    check('<title>PlayerControl(ShowVideoMenu)</title>' in content,
          'the Title button is bound to the disc menu')

    # The popup variant is opt-in, because upstream Kodi matches the builtin
    # parameter exactly and would silently ignore the argument.
    xbmcaddon.SETTINGS['extended_disc_menus'] = True
    check('<title>PlayerControl(ShowVideoMenu(popup))</title>' in keymap.build(),
          'enabling the extended menus switches the Title button to popup')
    xbmcaddon.SETTINGS['extended_disc_menus'] = False
    check('<title>PlayerControl(ShowVideoMenu)</title>' in keymap.build(),
          'and switching it back restores the portable builtin')

    # Turning every trigger off must produce an empty keymap, not a broken one.
    saved = dict(xbmcaddon.SETTINGS)
    for setting in ('km_longpress_ok', 'km_menu', 'km_disc_menu'):
        xbmcaddon.SETTINGS[setting] = False
    check(keymap.build() == '', 'no triggers means no keymap file')
    xbmcaddon.SETTINGS.clear()
    xbmcaddon.SETTINGS.update(saved)

    # A full round trip through the profile directory.
    profile_keymaps = keymap.keymap_dir()
    if os.path.isdir(os.path.dirname(profile_keymaps)):
        shutil.rmtree(os.path.dirname(profile_keymaps), ignore_errors=True)
    changed = keymap.sync()
    check(changed and keymap.is_installed(), 'sync writes the keymap file')
    check(keymap.sync() is False, 'a second sync is a no-op')
    xbmcaddon.SETTINGS['keymap_enabled'] = False
    check(keymap.sync() is True and not keymap.is_installed(),
          'disabling the keymap removes the file')
    xbmcaddon.SETTINGS['keymap_enabled'] = True
    keymap.sync()
    check('Action(reloadkeymaps)' in xbmc.BUILTINS,
          'Kodi is asked to reload its keymaps')
    shutil.rmtree(os.path.dirname(keymap.keymap_dir()), ignore_errors=True)


def test_player_helpers():
    section('player helpers')
    check(player.format_time(0) == '0:00', 'zero formats as 0:00')
    check(player.format_time(65) == '1:05', 'minutes and seconds')
    check(player.format_time(3725) == '1:02:05', 'hours, minutes and seconds')
    check(player.format_time(None) == '--:--', 'no time yet')
    check(player.time_dict_to_seconds(
        {'hours': 1, 'minutes': 2, 'seconds': 3}) == 3723, 'time dict')

    root = player.disc_root(
        'bluray://udf%3a%2f%2f%2fdev%2fsr0%2f/BDMV/PLAYLIST/00800.mpls')
    check(root == 'bluray://udf%3a%2f%2f%2fdev%2fsr0%2f/',
          'the disc root is derived from a playlist path (%s)' % root)
    check(player.disc_root('bluray://udf%3a%2f%2f%2fdev%2fsr0%2f/')
          == 'bluray://udf%3a%2f%2f%2fdev%2fsr0%2f/', 'an existing root is kept')
    mounted = player.disc_root('/media/BD_DISC/BDMV/index.bdmv')
    check(mounted.startswith('bluray://'),
          'a mounted disc folder is wrapped (%s)' % mounted)
    check(player.disc_root('/storage/videos/film.mkv') == '',
          'a plain file has no disc root')
    check(player.is_disc_playback('bluray://x/BDMV/y.mpls'),
          'bluray:// paths count as disc playback')
    check(player.is_disc_playback('/media/disc/BDMV/index.bdmv'),
          'mounted BDMV folders count as disc playback')
    check(not player.is_disc_playback('/storage/videos/film.mkv'),
          'regular files do not')


def test_player_state():
    section('player state')
    xbmc.JSONRPC_RESPONSES['Player.GetActivePlayers'] = [
        {'playerid': 1, 'type': 'video'}]
    xbmc.JSONRPC_RESPONSES['Player.GetProperties'] = {
        'speed': 1,
        'time': {'hours': 0, 'minutes': 12, 'seconds': 30},
        'totaltime': {'hours': 2, 'minutes': 0, 'seconds': 0},
        'percentage': 10.4,
        'chapter': 3,
        'chaptercount': 24,
        'canseek': True,
        'currentaudiostream': {'index': 0, 'language': 'eng',
                               'codec': 'truehd', 'channels': 8},
        'audiostreams': [
            {'index': 0, 'language': 'eng', 'codec': 'truehd', 'channels': 8},
            {'index': 1, 'language': 'deu', 'codec': 'dtshd', 'channels': 6},
        ],
        'currentsubtitle': {'index': 0, 'language': 'eng'},
        'subtitles': [{'index': 0, 'language': 'eng', 'name': 'Full'}],
        'subtitleenabled': False,
    }
    state = player.PlayerState()
    check(state.playing, 'a video player is detected')
    check(state.position == 750 and state.duration == 7200,
          'position and duration are converted to seconds')
    check(state.chapter == 3 and state.chapter_count == 24, 'chapter counters')
    check(state.has_menu, 'the disc menu flag is read from Kodi')
    check(state.is_disc, 'the path is recognised as a disc')
    described = state.describe()
    check('12:30' in described and 'Chapter 3/24' in described
          and 'Disc menu active' in described,
          'the status line reads: %s' % described)
    check(len(state.audio_streams) == 2, 'audio streams are exposed')
    check(actions._stream_label(state.audio_streams[1], 1)  # noqa: SLF001
          == 'DEU · DTSHD · 5.1ch',
          'stream labels are readable: %s'
          % actions._stream_label(state.audio_streams[1], 1))  # noqa: SLF001


def test_actions():
    section('actions')
    xbmc.BUILTINS.clear()
    actions.play_pause()
    actions.stop()
    actions.chapter_next()
    actions.chapter_previous()
    actions.disc_menu()
    actions.kodi_osd()
    actions.eject()
    actions.process_info()
    expected = ['PlayerControl(Play)', 'PlayerControl(Stop)',
                'PlayerControl(Next)', 'PlayerControl(Previous)',
                'PlayerControl(ShowVideoMenu)', 'ActivateWindow(videoosd)',
                'EjectTray()', 'ActivateWindow(playerprocessinfo)']
    check(xbmc.BUILTINS == expected,
          'the player builtins are the expected ones')

    # PlayerControl goes to the player itself, so the disc menu does not
    # depend on which window has focus; Action(...) would.
    check(not any(builtin.startswith('Action(show') for builtin in expected),
          'the disc menu does not rely on window routing')

    xbmc.BUILTINS.clear()
    actions.disc_popup_menu()
    actions.disc_top_menu()
    check(xbmc.BUILTINS == ['PlayerControl(ShowVideoMenu(popup))',
                            'PlayerControl(ShowVideoMenu(top))'],
          'the popup and top menu variants pass their argument')

    xbmc.BUILTINS.clear()
    xbmc.JSONRPC_RESPONSES['Player.Seek'] = {'percentage': 11.0}
    actions.seek_forward()
    check(not xbmc.BUILTINS,
          'seeking prefers JSON-RPC over the Seek builtin')

    # When JSON-RPC refuses the request the builtin has to take over.
    del xbmc.JSONRPC_RESPONSES['Player.Seek']
    xbmc.BUILTINS.clear()
    actions.seek_backward()
    check(xbmc.BUILTINS == ['Seek(-30)'],
          'seeking falls back to the builtin (%s)' % xbmc.BUILTINS)

    # A disc that forbids seeking must produce a message, not a silent no-op.
    xbmc.JSONRPC_RESPONSES['Player.GetProperties'] = dict(
        xbmc.JSONRPC_RESPONSES['Player.GetProperties'], canseek=False)
    xbmcgui.NOTIFICATIONS.clear()
    xbmc.BUILTINS.clear()
    actions.seek_forward()
    check(not xbmc.BUILTINS and len(xbmcgui.NOTIFICATIONS) == 1,
          'a locked disc explains why nothing happened')
    xbmc.JSONRPC_RESPONSES['Player.GetProperties'] = dict(
        xbmc.JSONRPC_RESPONSES['Player.GetProperties'], canseek=True)


def test_titles_browser():
    section('title browser')
    xbmc.JSONRPC_RESPONSES['Files.GetDirectory'] = {
        'files': [
            {'label': 'Main title', 'file': 'bluray://x/BDMV/PLAYLIST/00800.mpls',
             'duration': 7200, 'filetype': 'file'},
            {'label': 'Titles', 'file': 'bluray://x/titles/',
             'filetype': 'directory'},
        ]
    }
    opened = {}
    xbmc.JSONRPC_RESPONSES['Player.Open'] = lambda params: opened.update(params)
    xbmcgui.SELECT_RESULT = 0
    actions.browse_titles()
    check(opened.get('item', {}).get('file')
          == 'bluray://x/BDMV/PLAYLIST/00800.mpls',
          'picking a title starts it without the disc menu')

    xbmcgui.SELECT_RESULT = -1
    opened.clear()
    actions.browse_titles()
    check(not opened, 'cancelling the list plays nothing')


def test_diagnostics():
    section('diagnostics')
    xbmc.JSONRPC_RESPONSES['Settings.GetSettingValue'] = {'value': 1}
    xbmc.JSONRPC_RESPONSES['Settings.GetSettings'] = {
        'settings': [{'id': 'disc.playback',
                      'options': [{'label': 'Simple menu', 'value': 0},
                                  {'label': 'Disc menu', 'value': 1},
                                  {'label': 'Main title', 'value': 2}]}]
    }
    text = tools.diagnostics_text()
    check('Kodi:' in text, 'the Kodi version is reported')
    check('libbluray' in text, 'the Blu-ray libraries are reported')
    check('Disc menu (1)' in text,
          'the active Blu-ray playback mode is resolved to its label')
    check('Disc menu in control: yes' in text,
          'the live disc-menu state is reported')
    check('3840x2160' in text, 'the playing resolution is reported')
    missing = [line for line in text.splitlines() if line.strip().endswith(': ')]
    check(not missing, 'no diagnostic line is left blank: %s' % missing)


def test_more_menu():
    section('more menu')
    xbmcgui.SELECT_RESULT = -1
    xbmcaddon.SETTINGS['extended_disc_menus'] = False
    plain = []
    original_select = xbmcgui.Dialog.select

    def capture(self, heading, options, preselect=-1):
        plain.extend(options)
        return -1

    xbmcgui.Dialog.select = capture
    try:
        tools.more_menu()
        check('Disc popup menu' not in plain,
              'the popup entries are hidden on a stock build')
        xbmcaddon.SETTINGS['extended_disc_menus'] = True
        plain.clear()
        tools.more_menu()
        check('Disc popup menu' in plain and 'Disc top menu' in plain,
              'they appear once the extended menus are enabled')
    finally:
        xbmcgui.Dialog.select = original_select
        xbmcaddon.SETTINGS['extended_disc_menus'] = False


def test_service():
    section('service')
    instance = service.Service()
    instance.on_playback_started()
    check(instance._pending_path == xbmc.PLAYING_FILE,  # noqa: SLF001
          'disc playback is queued for the menu check')
    xbmcgui.NOTIFICATIONS.clear()
    instance._process_pending()  # noqa: SLF001
    check(len(xbmcgui.NOTIFICATIONS) == 1,
          'the user is told how to open BD Control')
    check('hold OK' in xbmcgui.NOTIFICATIONS[0][1],
          'the hint names the configured trigger: %s'
          % xbmcgui.NOTIFICATIONS[0][1])
    check(instance._pending_path == '',  # noqa: SLF001
          'the pending check is cleared afterwards')

    # A regular file must not trigger anything.
    saved = xbmc.PLAYING_FILE
    xbmc.PLAYING_FILE = '/storage/videos/film.mkv'
    instance = service.Service()
    instance.on_playback_started()
    check(instance._pending_path == '',  # noqa: SLF001
          'a normal video file is ignored')
    xbmc.PLAYING_FILE = saved


def test_skin_ids_match():
    section('skin / code consistency')
    path = os.path.join(ROOT, 'resources', 'skins', 'default', '1080i',
                        'script-bdcontrol-osd.xml')
    document = xml.dom.minidom.parse(path)
    ids = set()
    for element in document.getElementsByTagName('control'):
        value = element.getAttribute('id')
        if value:
            ids.add(int(value))
    commands = dialog._build_commands()  # noqa: SLF001
    missing = sorted(set(commands) - ids)
    check(not missing, 'every command has a button in the skin file: %s'
          % missing)
    for control_id in (dialog.LABEL_TITLE, dialog.LABEL_STATUS,
                       dialog.PROGRESS, dialog.LABEL_HINT):
        check(control_id in ids, 'control %d exists in the skin file'
              % control_id)
    textures = set()
    for element in document.getElementsByTagName('*'):
        if element.firstChild and element.firstChild.nodeType == 3:
            value = element.firstChild.nodeValue.strip()
            if value.endswith('.png'):
                textures.add(value)
    media = os.path.join(ROOT, 'resources', 'skins', 'default', 'media')
    absent = sorted(name for name in textures
                    if not os.path.exists(os.path.join(media, name)))
    check(not absent, 'every texture referenced by the skin exists: %s'
          % absent)


def test_dialog():
    section('OSD dialog')
    instance = dialog.BDControlDialog('script-bdcontrol-osd.xml', ROOT,
                                      'default', '1080i')
    instance.onInit()
    instance.wait_for_worker()
    title = instance.getControl(dialog.LABEL_TITLE).label
    check(title == 'Concert Disc', 'the title label is filled in (%s)' % title)
    status = instance.getControl(dialog.LABEL_STATUS).label
    check('Chapter 3/24' in status, 'the status label is filled in')
    check(instance.getControl(dialog.PROGRESS).percent > 0,
          'the progress bar follows the player')
    play_label = instance.getControl(dialog.BUTTON_PLAY_PAUSE).label
    check(play_label == 'Pause', 'a playing disc offers Pause (%s)' % play_label)
    seek_label = instance.getControl(dialog.BUTTON_SEEK_FORWARD).label
    check(seek_label == '+ 30 s',
          'the seek button shows the step (%s)' % seek_label)

    instance.onFocus(dialog.BUTTON_KODI_OSD)
    hint = instance.getControl(dialog.LABEL_HINT).label
    check(hint.startswith('Open Kodi'), 'focusing a button explains it (%s)'
          % hint)

    xbmc.BUILTINS.clear()
    instance.onClick(dialog.BUTTON_KODI_OSD)
    check(xbmc.BUILTINS == ['ActivateWindow(videoosd)'],
          'clicking "Kodi OSD" opens the native OSD')

    # A paused player must offer Play instead of Pause.
    instance = dialog.BDControlDialog('script-bdcontrol-osd.xml', ROOT,
                                      'default', '1080i')
    xbmc.JSONRPC_RESPONSES['Player.GetProperties'] = dict(
        xbmc.JSONRPC_RESPONSES['Player.GetProperties'], speed=0)
    instance.onInit()
    instance.wait_for_worker()
    check(instance.getControl(dialog.BUTTON_PLAY_PAUSE).label == 'Play',
          'a paused disc offers Play')
    xbmc.JSONRPC_RESPONSES['Player.GetProperties'] = dict(
        xbmc.JSONRPC_RESPONSES['Player.GetProperties'], speed=1)

    # The fallback list must cover the same commands.
    xbmcgui.SELECT_RESULT = 0
    xbmc.BUILTINS.clear()
    dialog.fallback()
    check(xbmc.BUILTINS == ['ActivateWindow(videoosd)'],
          'the fallback list runs the first command')
    xbmcgui.SELECT_RESULT = -1
    commands = dialog._build_commands()  # noqa: SLF001
    check(set(dialog.FALLBACK_ORDER) == set(commands),
          'the fallback list offers every command')

    # Opening the OSD with nothing playing must explain itself rather than
    # flashing a window that closes on its first refresh.
    xbmc.COND_VISIBILITY['Player.HasVideo'] = False
    xbmcgui.NOTIFICATIONS.clear()
    dialog.show()
    check(len(xbmcgui.NOTIFICATIONS) == 1
          and xbmcgui.NOTIFICATIONS[0][1] == 'Nothing is playing',
          'opening the OSD while idle says so')
    xbmc.COND_VISIBILITY['Player.HasVideo'] = True


def main_test():
    test_localisation()
    test_arguments()
    test_keymap()
    test_player_helpers()
    test_player_state()
    test_actions()
    test_titles_browser()
    test_diagnostics()
    test_more_menu()
    test_service()
    test_skin_ids_match()
    test_dialog()

    print('')
    if FAILURES:
        print('%d check(s) failed' % len(FAILURES))
        return 1
    print('all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main_test())
