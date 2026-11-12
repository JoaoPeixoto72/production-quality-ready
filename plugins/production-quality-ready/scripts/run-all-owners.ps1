#!/usr/bin/env pwsh
# run-all-owners.ps1 — kept for existing habits; the runner is run_all_owners.py
# (one implementation, tested, runs on Linux and in CI). Arguments map one to one.
#
#   pwsh scripts/run-all-owners.ps1 -RepoRoot . [-Only a,b] [-Skip c] [-DryRun] [-WebsiteUrl <url>] [-WebsiteDir <dir>]

[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [string[]]$Only = @(),
    [string[]]$Skip = @(),
    [switch]$DryRun,
    [string]$PluginRoot = "",
    [string]$WebsiteUrl = "",
    [string]$WebsiteDir = ""
)
$py = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } elseif (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { "py" }
$argv = @((Join-Path $PSScriptRoot "run_all_owners.py"), "--repo", $RepoRoot)
if ($Only)       { $argv += @("--only", ($Only -join ",")) }
if ($Skip)       { $argv += @("--skip", ($Skip -join ",")) }
if ($DryRun)     { $argv += "--dry-run" }
if ($PluginRoot) { $argv += @("--plugin", $PluginRoot) }
if ($WebsiteUrl) { $argv += @("--website-url", $WebsiteUrl) }
if ($WebsiteDir) { $argv += @("--website-dir", $WebsiteDir) }
& $py @argv
exit $LASTEXITCODE
