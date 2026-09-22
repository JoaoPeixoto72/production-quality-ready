---
name: drive-app-window
description: "Test a change in a running desktop window on Windows: click, type, drag, scroll, full-content screenshot (Win32, WebView2, Tauri, Electron). Use when verify needs a desktop driver. Closes no verdict. Not for web apps (use a browser instead)."
contract: CONTRACTS.md
evidence-schema: "1.3.x"
argument-hint: "-Title <window> -Process <exe without .exe> -Action <content|shot|crop|screen|click|hover|drag|wheel|rawkeys|list>"
platforms: [desktop]
version: 2.0.0
allowed-tools: Read, Glob, Grep, Bash, Write
disallowed-tools: Edit, MultiEdit, NotebookEdit
---

# Drive an app window from the terminal

What tests cannot catch is in the window. This is the harness to get there,
and the five things that break on the way.

## Boundary with verify (bilateral pair, POLICY §1.2)

This owner is a **mechanism**, not a proof strategy. It exposes the ten
actions below; `verify` decides *what* to check and *which* actions to
compose into an evidence run. No verdict closes here — this is an
instrument that produces artifacts (screenshots, event logs) that other
owners read.

The script is `scripts/gui.ps1`, and it has **no defaults for any application**:
the title and the process go on the command line every time. Put them in a pair
of variables once and forget them:

```bash
G="scripts/gui.ps1"   # from the skill folder: <host>/plugins/production-quality-ready/skills/drive-app-window/
A="-Title MyApp -Process my_app"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $G $A -Action content -Out "out\x.png"
```

## The ten actions

| Action | What it does | Parameters |
|---|---|---|
| `content` | **the one to reach for**: pins the window and captures its region from the screen | `-Out`, `-Inset` |
| `shot` | `PrintWindow` of the window, even underneath others — **can come back blank** | `-Out` |
| `crop` | a piece of `shot`, in window coordinates | `-X -Y -X2 -Y2 -Out` |
| `screen` | `CopyFromScreen` of a screen region. For what `shot` cannot get | `-X -Y -X2 -Y2 -Out` |
| `click` | press and release | `-X -Y` |
| `hover` | pointer only, no button — this is how you see a tooltip | `-X -Y` |
| `drag` | in 12 steps: a single jump does not always produce a `mousemove` in a webview | `-X -Y -X2 -Y2` |
| `wheel` | mouse wheel; negative `-X2` scrolls down | `-X -Y -X2` |
| `rawkeys` | bare `SendKeys`, **without pinning the window** (see trap 3) | `-Keys` |
| `list` | pid, hwnd, title and rectangle of every window of the process | — |

The window is pinned at `(0,0)` with `-Width 1800 -Height 1150` before every
action that takes coordinates. That is what makes the pixel in the screenshot
the pixel the click lands on.

## The five things that break

**1. The screenshot has to be `PrintWindow`, not `CopyFromScreen`.** Someone is
using the machine you are running on: a full-screen `CopyFromScreen` grabs their
browser, not the app. `PrintWindow` with `PW_RENDERFULLCONTENT` (0x2) reads the
window even underneath other windows, and shows nobody's screen.

**2. But `PrintWindow` can come back blank.** A WebView2 composites on the GPU in
another process, and what `shot` captures is the frame without the content — an
entirely white image. **This is not a broken app.** The size gives it away too: a
1800x1150 PNG weighing 8 KB has no interface inside it.

The way out is **`content`**: it pins the window and captures that region from
the screen. It does in one action what `shot` + `screen` did by hand, and it
**pulls back by `-Inset` (10 px by default) on purpose** — Windows' invisible
resize border sits *outside* what you see, so capturing the window's exact
rectangle lets a few pixels of whatever is behind leak in. The reason from point
1 still holds: the region never goes past the window's own edges.

**And the mouse pointer is in no screenshot**, by either route. To prove the
cursor's shape, ask the system (`GetCursorInfo`) and compare the handle against
`LoadCursor` of `IDC_ARROW` (32512) and `IDC_CROSS` (32515). The pointer has to
sit still for ~600 ms first: a webview only swaps the cursor after the
`mousemove`.

**3. The window moves, and `rawkeys` is a trap in both directions.**
`ShowWindow(SW_RESTORE)`, needed to bring it to the front, returns the window to
its "restored" position — which may be on another monitor. Without pinning, the
pixel in the screenshot stops being the pixel of the click and **clicks land
elsewhere without saying anything**: it looks like an app bug and it is a harness
bug. That is why the script pins before every action with coordinates.

`rawkeys` is the exception: it is a bare `SendKeys`, it does **not** pin, so the
keys go to whatever window is in front — which, after a `-Action screen`, may be
your terminal. The symptom is a feature that looks broken: an Escape that does
not close a panel, a `{DOWN}` that does not move. Before keys aimed at the app,
a `-Action hover` over a dead spot of it — that pins it, and the keys arrive:

```bash
powershell.exe ... $A -Action hover -X 900 -Y 900
powershell.exe ... $A -Action rawkeys -Keys "{ESC}"
```

**And it is not fixed by pinning inside `rawkeys`**, however much you want to:
system file dialogs are a different window, and they are where you type a path to
open a file without navigating folders. Pinning the app before typing steals
their focus, and the path ends up in the app. For those, bare `rawkeys` is the
correct one — so the choice belongs to whoever is driving, not to the script.

**4. A native `<select>` list opens in another window.** `PrintWindow` does not
capture it (use `-Action screen`), and clicking it is not trustworthy: moving the
pointer across re-highlights whatever is under the cursor, and you get something
else. **What works is the keyboard, with the list closed:**

```bash
-Action click -X <select>          # opens it
-Action rawkeys -Keys "{ESC}"      # closes it, but keeps the focus
-Action rawkeys -Keys "{HOME}"     # first option — the only reliable starting point
-Action rawkeys -Keys "{DOWN 8}"
```

Always count from `{HOME}`, and **count every option**, including the ones that
do not look like options (a "none" or a "from a file" at the top).

**5. Never find the window by `MainWindowHandle`.** .NET's
`Process.MainWindowHandle` is a heuristic, and it **breaks the moment the app
opens a second top-level window** — a region selector, a marker, a splash: it
starts returning the other one, and every action with coordinates works on the
wrong window, with no error to warn you. The lookup is by **title**, walking the
process's windows with `EnumWindows`. `-Action list` shows why this matters: a
Tauri app usually has a second, untitled 16x16 window, and that is the one the
heuristic picks.

If the script ever has to be rebuilt, this is the first thing to get right.

## When an action says it cannot find the window

`-Action list`. It prints what exists with pid, hwnd, title and rectangle, and
answers three questions at once: the app is running, the title is what you
thought, and the window is where you thought.

## Requirements

Windows, and the PowerShell that ships with it (5.1 or newer). Nothing external.

## What this owner does NOT do

- Does not decide *what* to prove — that is `verify`.
- Does not run on macOS or Linux — the harness is Win32 (register as
  `not-applicable: "non-Windows target"` in `gates.json` when it does not
  apply).
- Does not run tests — that is `code-review`.

## Instruments accepted

See `instruments.yaml`. This owner is itself the canonical producer of
its own artifacts (`gui.ps1` output); no external instrument accepted.
