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
    (30058, 'Blu-ray menu playback - assign a button in the BD Control '
            'settings',
     'Blu-ray-Menüwiedergabe - Taste in den BD-Control-Einstellungen '
     'zuweisen'),
    (30059, 'Blu-ray menu playback - hold your BD Control button for player '
            'controls',
     'Blu-ray-Menüwiedergabe - BD-Control-Taste gedrückt halten für die '
     'Steuerung'),
    (30152, 'Blu-ray menu playback - press your BD Control button for player '
            'controls',
     'Blu-ray-Menüwiedergabe - BD-Control-Taste drücken für die Steuerung'),
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
    (30073, 'The keymap is switched off', 'Die Tastenbelegung ist deaktiviert'),

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
    (30114, 'Disc popup menu', 'Popup-Menü der Disc'),
    (30115, 'Disc top menu', 'Hauptmenü der Disc'),
    (30116, 'Assign a button', 'Taste zuweisen'),
    (30117, 'Press the button you want to use for BD Control',
     'Drücke die Taste, die BD Control öffnen soll'),
    (30118, 'Press it now on your remote. Back cancels.',
     'Jetzt auf der Fernbedienung drücken. Zurück bricht ab.'),
    (30119, 'Button id %d', 'Tasten-ID %d'),
    (30120, 'No button was detected',
     'Es wurde keine Taste erkannt'),
    (30121, 'Recent key presses from the Kodi log',
     'Zuletzt gedrückte Tasten laut Kodi-Log'),
    (30122, 'No key presses found in the log. Turn on debug logging under '
            'Settings > System > Logging, press the button during playback, '
            'then look again.',
     'Im Log wurden keine Tastendrücke gefunden. Debug-Logging unter '
     'Einstellungen > System > Protokollierung einschalten, die Taste '
     'während der Wiedergabe drücken und erneut nachsehen.'),
    (30125, 'Debug logging', 'Debug-Logging'),
    (30126, 'Keymap file contents', 'Inhalt der Tastenbelegungsdatei'),
    (30127, 'Note: long press only fires when the remote driver reports a '
            'held key. If it does not work, assign the button again and '
            'choose a short press.',
     'Hinweis: Langes Drücken funktioniert nur, wenn der '
     'Fernbedienungstreiber eine gehaltene Taste meldet. Falls es nicht '
     'klappt, die Taste erneut zuweisen und kurzes Drücken wählen.'),
    (30128, 'Remote configuration', 'Fernbedienungs-Konfiguration'),
    (30129, 'no repeat settings found', 'keine Repeat-Einstellungen gefunden'),
    (30130, 'none found', 'keine gefunden'),
    (30131, 'The BD Control keymap was disabled by another addon and has been '
            'restored',
     'Die BD-Control-Tastenbelegung wurde von einem anderen Addon deaktiviert '
     'und wiederhergestellt'),
    (30132, 'Keymap Editor', 'Keymap Editor'),
    (30133, 'not installed', 'nicht installiert'),
    (30134, 'Allow multiple keymap files',
     'Mehrere Tastenbelegungsdateien zulassen'),
    (30135, 'Disabled copies of the BD Control keymap',
     'Deaktivierte Kopien der BD-Control-Tastenbelegung'),
    (30140, 'Open BD Control', 'BD Control öffnen'),
    (30141, 'Open the disc menu', 'Disc-Menü öffnen'),
    (30142, 'Should it only trigger on a long press?',
     'Soll sie erst bei langem Drücken auslösen?'),
    (30143, 'Long press', 'Langes Drücken'),
    (30144, 'Short press', 'Kurzes Drücken'),
    (30146, 'not assigned', 'nicht zugewiesen'),
    (30149, 'No button was detected. Pick one from the Kodi log instead?',
     'Es wurde keine Taste erkannt. Stattdessen eine aus dem Kodi-Log '
     'wählen?'),
    (30150, 'That button is already assigned to "%s"',
     'Diese Taste ist bereits "%s" zugewiesen'),
    (30151, 'Long press only works when the remote driver reports a held '
            'key, which not every remote does. If the button does nothing, '
            'assign it again and choose a short press.',
     'Langes Drücken funktioniert nur, wenn der Fernbedienungstreiber eine '
     'gehaltene Taste meldet - das tut nicht jede Fernbedienung. Passiert '
     'nichts, die Taste erneut zuweisen und kurzes Drücken wählen.'),
    (30136, 'With this off, saving in Keymap Editor renames every other '
            'keymap file to *.xml.bak.N - including this addon\'s. Turn it on '
            'in the Keymap Editor settings, or switch the BD Control keymap '
            'off and do the mapping in Keymap Editor instead.',
     'Ist dies aus, benennt das Speichern im Keymap Editor alle anderen '
     'Tastenbelegungsdateien in *.xml.bak.N um - auch die dieses Addons. '
     'Entweder in den Keymap-Editor-Einstellungen einschalten oder die '
     'BD-Control-Tastenbelegung ausschalten und die Zuordnung im Keymap '
     'Editor vornehmen.'),

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
    (30221, 'Assigned buttons', 'Zugewiesene Tasten'),
    (30227, 'Assign the button for BD Control',
     'Taste für BD Control zuweisen'),
    (30228, 'Assign the button for the disc menu',
     'Taste für das Disc-Menü zuweisen'),
    (30229, 'Clear all assignments', 'Alle Zuweisungen löschen'),
    (30223, 'Separate popup and top menu entries',
     'Getrennte Einträge für Popup- und Hauptmenü'),
    (30226, 'Show recent key presses from the log',
     'Zuletzt gedrückte Tasten aus dem Log anzeigen'),
    (30230, 'Tools', 'Werkzeuge'),
    (30231, 'Open the BD Control OSD', 'BD-Control-OSD öffnen'),
    (30240, 'Advanced', 'Erweitert'),
    (30241, 'Write debug messages to the Kodi log',
     'Debug-Meldungen in das Kodi-Log schreiben'),

    # --- settings help ---------------------------------------------------
    (30261, 'The keymap only changes fullscreen video playback; the rest of '
            'Kodi is untouched.',
     'Die Tastenbelegung ändert nur die Vollbildwiedergabe; der Rest von '
     'Kodi bleibt unverändert.'),
    (30263, 'Needs a Kodi build whose PlayerControl(ShowVideoMenu) accepts '
            '"popup" and "top", such as SamuriHL\'s CoreELEC build. Other '
            'builds ignore the argument, so leave this off there and use the '
            'single Disc menu button.',
     'Benötigt einen Kodi-Build, dessen PlayerControl(ShowVideoMenu) die '
     'Argumente "popup" und "top" akzeptiert, etwa den CoreELEC-Build von '
     'SamuriHL. Andere Builds ignorieren das Argument - dort ausgeschaltet '
     'lassen und die einzelne Disc-Menü-Taste verwenden.'),
    (30264, 'Press the button you want to use, then choose whether it should '
            'need a long press. The exact button code is bound, so it works '
            'whatever kind of remote sends it.',
     'Die gewünschte Taste drücken und danach wählen, ob sie lange gedrückt '
     'werden soll. Gebunden wird der exakte Tastencode - das funktioniert '
     'unabhängig davon, welche Art von Fernbedienung ihn sendet.'),
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
