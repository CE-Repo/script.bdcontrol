# BD Control (`script.bdcontrol`)

Player controls for Blu-ray and UHD Blu-ray **disc menus** in Kodi / CoreELEC.

## The problem

When Kodi plays a Blu-ray with full disc menus, the disc's own menu system
(HDMV or BD-J) takes over the remote. Kodi forwards the navigation actions —
up, down, left, right and **OK** — straight to the disc, which is exactly what
makes the menus work.

The side effect is that once a title is playing, there is no button left to
open Kodi's player OSD:

* pressing **OK** does nothing at all — no progress bar, no player controls,
* pause, stop, seeking, audio and subtitle selection are unreachable,
* only **chapter forward / back** still respond, because those are not
  navigation actions.

This is by design, not a bug in CoreELEC: when you play from the disc menu,
the disc is in charge. BD Control gives you a way back in.

## What the addon does

BD Control adds its own on-screen display that opens on a spare remote button.
Because the keymap is evaluated *before* the action reaches the player, that
button is not swallowed by the disc, and the dialog that opens receives the
remote itself — so OK, the arrow keys and Back all work normally inside it.

From the OSD you can reach:

| Row | Buttons |
| --- | --- |
| Playback | Disc menu · Play/Pause · Stop · Previous chapter · Next chapter · Rewind · Fast forward |
| Tools | **Kodi OSD** · Audio track · Subtitles · Video settings · Codec info · Titles · More |

Plus, under **More**: Kodi's audio and subtitle settings, subtitle toggle, next
audio language, the Blu-ray playback mode, disc eject, and a diagnostics
report.

Two entries are worth calling out:

* **Kodi OSD** opens Kodi's own player OSD by name. That bypasses the disc's
  grip on the OK button entirely, so you get the familiar player controls back,
  including the seek bar.
* **Titles** lists the playlists on the disc and plays one directly, without
  the disc menu. Kodi is then fully in charge again — OSD, seeking and resume
  all behave as they do with any other video.

## Installation

1. Download this repository as a ZIP.
2. In Kodi: **Add-ons → Install from zip file** and pick the ZIP.
3. The keymap is installed automatically the first time the service starts.

## Which button opens BD Control?

By default: **hold OK** during playback.

A *short* press of OK still goes to the disc, so navigating the disc menu is
unchanged; only holding the button opens BD Control. Additional triggers can be
enabled in **Settings → Keymap**:

| Trigger | Default |
| --- | --- |
| Long press OK | on |
| Menu / Title button | on |
| Info button | off |
| Context menu button (C) | off |
| Long press Back | off |
| Display button → opens the Kodi OSD directly | off |
| Stop button → stops playback | off |

The generated keymap is written to
`special://profile/keymaps/script.bdcontrol.xml` and only ever touches the
`FullscreenVideo` window — navigation everywhere else in Kodi is untouched.
It is rewritten whenever you change those settings, and removing it (or using
**Remove keymap**) restores Kodi's stock behaviour.

## Settings

**General**

* *Show a hint when a disc menu takes over* — a short notification naming the
  trigger button, whenever a disc menu starts driving playback.
* *Open BD Control automatically* — show the OSD by itself in that situation.
* *Close the OSD after* — idle timeout in seconds; `0` keeps it open.
* *Seek step* — how far the rewind / fast forward buttons jump.

**Tools** contains the OSD, the Blu-ray playback mode switch and the
diagnostics report, so they can be reached without a disc in the drive.

## Diagnostics

**Settings → Tools → Diagnostics** reports the things a UHD Blu-ray needs on
CoreELEC:

* Kodi and OS version,
* the optical drive device nodes and whether a disc is present,
* `libbluray`, `libaacs`, `libbdplus` and a `KEYDB.cfg` (needed for encrypted
  retail discs),
* Kodi's Blu-ray playback mode,
* which BD Control triggers are active,
* the live state of the current playback: whether the disc menu is in control,
  whether seeking is allowed, chapter counters, track counts and the output
  resolution.

*Write diagnostics to the Kodi log* puts the same report into `kodi.log`, which
is the quickest thing to attach to a forum post.

## Scripting

Every command is reachable from a keymap, a skin button or another addon:

```
RunScript(script.bdcontrol,action=toggle)        # open / close the BD Control OSD
RunScript(script.bdcontrol,action=osd)           # Kodi's own player OSD
RunScript(script.bdcontrol,action=discmenu)      # back to the disc menu
RunScript(script.bdcontrol,action=playpause)
RunScript(script.bdcontrol,action=stop)
RunScript(script.bdcontrol,action=nextchapter)
RunScript(script.bdcontrol,action=previouschapter)
RunScript(script.bdcontrol,action=seek,seconds=60)
RunScript(script.bdcontrol,action=audio)
RunScript(script.bdcontrol,action=subtitles)
RunScript(script.bdcontrol,action=titles)
RunScript(script.bdcontrol,action=discmode)
RunScript(script.bdcontrol,action=eject)
RunScript(script.bdcontrol,action=diagnostics)
RunScript(script.bdcontrol,action=install_keymap)
RunScript(script.bdcontrol,action=remove_keymap)
```

## Development

The repository carries its own generators and checks, all standard library
only:

```
python3 tools/make_assets.py     # regenerate the PNG textures and the icon
python3 tools/make_strings.py    # regenerate the English and German .po files
python3 tools/check_strings.py   # every string id used by the code is defined
python3 tools/smoke_test.py      # exercise the addon against stubbed Kodi APIs
```

`tools/smoke_test.py` runs the real addon modules against small stand-ins for
`xbmc`, `xbmcgui`, `xbmcaddon` and `xbmcvfs`, covering the keymap generation,
the disc path handling, the player state, the actions, the title browser, the
diagnostics report, the service and the OSD dialog.

## Licence

MIT. See [LICENSE](LICENSE).
