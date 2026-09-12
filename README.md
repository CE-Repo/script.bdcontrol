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

The OSD shows the disc title, the position and the chapter counter, and holds
exactly four buttons:

| Button | What it does |
| --- | --- |
| **Popup menu** | `PlayerControl(ShowVideoMenu(popup))` — the disc's in-movie popup menu |
| **Main menu** | `PlayerControl(ShowVideoMenu(top))` — the disc's top / root menu |
| **Video OSD** | `ActivateWindow(videoosd)` — Kodi's own player OSD |
| **Diagnostics** | the report described [below](#diagnostics) |

**Video OSD** is the one that answers "OK does nothing": activating the window
by name bypasses the disc's grip on the OK button entirely, so you get the
familiar player controls back — pause, stop, the seek bar, audio and subtitle
selection — from Kodi's own OSD.

The `PlayerControl(...)` builtins behind the two menu buttons go to the player
rather than to the focused window, so they work regardless of what is on
screen.

> **A build requirement for the two menu buttons.** Upstream Kodi compares the
> builtin's parameter exactly (`paramlow == "showvideomenu"`), so the
> `ShowVideoMenu(popup)` / `ShowVideoMenu(top)` argument form matches nothing
> and does *silently* nothing on a stock build. Telling the popup and the top
> menu apart needs a build carrying the ShowVideoMenu patch —
> [SamuriHL's CoreELEC build](https://github.com/SamuriHL/coreelec-xbmc) among
> them. There is no way to probe for it from a script. On a stock build, use
> Kodi's own **Video OSD** button, or map the portable
> `PlayerControl(ShowVideoMenu)` to a remote button directly.

### Button style

The four buttons can be shown three ways, under **Settings → Appearance →
Buttons → Button style**:

| Style | |
| --- | --- |
| **Icons** | the glyph only |
| **Text** | the label only |
| **Icons and text** | both (the default) |

The line under the buttons that explains the focused one only shows for
**Icons** — with a label already on the button, it would just repeat it.

## Installation

1. Download this repository as a ZIP.
2. In Kodi: **Add-ons → Install from zip file** and pick the ZIP.
3. Map a remote button with **Keymap Editor** (see below). Nothing is bound
   until you do.

## Mapping a button

BD Control does not manage keymaps itself — key assignment is the
[**Keymap Editor**](https://github.com/tamland/xbmc-keymap-editor)
(`script.keymap`) addon's job, and it is the only supported way to bind a
button.

### The quick way

1. Start playback of the disc, or just open Keymap Editor from
   **Add-ons → Program add-ons**.
2. Choose **Edit keymap → Fullscreen video → Add-ons**.
3. Pick **BD Control** from the list.
4. Press the remote button you want to use, and save.

That writes `runaddon(script.bdcontrol)` for the button, which opens the BD
Control OSD — and closes it again when the same button is pressed a second
time.

Keymap Editor also offers **Long press** for a mapping, which is handy if you
want to keep the button's short press for something else. Long press only
fires when the input driver reports a *held* key, and not every remote on
CoreELEC does: Amlogic's IR driver only emits repeats when `repeat_enable` is
set in `remote.conf`. The [diagnostics](#diagnostics) page reports what your
`remote.conf` says.

### Mapping the individual commands

Keymap Editor's **Add-ons** category can only write the plain "launch the
addon" form. To put one specific command on a button — the popup menu on a
POPUP key, say — write the keymap by hand. Drop a file into
`userdata/keymaps/` (any name ending in `.xml`):

```xml
<keymap>
  <FullscreenVideo>
    <keyboard>
      <key id="61517" mod="longpress">RunScript(script.bdcontrol)</key>
      <key id="61453">RunScript(script.bdcontrol,action=popupmenu)</key>
      <key id="61454">RunScript(script.bdcontrol,action=topmenu)</key>
    </keyboard>
  </FullscreenVideo>
</keymap>
```

Kodi merges every keymap section into one map keyed by the raw button code, so
a code captured from a real press works whatever kind of device sent it —
keyboard, IR remote or CEC. Keeping the mapping inside `<FullscreenVideo>`
leaves navigation everywhere else in Kodi unchanged.

To find the button code, switch on
**Settings → System → Logging → Enable debug logging**, press the button, and
look for the `HandleKey:` lines in `kodi.log`.

The diagnostics page lists every keymap entry that mentions `script.bdcontrol`,
so a binding that does not fire can be told apart from one that was never
written.

> **Note on Keymap Editor and other keymap files:** on save it renames every
> *other* `*.xml` in `userdata/keymaps` to `*.xml.bak.N`, unless its **Allow
> multiple keymap files** setting is on. Switch that setting on if you keep a
> hand-written keymap alongside it.

## Settings

**General**

* *Show a hint when a disc menu takes over* — a short notification whenever a
  disc menu starts driving playback.
* *Open BD Control automatically* — show the OSD by itself in that situation.
  It fires once per disc, and never while an OSD you opened yourself is up: a
  disc menu jumps between titles constantly, and each jump looks like a fresh
  start to Kodi's playback callbacks.
* *Close the OSD after* — idle timeout in seconds; `0` keeps it open.

**Appearance**

* *Button style* — icons, text, or both.
* *Vertical position* — `0 %` anchors the panel at the bottom, `100 %` moves
  it to just below the top edge.
* A colour and an opacity for each part of the OSD — panel, screen dim, title,
  text, and the focused / unfocused button background and text.
  Each offers a 50-colour palette plus a custom **HEX colour** entry.
* *Show OSD preview (3 seconds)* — renders the OSD with sample data so a
  colour, style or position change can be checked without a disc in the drive.

**Tools** holds the OSD and the diagnostics report, so both can be reached
without playback.

**Advanced** has the addon's own debug logging.

## Diagnostics

**Settings → Tools → Diagnostics** reports the things a UHD Blu-ray needs on
CoreELEC:

* Kodi and OS version,
* the optical drive device nodes and whether a disc is present,
* `libbluray`, `libaacs`, `libbdplus` and a `KEYDB.cfg` (needed for encrypted
  retail discs),
* Kodi's Blu-ray playback mode,
* whether Keymap Editor is installed, and every keymap entry that refers to
  BD Control,
* whether a `remote.conf` is present and what it says about key repeat, which
  is what long press depends on,
* whether Kodi's debug logging is on,
* the live state of the current playback: whether the disc menu is in control,
  whether seeking is allowed, chapter counters, track counts and the output
  resolution.

## Scripting

These are all the commands BD Control provides. Each one is reachable from a
keymap, a skin button or another addon:

```
RunScript(script.bdcontrol)
# opens and closes the BD Control OSD

RunScript(script.bdcontrol,action=osd)
# opens Kodi's own video OSD

RunScript(script.bdcontrol,action=popupmenu)
# opens the disc's popup menu only

RunScript(script.bdcontrol,action=topmenu)
# opens the disc's main menu only

RunScript(script.bdcontrol,action=diagnostics)
# opens the diagnostics report
```

## Licence

MIT. See [LICENSE](LICENSE).
