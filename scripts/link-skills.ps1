# link-skills.ps1 - make this plugin's skills visible to Codex.
#
# Codex reads SKILL.md files from .agents/skills (repo and its parents),
# $HOME/.agents/skills (user) and /etc/codex/skills (admin). It does not read
# .agents/plugins/, which is where install.ps1 puts the plugin. This links each
# skill into the user scope so Codex sees it in every repository.
#
# Junctions are used on Windows because they need no elevation.
#
# Usage:
#   pwsh scripts/link-skills.ps1                     # link into $HOME/.agents/skills
#   pwsh scripts/link-skills.ps1 -Dest <dir>         # link somewhere else
#   pwsh scripts/link-skills.ps1 -Remove             # unlink what this script made
#   pwsh scripts/link-skills.ps1 -Copy               # copy instead of link

[CmdletBinding()]
param(
    [string]$PluginDir = "",
    [string]$Dest = "",
    [switch]$Copy,
    [switch]$Remove
)

$ErrorActionPreference = "Stop"

if (-not $PluginDir) {
    $PluginDir = Split-Path -Parent $PSScriptRoot
}

$skillsDir = Join-Path $PluginDir "skills"

if (-not (Test-Path -LiteralPath (Join-Path $PluginDir "plugin.json"))) {
    Write-Error "Not a production-quality-ready plugin folder: $PluginDir"
}

if (-not (Test-Path -LiteralPath $skillsDir)) {
    Write-Error "No skills/ folder in $PluginDir"
}

if (-not $Dest) {
    $Dest = Join-Path ([Environment]::GetFolderPath("UserProfile")) ".agents\skills"
}

if (-not (Test-Path -LiteralPath $Dest)) {
    New-Item -ItemType Directory -Force -Path $Dest | Out-Null
}

Write-Host "Plugin: $PluginDir" -ForegroundColor Cyan
Write-Host "Target: $Dest" -ForegroundColor Cyan

$linked = 0
$skipped = 0

foreach ($skill in Get-ChildItem -Directory -LiteralPath $skillsDir) {
    if (-not (Test-Path -LiteralPath (Join-Path $skill.FullName "SKILL.md"))) {
        continue
    }

    $target = Join-Path $Dest $skill.Name

    if ($Remove) {
        if (Test-Path -LiteralPath $target) {
            $item = Get-Item -LiteralPath $target -Force
            if ($item.LinkType) {
                # Remove the link only; the skill stays in the plugin folder.
                if ($item.LinkType -eq "Junction" -or $item.LinkType -eq "SymbolicLink") {
                    [System.IO.Directory]::Delete($target, $false)
                } else {
                    Remove-Item -Recurse -Force -LiteralPath $target
                }
                Write-Host "unlinked $($skill.Name)"
                $linked++
            } else {
                Write-Host "kept $($skill.Name) (not a link; not created here)" -ForegroundColor DarkYellow
                $skipped++
            }
        }
        continue
    }

    if (Test-Path -LiteralPath $target) {
        $item = Get-Item -LiteralPath $target -Force
        if (-not $item.LinkType -and -not $Copy) {
            # A real directory with that name: not ours to delete.
            Write-Host "skipped $($skill.Name): $target exists and is not a link" -ForegroundColor DarkYellow
            $skipped++
            continue
        }
        if ($item.LinkType -or $Copy) {
            Remove-Item -Recurse -Force -LiteralPath $target
        }
    }

    if ($Copy) {
        Copy-Item -Recurse -Force -LiteralPath $skill.FullName -Destination $target
        Write-Host "copied $($skill.Name)"
    } else {
        New-Item -ItemType Junction -Path $target -Target $skill.FullName | Out-Null
        Write-Host "linked $($skill.Name)"
    }
    $linked++
}

$verb = if ($Remove) { "unlinked" } else { "linked" }
Write-Host ""
Write-Host "$verb $linked skill(s); skipped $skipped." -ForegroundColor Green

if (-not $Remove) {
    Write-Host "Codex detects skill changes automatically; restart it if a skill does not appear." -ForegroundColor Cyan
}
