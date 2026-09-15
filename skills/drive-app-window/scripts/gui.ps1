# Drive a desktop app's window from the terminal (Windows).
#
# Built for Tauri/WebView2, works on any native window. The reason behind every
# choice here is in the `drive-app-window` skill — in particular the five things
# that break, which this script exists in order not to break:
#
#   1. a shot is `PrintWindow` with PW_RENDERFULLCONTENT, never `CopyFromScreen`
#      (someone is using the machine; CopyFromScreen grabs their screen instead
#      of the app);
#   2. PrintWindow can come back blank on a WebView2, which composites on the
#      GPU in another process — that is what `content` is for;
#   3. the window is pinned at (0,0) before every action that takes coordinates
#      (SW_RESTORE returns it to its "restored" position, possibly on another
#      monitor, and clicks start landing elsewhere without saying anything);
#   4. a native `<select>` popup opens in its own window — PrintWindow does not
#      capture it; use `screen` for that one;
#   5. the window is found by TITLE with EnumWindows, never by
#      `MainWindowHandle`: that .NET heuristic returns the wrong window the
#      moment the app opens a second top-level one.

param(
  [Parameter(Mandatory = $true)][string]$Action,
  [int]$X = 0,
  [int]$Y = 0,
  [int]$X2 = 0,
  [int]$Y2 = 0,
  [string]$Out = "",
  [string]$Keys = "",
  # The window is found by title (what the title bar shows, or part of it) and
  # the process by executable name without `.exe`. No defaults on purpose: a
  # default for one app is exactly why a harness stops serving the next one.
  [string]$Title = "",
  [string]$Process = "",
  # The window is pinned to this size. Big enough for the whole interface, and
  # the same across every action so the pixel in the shot is the pixel clicked.
  [int]$Width = 1800,
  [int]$Height = 1150,
  # How far `content` pulls back from the edges. Windows' invisible resize
  # border sits *outside* what you see, so capturing the exact window rectangle
  # lets a few pixels of whatever is behind leak in.
  [int]$Inset = 10
)

if (-not $Title) { throw "Missing -Title (the window title, or part of it)." }
if (-not $Process) { throw "Missing -Process (the executable name, without .exe)." }

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms, System.Drawing

Add-Type @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public class Native {
  public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);

  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr lParam);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowTextW(IntPtr hWnd, StringBuilder s, int max);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowTextLengthW(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdc, uint flags);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int cmd);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr hWnd, int x, int y, int w, int h, bool repaint);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, int d, UIntPtr extra);

  [StructLayout(LayoutKind.Sequential)]
  public struct RECT { public int Left, Top, Right, Bottom; }

  // Every visible top-level window of the process. Deliberately a list: an app
  // usually has more than one, and the caller is the one that picks by title.
  public static List<IntPtr> WindowsOfProcess(uint target) {
    List<IntPtr> found = new List<IntPtr>();
    EnumWindows(delegate(IntPtr h, IntPtr l) {
      uint pid; GetWindowThreadProcessId(h, out pid);
      if (pid == target && IsWindowVisible(h)) found.Add(h);
      return true;
    }, IntPtr.Zero);
    return found;
  }

  public static string TitleOf(IntPtr h) {
    int n = GetWindowTextLengthW(h);
    if (n == 0) return "";
    StringBuilder s = new StringBuilder(n + 1);
    GetWindowTextW(h, s, s.Capacity);
    return s.ToString();
  }
}
"@

$SW_RESTORE = 9
$PW_RENDERFULLCONTENT = 0x2
$MOUSEEVENTF_LEFTDOWN = 0x0002
$MOUSEEVENTF_LEFTUP = 0x0004
$MOUSEEVENTF_WHEEL = 0x0800

# ---------------------------------------------------------------- the window --

