#!/usr/bin/env python3
"""Generate the Kodi language files from a single table.

    python3 tools/make_strings.py

Keeping both languages in one place makes it obvious when a string is added
without a translation.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LANG = os.path.join(ROOT, 'resources', 'language')

# id: (english, german)
STRINGS = [
    # --- addon / menus ---------------------------------------------------
    (30000, 'BD Control', 'BD Control'),
    (30001, 'Open the BD Control OSD', 'BD-Control-OSD öffnen'),
    (30002, 'Install keymap', 'Tastenbelegung installieren'),
    (30003, 'Remove keymap', 'Tastenbelegung entfernen'),
    (30004, 'Settings', 'Einstellungen'),

    # --- status line -----------------------------------------------------
    (30010, 'Chapter %d/%d', 'Kapitel %d/%d'),
    (30011, 'Disc menu active', 'Disc-Menü aktiv'),

    # --- OSD buttons -----------------------------------------------------
    (30020, 'Disc menu', 'Disc-Menü'),
    (30021, 'Pause', 'Pause'),
    (30022, 'Stop', 'Stopp'),
    (30023, 'Prev. chapter', 'Kapitel zurück'),
    (30024, 'Next chapter', 'Kapitel vor'),
    (30025, '- %d s', '- %d s'),
    (30026, 'More...', 'Mehr ...'),
    (30027, '+ %d s', '+ %d s'),
    (30028, 'Kodi OSD', 'Kodi-OSD'),
    (30029, 'Video settings', 'Bildeinstellungen'),
    (30030, 'Audio track', 'Tonspur'),
    (30031, 'Subtitles', 'Untertitel'),
    (30032, 'Titles', 'Titel'),
    (30033, 'Blu-ray playback mode', 'Blu-ray-Wiedergabemodus'),
    (30034, 'Diagnostics', 'Diagnose'),
    (30035, 'Kodi audio settings', 'Kodi-Toneinstellungen'),
    (30036, 'Kodi subtitle settings', 'Kodi-Untertiteleinstellungen'),
    (30037, 'Turn subtitles on or off', 'Untertitel ein-/ausschalten'),
    (30038, 'Next audio language', 'Nächste Tonsprache'),
    (30039, 'Eject disc', 'Disc auswerfen'),

    # --- OSD button help lines -------------------------------------------
    (30040, "Go back to the disc's own menu",
     'Zurück zum Menü der Disc'),
    (30041, 'Pause or resume playback',
     'Wiedergabe anhalten oder fortsetzen'),
    (30042, 'Stop playback and leave the disc',
     'Wiedergabe beenden und die Disc verlassen'),
    (30043, 'Jump to the previous chapter',
     'Zum vorherigen Kapitel springen'),
    (30044, 'Jump to the next chapter', 'Zum nächsten Kapitel springen'),
    (30045, 'Rewind by the configured step',
     'Um die eingestellte Schrittweite zurückspulen'),
    (30046, 'Fast forward by the configured step',
     'Um die eingestellte Schrittweite vorspulen'),
    (30047, "Open Kodi's own player OSD, which the disc menu blocks",
     'Das Kodi-eigene OSD öffnen, das vom Disc-Menü blockiert wird'),
    (30048, 'Choose an audio track', 'Eine Tonspur auswählen'),
    (30049, 'Choose a subtitle track or turn subtitles off',
     'Untertitelspur wählen oder Untertitel ausschalten'),
    (30050, "Open Kodi's video settings for this stream",
     'Kodi-Bildeinstellungen für diesen Stream öffnen'),
    (30051, 'Codec info', 'Codec-Info'),
    (30052, 'Show decoder, resolution and HDR information',
     'Decoder, Auflösung und HDR-Informationen anzeigen'),
    (30053, 'Play a single title without the disc menu',
     'Einen einzelnen Titel ohne Disc-Menü abspielen'),
    (30054, 'More tools, disc settings and diagnostics',
     'Weitere Werkzeuge, Disc-Einstellungen und Diagnose'),

    # --- messages --------------------------------------------------------
    (30055, 'The command failed - see the Kodi log',
     'Der Befehl ist fehlgeschlagen - siehe Kodi-Log'),
    (30056, 'Play', 'Wiedergabe'),
    (30057, 'Unknown action "%s"', 'Unbekannte Aktion "%s"'),
    (30058, 'Blu-ray menu playback - open BD Control for player controls',
     'Blu-ray-Menüwiedergabe - BD Control für die Steuerung öffnen'),
    (30059, 'Blu-ray menu playback - hold OK for player controls',
     'Blu-ray-Menüwiedergabe - OK gedrückt halten für die Steuerung'),
    (30060, 'This disc does not allow seeking here',
     'Diese Disc erlaubt hier kein Spulen'),
    (30061, 'No audio tracks reported', 'Keine Tonspuren gemeldet'),
    (30062, 'Disabled', 'Aus'),
    (30063, 'This disc reports no subtitle tracks',
     'Diese Disc meldet keine Untertitelspuren'),
    (30064, 'No Blu-ray disc is playing',
     'Es wird gerade keine Blu-ray wiedergegeben'),
    (30065, 'No titles found on this disc',
     'Auf dieser Disc wurden keine Titel gefunden'),
    (30066, 'Kodi did not report a Blu-ray playback mode',
     'Kodi hat keinen Blu-ray-Wiedergabemodus gemeldet'),
    (30067, 'Playback mode changed - it applies the next time a disc starts',
     'Wiedergabemodus geändert - gilt ab der nächsten Disc'),

    # --- keymap ----------------------------------------------------------
    (30070, 'Keymap installed', 'Tastenbelegung installiert'),
    (30071, 'Keymap removed', 'Tastenbelegung entfernt'),
    (30072, 'No trigger buttons are enabled',
     'Es ist keine Auslösetaste aktiviert'),
    (30073, 'The keymap is switched off', 'Die Tastenbelegung ist deaktiviert'),
    (30074, 'long press', 'langer Druck'),

    # --- diagnostics -----------------------------------------------------
    (30080, 'yes', 'ja'),
    (30081, 'no', 'nein'),
    (30090, 'System', 'System'),
    (30091, 'Device name', 'Gerätename'),
    (30092, 'Optical drive', 'Optisches Laufwerk'),
    (30093, 'Device nodes', 'Gerätedateien'),
    (30094, 'Disc inserted', 'Disc eingelegt'),
    (30095, 'Blu-ray libraries', 'Blu-ray-Bibliotheken'),
    (30096, 'libaacs and a KEYDB.cfg are required for encrypted retail discs.',
     'Für verschlüsselte Kauf-Discs werden libaacs und eine KEYDB.cfg '
     'benötigt.'),
    (30097, 'Kodi disc settings', 'Kodi-Disc-Einstellungen'),
    (30098, 'Blu-ray playback mode', 'Blu-ray-Wiedergabemodus'),
    (30099, 'Keymap', 'Tastenbelegung'),
    (30100, 'Keymap file', 'Tastenbelegungsdatei'),
    (30101, 'Playback', 'Wiedergabe'),
    (30102, 'Nothing is playing', 'Es läuft keine Wiedergabe'),
    (30103, 'Title', 'Titel'),
    (30104, 'Path', 'Pfad'),
    (30105, 'Optical disc', 'Optische Disc'),
    (30106, 'Disc menu in control', 'Disc-Menü steuert die Wiedergabe'),
    (30107, 'Seeking allowed', 'Spulen erlaubt'),
    (30108, 'Chapter', 'Kapitel'),
    (30109, 'Audio tracks', 'Tonspuren'),
    (30110, 'Subtitle tracks', 'Untertitelspuren'),
    (30111, 'Resolution', 'Auflösung'),
    (30112, 'Diagnostics written to the Kodi log',
     'Diagnose in das Kodi-Log geschrieben'),
    (30113, 'Write diagnostics to the Kodi log',
     'Diagnose in das Kodi-Log schreiben'),

    # --- settings --------------------------------------------------------
    (30200, 'General', 'Allgemein'),
    (30201, 'Show a hint when a disc menu takes over',
     'Hinweis anzeigen, wenn ein Disc-Menü die Steuerung übernimmt'),
    (30202, 'Open BD Control automatically',
     'BD Control automatisch öffnen'),
    (30203, 'Close the OSD after (seconds, 0 = never)',
     'OSD schließen nach (Sekunden, 0 = nie)'),
    (30204, 'Seek step (seconds)', 'Spulschritt (Sekunden)'),
    (30210, 'Keymap', 'Tastenbelegung'),
    (30211, 'Install the BD Control keymap',
     'BD-Control-Tastenbelegung installieren'),
    (30212, 'Long press OK (recommended)',
     'OK lange drücken (empfohlen)'),
    (30213, 'Menu / Title button', 'Menü-/Titel-Taste'),
    (30214, 'Info button', 'Info-Taste'),
    (30215, 'Context menu button (C)', 'Kontextmenü-Taste (C)'),
    (30216, 'Long press Back', 'Zurück lange drücken'),
    (30217, 'Display button opens the Kodi OSD directly',
     'Display-Taste öffnet direkt das Kodi-OSD'),
    (30218, 'Stop button stops playback', 'Stopp-Taste beendet die Wiedergabe'),
    (30219, 'Install keymap now', 'Tastenbelegung jetzt installieren'),
    (30220, 'Remove keymap', 'Tastenbelegung entfernen'),
    (30221, 'Trigger buttons', 'Auslösetasten'),
    (30230, 'Tools', 'Werkzeuge'),
    (30231, 'Open the BD Control OSD', 'BD-Control-OSD öffnen'),
    (30240, 'Advanced', 'Erweitert'),
    (30241, 'Write debug messages to the Kodi log',
     'Debug-Meldungen in das Kodi-Log schreiben'),

    # --- settings help ---------------------------------------------------
    (30260, 'A short press still reaches the disc menu, so navigating the '
            'menu keeps working. Holding OK opens BD Control.',
     'Ein kurzer Druck erreicht weiterhin das Disc-Menü, die Navigation '
     'funktioniert also unverändert. Langes Drücken von OK öffnet '
     'BD Control.'),
    (30261, 'The keymap only changes fullscreen video playback; the rest of '
            'Kodi is untouched.',
     'Die Tastenbelegung ändert nur die Vollbildwiedergabe; der Rest von '
     'Kodi bleibt unverändert.'),
    (30262, 'Opens the OSD by itself whenever a disc menu takes over the '
            'remote.',
     'Öffnet das OSD automatisch, sobald ein Disc-Menü die Fernbedienung '
     'übernimmt.'),
]

HEADER = """# Kodi Media Center language file
# Addon Name: BD Control
# Addon id: script.bdcontrol
# Addon Provider: jamal2362
msgid ""
msgstr ""
"Project-Id-Version: script.bdcontrol\\n"
"Report-Msgid-Bugs-To: https://github.com/CE-Repo/script.bdcontrol\\n"
"POT-Creation-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: Kodi Translation Team\\n"
"Language-Team: %(team)s\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Language: %(code)s\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"
"""


def escape(text):
    return text.replace('\\', '\\\\').replace('"', '\\"')


def write_po(folder, code, team, translated):
    directory = os.path.join(LANG, folder)
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, 'strings.po')
    chunks = [HEADER % {'team': team, 'code': code}]
    for string_id, english, german in STRINGS:
        chunks.append('')
        chunks.append('msgctxt "#%d"' % string_id)
        chunks.append('msgid "%s"' % escape(english))
        chunks.append('msgstr "%s"' % (escape(german) if translated else ''))
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write('\n'.join(chunks) + '\n')
    print('wrote %s (%d strings)' % (path, len(STRINGS)))


def main():
    ids = [entry[0] for entry in STRINGS]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise SystemExit('duplicate string ids: %s' % duplicates)
    write_po('resource.language.en_gb', 'en_GB',
             'English (United Kingdom) (http://www.transifex.com/)', False)
    write_po('resource.language.de_de', 'de_DE',
             'German (Germany) (http://www.transifex.com/)', True)


if __name__ == '__main__':
    main()
