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

Three entries are worth calling out:

* **Kodi OSD** opens Kodi's own player OSD by name. That bypasses the disc's
  grip on the OK button entirely, so you get the familiar player controls back,
  including the seek bar.
* **Disc menu** sends `PlayerControl(ShowVideoMenu)`. That builtin goes to the
  player itself rather than to the focused window, so it works regardless of
  what is on screen. libbluray tries the in-movie popup menu first and falls
  back to the root menu, so one button behaves like a standalone player's
  POPUP MENU / TOP MENU combo.
* **Titles** lists the playlists on the disc and plays one directly, without
  the disc menu. Kodi is then fully in charge again — OSD, seeking and resume
  all behave as they do with any other video.

### Separate popup and top menus

Some Kodi builds — [SamuriHL's CoreELEC
build](https://github.com/SamuriHL/coreelec-xbmc) among them — extend the
builtin so it takes an argument: `PlayerControl(ShowVideoMenu(popup))` opens
only the in-movie popup menu, `ShowVideoMenu(top)` only the root menu.

Upstream Kodi compares the builtin's parameter exactly, so on a stock build
the argument form matches nothing and does *silently* nothing. There is no way
to probe for the patch, so it is a setting: switch on **Separate popup and top
menu entries** (General) and two extra entries appear under **More**, and the
Title button sends the popup variant instead of the portable one. Leave it off
on a stock build.

## Installation

1. Download this repository as a ZIP.
2. In Kodi: **Add-ons → Install from zip file** and pick the ZIP.
3. Open **Settings → Keymap** and assign a button (see below). Nothing is
   bound until you do.

## Assigning a button

Nothing is bound until you say so. In **Settings → Keymap** there are two
assignable buttons:

| | |
| --- | --- |
| **Assign the button for BD Control** | opens the BD Control OSD |
| **Assign the button for the disc menu** | the disc's own popup / top menu |

Pressing either one starts the same short wizard:

1. A dialog asks you to **press the button you want to use**. Back cancels.
2. It then asks whether it should **only trigger on a long press**, or on a
   normal short press.
3. The keymap is written immediately — no restart, no SSH, no XML.

The button is bound by its **raw button code**:

```xml
<keymap>
  <FullscreenVideo>
    <keyboard>
      <key id="61517" mod="longpress">RunScript(script.bdcontrol,action=toggle)</key>
      <key id="61453">PlayerControl(ShowVideoMenu)</key>
    </keyboard>
  </FullscreenVideo>
</keymap>
```

Kodi merges every keymap section into one map keyed by that number, so the
code captured from a real press works whatever kind of device sent it —
keyboard, IR remote or CEC. There is no list of named buttons to guess from,
and the mapping only ever touches the `FullscreenVideo` window, so navigation
everywhere else in Kodi is unchanged.

> **A note on long press:** it only fires when the input driver reports a
> *held* key, and not every remote on CoreELEC does — Amlogic's IR driver only
> emits repeats when `repeat_enable` is set in `remote.conf`. If a long press
> binding does nothing, assign the button again and choose **short press**.
> The addon says as much when you pick long press.

**If the dialog never sees your press:** a button with no mapping anywhere
produces no action at all and never reaches a dialog. The wizard then offers
to pick from the Kodi log instead, which reads the `HandleKey:` lines out of
`kodi.log` — the same thing the manual procedure asks you to look for over
SSH. That needs debug logging on:
**Settings → System → Logging → Enable debug logging**.
**Show recent key presses from the log** does the same as a read-only list.

**Clear all assignments** removes both bindings and deletes the keymap file.

### Keymap Editor

If you would rather use the **Keymap Editor** addon (`script.keymap`), note
that on save it renames every *other* `*.xml` in `userdata/keymaps` to
`*.xml.bak.N` — including this addon's — unless its **Allow multiple keymap
files** setting is on. The service notices within half a minute, puts the
keymap back and tells you; the diagnostics page names the setting. Its
**Add-ons → Launch BD Control** entry writes `runaddon(script.bdcontrol)`,
which during playback opens the OSD directly.

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
* Kodi's Blu-ray playback mode and whether the extended popup/top menus are
  enabled,
* which buttons are assigned and the full contents of the generated keymap
  file,
* whether a `remote.conf` is present and what it says about key repeat, which
  is what long press depends on,
* whether debug logging is on, and the last few key presses from the log,
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
RunScript(script.bdcontrol,action=discmenu)      # popup menu, or top menu if there is none
RunScript(script.bdcontrol,action=popupmenu)     # popup menu only   (patched builds)
RunScript(script.bdcontrol,action=topmenu)       # top menu only     (patched builds)
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
RunScript(script.bdcontrol,action=assign,slot=osd)       # assign the BD Control button
RunScript(script.bdcontrol,action=assign,slot=discmenu)  # assign the disc menu button
RunScript(script.bdcontrol,action=keylog)        # recent key presses from the log
RunScript(script.bdcontrol,action=diagnostics)
RunScript(script.bdcontrol,action=clearkeys)     # clear both assignments
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