function Get-AppWindow {
  param([string]$Name)

  $procs = Get-Process -Name $Process -ErrorAction SilentlyContinue
  if (-not $procs) { throw "$Process.exe is not running." }

  foreach ($p in $procs) {
    foreach ($h in [Native]::WindowsOfProcess([uint32]$p.Id)) {
      $t = [Native]::TitleOf($h)
      if ($t -and $t.Contains($Name)) { return $h }
    }
  }

  # Fail saying what is there, instead of silently returning the wrong window.
  $seen = @()
  foreach ($p in $procs) {
    foreach ($h in [Native]::WindowsOfProcess([uint32]$p.Id)) {
      $t = [Native]::TitleOf($h)
      if ($t) { $seen += $t }
    }
  }
  throw "No window titled '$Name'. Visible: $($seen -join ' | ')"
}

# Pin the window before any action with coordinates: this is what makes the
# pixel in the shot the same pixel the click lands on.
function Lock-Window {
  param([IntPtr]$H)
  if ([Native]::IsIconic($H)) { [void][Native]::ShowWindow($H, $SW_RESTORE) }
  [void][Native]::SetForegroundWindow($H)
  [void][Native]::MoveWindow($H, 0, 0, $Width, $Height, $true)
  Start-Sleep -Milliseconds 350
}

function Save-Png {
  param([System.Drawing.Bitmap]$Bmp, [string]$Path)
  if (-not $Path) { throw "Missing -Out." }
  $dir = Split-Path -Parent $Path
  if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $Bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
  Write-Output "saved: $Path ($($Bmp.Width)x$($Bmp.Height))"
}

# The window itself, even underneath other windows. Never CopyFromScreen.
function Get-WindowShot {
  param([IntPtr]$H)
  $r = New-Object Native+RECT
  [void][Native]::GetWindowRect($H, [ref]$r)
  $w = $r.Right - $r.Left
  $h = $r.Bottom - $r.Top
  $bmp = New-Object System.Drawing.Bitmap($w, $h)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $hdc = $g.GetHdc()
  [void][Native]::PrintWindow($H, $hdc, $PW_RENDERFULLCONTENT)
  $g.ReleaseHdc($hdc)
  $g.Dispose()
  return $bmp
}

# ----------------------------------------------------------------- actions --

