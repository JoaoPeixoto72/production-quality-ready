# install.ps1 — Installer for production-quality-ready plugin
# Usage:
#   irm https://raw.githubusercontent.com/JoaoPeixoto72/production-quality-ready/main/install.ps1 | iex
#   Or locally:
#   pwsh install.ps1 [-Global] [-TargetDir <path>] [-Force]

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [switch]$Global,

    [Parameter(Mandatory=$false)]
    [string]$TargetDir = "",

    [Parameter(Mandatory=$false)]
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/JoaoPeixoto72/production-quality-ready.git"
$PluginName = "production-quality-ready"

Write-Host "=== Installing $PluginName plugin ===" -ForegroundColor Cyan

# Determine destination
if ($TargetDir) {
    $Dest = Resolve-Path -LiteralPath $TargetDir -ErrorAction SilentlyContinue
    if (-not $Dest) { $Dest = $TargetDir }
} elseif ($Global) {
    $UserProfile = [Environment]::GetFolderPath("UserProfile")
    $Dest = Join-Path $UserProfile ".gemini\config\plugins\$PluginName"
} else {
    # Project-local install into .agents/plugins/production-quality-ready
    $CurrentDir = Get-Location
    $Dest = Join-Path $CurrentDir ".agents\plugins\$PluginName"
}

Write-Host "Destination: $Dest" -ForegroundColor Yellow

if (Test-Path $Dest) {
    if ($Force) {
        Write-Host "Overwriting existing installation at $Dest..." -ForegroundColor DarkYellow
        Remove-Item -Recurse -Force -LiteralPath $Dest
    } else {
        Write-Host "Directory already exists at $Dest. Use -Force to overwrite." -ForegroundColor Red
        exit 1
    }
}

$Parent = Split-Path -Parent $Dest
if (-not (Test-Path $Parent)) {
    New-Item -ItemType Directory -Force -Path $Parent | Out-Null
}

# If running from within the clone repo itself
$LocalScriptRoot = $PSScriptRoot
if ($LocalScriptRoot -and (Test-Path (Join-Path $LocalScriptRoot "plugin.json"))) {
    Write-Host "Copying from local source..." -ForegroundColor Green
    Copy-Item -Recurse -Force -LiteralPath $LocalScriptRoot -Destination $Dest
    $copiedGit = Join-Path $Dest ".git"
    if (Test-Path $copiedGit) { Remove-Item -Recurse -Force -LiteralPath $copiedGit }
} else {
    Write-Host "Cloning from GitHub ($RepoUrl)..." -ForegroundColor Green
    git clone --depth 1 $RepoUrl $Dest
    $clonedGit = Join-Path $Dest ".git"
    if (Test-Path $clonedGit) { Remove-Item -Recurse -Force -LiteralPath $clonedGit }
}

Write-Host ""
Write-Host "Plugin successfully installed to: $Dest" -ForegroundColor Green
Write-Host ""
Write-Host "To use with Claude Code:" -ForegroundColor Cyan
Write-Host "  1. In Claude Code terminal:"
Write-Host "     /plugin marketplace add JoaoPeixoto72/production-quality-ready"
Write-Host "     /plugin install production-quality-ready@JoaoPeixoto72/production-quality-ready"
Write-Host "  2. Or start with local flag: claude --plugin-dir $Dest"
Write-Host ""
Write-Host "To use with Antigravity:" -ForegroundColor Cyan
Write-Host "  The plugin is active in your workspace under .agents/plugins/$PluginName"
Write-Host "  Run: 'run audit-app' or 'use the bootstrap-project skill' in chat."
Write-Host ""