switch ($Action) {

  # The one to reach for. Pins the window and captures its region from the
  # screen, pulled back by -Inset. Does in one action what `shot` + `screen`
  # did by hand, without letting in what is behind.
  "content" {
    $h = Get-AppWindow -Name $Title
    Lock-Window -H $h
    $r = New-Object Native+RECT
    [void][Native]::GetWindowRect($h, [ref]$r)
    $x = $r.Left + $Inset
    $y = $r.Top
    $w = ($r.Right - $r.Left) - (2 * $Inset)
    $ht = ($r.Bottom - $r.Top) - $Inset
    if ($w -le 0 -or $ht -le 0) { throw "Window smaller than the inset ($Inset)." }
    $bmp = New-Object System.Drawing.Bitmap($w, $ht)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($x, $y, 0, 0, (New-Object System.Drawing.Size($w, $ht)))
    $g.Dispose()
    Save-Png -Bmp $bmp -Path $Out
    $bmp.Dispose()
  }

  # PrintWindow. Reads the window under other windows — and can come back
  # entirely blank on a WebView2. See `content`.
  "shot" {
    $h = Get-AppWindow -Name $Title
    Lock-Window -H $h
    $bmp = Get-WindowShot -H $h
    Save-Png -Bmp $bmp -Path $Out
    $bmp.Dispose()
  }

  "crop" {
    $h = Get-AppWindow -Name $Title
    Lock-Window -H $h
    $bmp = Get-WindowShot -H $h
    $w = $X2 - $X
    $ht = $Y2 - $Y
    if ($w -le 0 -or $ht -le 0) { throw "Empty crop: -X -Y -X2 -Y2." }
    $rect = New-Object System.Drawing.Rectangle($X, $Y, $w, $ht)
    $cut = $bmp.Clone($rect, $bmp.PixelFormat)
    Save-Png -Bmp $cut -Path $Out
    $cut.Dispose(); $bmp.Dispose()
  }

  # The screen itself (CopyFromScreen). Only for what PrintWindow cannot get:
  # the open list of a native `<select>`, which lives in its own window.
  "screen" {
    $w = $X2 - $X
    $ht = $Y2 - $Y
    if ($w -le 0 -or $ht -le 0) { throw "Empty region: -X -Y -X2 -Y2." }
    $bmp = New-Object System.Drawing.Bitmap($w, $ht)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($X, $Y, 0, 0, (New-Object System.Drawing.Size($w, $ht)))
    $g.Dispose()
    Save-Png -Bmp $bmp -Path $Out
    $bmp.Dispose()
  }

  "click" {
    $h = Get-AppWindow -Name $Title
    Lock-Window -H $h
    [void][Native]::SetCursorPos($X, $Y)
    Start-Sleep -Milliseconds 120
    [Native]::mouse_event($MOUSEEVENTF_LEFTDOWN, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 60
    [Native]::mouse_event($MOUSEEVENTF_LEFTUP, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 250
    Write-Output "click: $X,$Y"
  }

  # Pointer only, no button: this is how you see a tooltip.
  "hover" {
    $h = Get-AppWindow -Name $Title
    Lock-Window -H $h
    [void][Native]::SetCursorPos($X, $Y)
    Start-Sleep -Milliseconds 400
    Write-Output "pointer: $X,$Y"
  }

  "drag" {
    [void][Native]::SetCursorPos($X, $Y)
    Start-Sleep -Milliseconds 200
    [Native]::mouse_event($MOUSEEVENTF_LEFTDOWN, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 150
    # In steps: a single jump does not always produce a `mousemove` in a webview.
    $steps = 12
    for ($i = 1; $i -le $steps; $i++) {
      $px = $X + [int](($X2 - $X) * $i / $steps)
      $py = $Y + [int](($Y2 - $Y) * $i / $steps)
      [void][Native]::SetCursorPos($px, $py)
      Start-Sleep -Milliseconds 40
    }
    Start-Sleep -Milliseconds 150
    [Native]::mouse_event($MOUSEEVENTF_LEFTUP, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 300
    Write-Output "drag: $X,$Y -> $X2,$Y2"
  }

  "wheel" {
    $h = Get-AppWindow -Name $Title
    Lock-Window -H $h
    [void][Native]::SetCursorPos($X, $Y)
    Start-Sleep -Milliseconds 120
    [Native]::mouse_event($MOUSEEVENTF_WHEEL, 0, 0, ($X2 * 12), [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 250
    Write-Output "wheel: $X2"
  }

  "rawkeys" {
    if (-not $Keys) { throw "Missing -Keys." }
    # **It does not pin the window, on purpose.** Keys go to whatever window is
    # in front, and sometimes the one that matters is not the app: it is the
    # system file dialog, which is where you type a path. Pinning the app first
    # would steal its focus and the path would land in the app.
    #
    # The price is that keys aimed at the app need a `-Action hover` first —
    # that one pins. Without it, after a `-Action screen` the keys go to the
    # terminal and the app looks broken.
    [System.Windows.Forms.SendKeys]::SendWait($Keys)
    Start-Sleep -Milliseconds 250
    Write-Output "keys: $Keys"
  }

  # List what is there: the first thing to run when an action says it cannot
  # find the window.
  "list" {
    $procs = Get-Process -Name $Process -ErrorAction SilentlyContinue
    if (-not $procs) { Write-Output "$Process.exe is not running"; break }
    foreach ($p in $procs) {
      foreach ($hw in [Native]::WindowsOfProcess([uint32]$p.Id)) {
        $t = [Native]::TitleOf($hw)
        $r = New-Object Native+RECT
        [void][Native]::GetWindowRect($hw, [ref]$r)
        Write-Output ("pid={0} hwnd={1} '{2}' [{3},{4} {5}x{6}]" -f $p.Id, $hw, $t, $r.Left, $r.Top, ($r.Right - $r.Left), ($r.Bottom - $r.Top))
      }
    }
  }

  default { throw "Unknown action: $Action" }
}
