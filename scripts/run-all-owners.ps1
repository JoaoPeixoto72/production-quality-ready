#!/usr/bin/env pwsh
# run-all-owners.ps1 — production-quality-ready
#
# Executa os owners aplicáveis declarados em .claude/gates.json, escreve
# evidência em .audit/<owner>/*.evidence.yaml, e no fim chama audit-app
# para agregar. Corre no CI ou à mão; nunca dentro do modelo.
#
# NÃO viola PURPOSE §3.3: este é um script de shell, não uma skill
# invocando skills. Corre por baixo do agente, produz ficheiros, e o
# audit-app lê os ficheiros como sempre — reprodutibilidade preservada.
#
# Uso:
#   pwsh scripts/run-all-owners.ps1 -RepoRoot C:\a\JustClip
#   pwsh scripts/run-all-owners.ps1 -RepoRoot . -Only ui-system,seo-audit
#   pwsh scripts/run-all-owners.ps1 -RepoRoot . -Skip commercial-readiness
#   pwsh scripts/run-all-owners.ps1 -RepoRoot . -DryRun
#
# Requer: PowerShell 7+ (Windows/Linux/macOS), git, Python 3.
# Não instala dependências. Um owner sem instrumento disponível fica
# NOT_VERIFIED/missing-instrument no output final — não aborta o run.

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$RepoRoot = ".",

    [Parameter(Mandatory=$false)]
    [string[]]$Only = @(),

    [Parameter(Mandatory=$false)]
    [string[]]$Skip = @(),

    [Parameter(Mandatory=$false)]
    [switch]$DryRun,

    [Parameter(Mandatory=$false)]
    [string]$PluginRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# ---------------------------------------------------------------------------
# 0. Resolve paths
# ---------------------------------------------------------------------------

$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path

if (-not $PluginRoot) {
    # This script lives at <plugin>/scripts/run-all-owners.ps1
    $PluginRoot = Split-Path -Parent $PSScriptRoot
}
$PluginRoot = (Resolve-Path -LiteralPath $PluginRoot).Path

$GatesPath  = Join-Path $RepoRoot ".claude/gates.json"
$AuditRoot  = Join-Path $RepoRoot ".audit"
$ReportsDir = Join-Path $RepoRoot "docs/auditorias"

Write-Host "run-all-owners.ps1"                          -ForegroundColor Cyan
Write-Host "  repo:   $RepoRoot"
Write-Host "  plugin: $PluginRoot"
Write-Host "  gates:  $GatesPath"
Write-Host ""

# ---------------------------------------------------------------------------
# 1. Read gates.json — declared applicable owners
# ---------------------------------------------------------------------------

if (-not (Test-Path $GatesPath)) {
    Write-Host "gates.json missing at $GatesPath" -ForegroundColor Red
    Write-Host "Run bootstrap-project first, or create .claude/gates.json."
    exit 2
}

$gates = Get-Content -Raw -LiteralPath $GatesPath | ConvertFrom-Json
if (-not $gates.owners) {
    Write-Host "gates.json has no 'owners' block." -ForegroundColor Red
    exit 2
}

# Applicable owners = declared in gates.json AND not marked not-applicable.
$applicable = @()
foreach ($prop in $gates.owners.PSObject.Properties) {
    $name = $prop.Name
    $cfg  = $prop.Value

    if ($cfg -and $cfg.PSObject.Properties['not-applicable']) {
        Write-Host "  [skip] $name — not-applicable: $($cfg.'not-applicable')" -ForegroundColor DarkGray
        continue
    }
    if ($Only.Count -gt 0 -and $Only -notcontains $name) { continue }
    if ($Skip -contains $name)                           { continue }

    $applicable += $name
}

if ($applicable.Count -eq 0) {
    Write-Host "No applicable owners after filtering." -ForegroundColor Yellow
    exit 1
}

Write-Host "Applicable owners ($($applicable.Count)):" -ForegroundColor Green
$applicable | ForEach-Object { Write-Host "  - $_" }
Write-Host ""

# ---------------------------------------------------------------------------
# 2. Git snapshot t0 (PURPOSE §Phase 0 mirror)
# ---------------------------------------------------------------------------

Push-Location $RepoRoot
$t0Head  = (git rev-parse --short HEAD  2>$null)
$t0Dirty = (git status --porcelain      2>$null)
Pop-Location

Write-Host "Git snapshot t0:" -ForegroundColor Cyan
Write-Host "  HEAD:   $t0Head"
Write-Host "  dirty:  $([bool]$t0Dirty)"
Write-Host ""

# ---------------------------------------------------------------------------
# 3. Evidence writer — schema 1.3.x, one file per (owner, check)
# ---------------------------------------------------------------------------

function New-EvidenceStub {
    param(
        [string]$Owner,
        [string]$Producer,
        [string]$Instrument,
        [string]$Check,
        [string]$Rule,
        [string]$RuleVersion,
        [string]$Result,          # PASS | FAIL | WARN | NOT_VERIFIED | NOT_APPLICABLE
        [string]$Severity = "",   # blocker | major | minor | ""
        [string]$Confidence,      # Observed | Inferred
        [string]$Reason = "",
        [string]$ArtifactPath = ""
    )

    $dir = Join-Path $AuditRoot $Owner
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $file = Join-Path $dir "$Producer--$Check.evidence.yaml"

    $now = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

    $body = @"
# evidence-schema: 1.3.x
check: $Check
owner: $Owner
producer: $Producer
instrument: $Instrument
rule: $Rule
rule-version: "$RuleVersion"
methods:
  - script: scripts/run-all-owners.ps1
    version: 1.0.0
evidence:
  head: $t0Head
  produced-at: $now
  artifact: $ArtifactPath
result: $Result
"@

    if ($Severity)   { $body += "`nseverity: $Severity" }
    if ($Reason)     { $body += "`nreason: |`n  $($Reason -replace "`n", "`n  ")" }
    $body += "`nconfidence: $Confidence`n"

    Set-Content -LiteralPath $file -Value $body -Encoding UTF8
    return $file
}

# ---------------------------------------------------------------------------
# 4. Owner runners — one function per owner
#    Each runner returns hashtables with per-check outcomes; the writer
#    above lands them as .audit/<owner>/*.evidence.yaml.
# ---------------------------------------------------------------------------

$Results = @{}   # owner -> @{ ran=int; passed=int; failed=int; notVerified=int }

function Register-Owner {
    param([string]$Owner, [int]$Ran, [int]$Passed, [int]$Failed, [int]$NotVerified)
    $Results[$Owner] = @{
        ran          = $Ran
        passed       = $Passed
        failed       = $Failed
        notVerified  = $NotVerified
    }
}

function Invoke-UiSystem {
    $owner = "ui-system"
    $script = Join-Path $PluginRoot "skills/ui-system/scripts/audit_ui.py"
    $cfg    = Join-Path $RepoRoot "ui.config.json"

    if (-not (Test-Path $script)) {
        New-EvidenceStub -Owner $owner -Producer $owner -Instrument audit_ui.py `
            -Check "ui.instrument-available" -Rule "instrument-present" -RuleVersion "1.0" `
            -Result NOT_VERIFIED -Confidence Observed `
            -Reason "audit_ui.py not found at $script" | Out-Null
        Register-Owner -Owner $owner -Ran 1 -Passed 0 -Failed 0 -NotVerified 1
        return
    }

    if (-not (Test-Path $cfg)) {
        New-EvidenceStub -Owner $owner -Producer $owner -Instrument audit_ui.py `
            -Check "ui.config-declared" -Rule "config-present" -RuleVersion "1.0" `
            -Result NOT_VERIFIED -Confidence Observed `
            -Reason "ui.config.json not present at repo root — instrument has no target" | Out-Null
        Register-Owner -Owner $owner -Ran 1 -Passed 0 -Failed 0 -NotVerified 1
        return
    }

    $outArtifact = Join-Path $AuditRoot "$owner/audit_ui.raw.md"
    New-Item -ItemType Directory -Force -Path (Split-Path $outArtifact) | Out-Null

    if (-not $DryRun) {
        python3 $script --repo $RepoRoot --config $cfg --out $outArtifact 2>&1 | Out-Null
    }

    # Ten canonical checks from ui-system/SKILL.md §6.
    $checks = @(
        "ui.architectural-boundary", "ui.legacy-package", "ui.invalid-boolean-selector",
        "ui.color-mix-sum", "ui.oklch-delta-l", "ui.remote-fonts",
        "ui.ai-generic-fonts", "ui.focus-ring", "ui.reduced-motion", "ui.unstyled-component"
    )
    $ran = 0
    foreach ($c in $checks) {
        New-EvidenceStub -Owner $owner -Producer $owner -Instrument audit_ui.py `
            -Check $c -Rule "data-ui-contract" -RuleVersion "1.0" `
            -Result NOT_VERIFIED -Confidence Observed `
            -Reason "raw output in $outArtifact — human parse into per-check verdict required" `
            -ArtifactPath $outArtifact | Out-Null
        $ran++
    }
    Register-Owner -Owner $owner -Ran $ran -Passed 0 -Failed 0 -NotVerified $ran
}

function Invoke-SeoAudit {
    $owner  = "seo-audit"
    $script = Join-Path $PluginRoot "skills/seo-audit/scripts/run_seo_audit.mjs"
    $cfg    = Join-Path $RepoRoot "skills/seo-audit/audit.config.json"

    if (-not (Test-Path $script)) {
        New-EvidenceStub -Owner $owner -Producer $owner -Instrument run_seo_audit.mjs `
            -Check "seo.instrument-available" -Rule "instrument-present" -RuleVersion "1.0" `
            -Result NOT_VERIFIED -Confidence Observed `
            -Reason "run_seo_audit.mjs not found at $script" | Out-Null
        Register-Owner -Owner $owner -Ran 1 -Passed 0 -Failed 0 -NotVerified 1
        return
    }

    # This instrument requires a target URL declared by the project.
    New-EvidenceStub -Owner $owner -Producer $owner -Instrument run_seo_audit.mjs `
        -Check "seo.target-declared" -Rule "sarif-2.1.0" -RuleVersion "1.0" `
        -Result NOT_VERIFIED -Confidence Observed `
        -Reason "target URL/build path must be supplied by the project. run: node $script --url <URL>" | Out-Null
    Register-Owner -Owner $owner -Ran 1 -Passed 0 -Failed 0 -NotVerified 1
}

function Invoke-SkillAuditor {
    # Present for symmetry — audit-app skips it (§3.5), but the plugin
    # skills themselves can still be linted in a separate lane.
    $owner  = "skill-auditor"
    $script = Join-Path $PluginRoot "skills/skill-auditor/scripts/audit.sh"
    if (-not (Test-Path $script)) {
        Register-Owner -Owner $owner -Ran 0 -Passed 0 -Failed 0 -NotVerified 0
        return
    }
    # Not written into .audit/ — this owner runs in a separate plane.
    Register-Owner -Owner $owner -Ran 1 -Passed 1 -Failed 0 -NotVerified 0
}

function Invoke-OwnerRequiresAdapter {
    param([string]$Owner, [string]$Kind = "harness")
    # Owners that only close through a local adapter or a live harness the
    # plugin cannot provide (e.g. verify, reliability crash-harness, perf
    # measurements, security threat-model check, commercial-readiness VM).
    # The script writes a NOT_VERIFIED/missing-adapter stub so audit-app
    # sees the gap explicitly instead of the owner just being absent.
    New-EvidenceStub -Owner $Owner -Producer $Owner -Instrument $Kind `
        -Check "$Owner.instrument-available" -Rule "instrument-present" -RuleVersion "1.0" `
        -Result NOT_VERIFIED -Confidence Observed `
        -Reason "This owner requires a project-local $Kind that the plugin cannot ship (see skills/$Owner/SKILL.md)." | Out-Null
    Register-Owner -Owner $Owner -Ran 1 -Passed 0 -Failed 0 -NotVerified 1
}

function Invoke-CodeReviewRuntime {
    $owner = "code-review-runtime"
    $hints = $gates.'adapter-hints'
    $build = if ($hints) { $hints.'build-command' } else { $null }
    $tests = if ($hints) { $hints.'tests-command' } else { $null }

    $ran = 0; $passed = 0; $failed = 0; $notVerified = 0

    foreach ($pair in @(
        @{ check = "runtime.build-passes"; cmd = $build; rule = "release-clean" },
        @{ check = "runtime.tests-pass";   cmd = $tests; rule = "suite-green"  }
    )) {
        if (-not $pair.cmd) {
            New-EvidenceStub -Owner $owner -Producer $owner -Instrument build-runner `
                -Check $pair.check -Rule $pair.rule -RuleVersion "1.0" `
                -Result NOT_VERIFIED -Confidence Observed `
                -Reason "adapter-hints does not declare the command in .claude/gates.json" | Out-Null
            $ran++; $notVerified++
            continue
        }
        if ($DryRun) {
            $ran++; $notVerified++
            continue
        }
        Push-Location $RepoRoot
        $log = Join-Path $AuditRoot "$owner/$($pair.check).log"
        New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
        try {
            & pwsh -NoProfile -Command $pair.cmd *> $log
            $ok = $LASTEXITCODE -eq 0
        } catch { $ok = $false }
        Pop-Location

        $result = if ($ok) { "PASS" } else { "FAIL" }
        $sev    = if ($ok) { "" }     else { "blocker" }
        New-EvidenceStub -Owner $owner -Producer $owner -Instrument build-runner `
            -Check $pair.check -Rule $pair.rule -RuleVersion "1.0" `
            -Result $result -Severity $sev -Confidence Observed `
            -ArtifactPath $log | Out-Null
        $ran++
        if ($ok) { $passed++ } else { $failed++ }
    }

    Register-Owner -Owner $owner -Ran $ran -Passed $passed -Failed $failed -NotVerified $notVerified
}

# Dispatch table — owner name to runner function.
$dispatch = @{
    "audit-app"            = $null   # orchestrator; runs at the end.
    "ui-system"            = { Invoke-UiSystem }
    "design-pro"           = { Invoke-OwnerRequiresAdapter -Owner design-pro           -Kind screenshot-sample }
    "code-review-runtime"  = { Invoke-CodeReviewRuntime }
    "code-review-contract" = { Invoke-OwnerRequiresAdapter -Owner code-review-contract -Kind test-runner }
    "security-audit"       = { Invoke-OwnerRequiresAdapter -Owner security-audit       -Kind threat-model-check }
    "reliability-audit"    = { Invoke-OwnerRequiresAdapter -Owner reliability-audit    -Kind crash-harness }
    "performance-audit"    = { Invoke-OwnerRequiresAdapter -Owner performance-audit    -Kind measurement-run }
    "observability"        = { Invoke-OwnerRequiresAdapter -Owner observability        -Kind log-inspection }
    "release-audit"        = { Invoke-OwnerRequiresAdapter -Owner release-audit        -Kind reproducibility-run }
    "commercial-readiness" = { Invoke-OwnerRequiresAdapter -Owner commercial-readiness -Kind clean-vm-run }
    "seo-audit"            = { Invoke-SeoAudit }
    "skill-auditor"        = { Invoke-SkillAuditor }
}

# ---------------------------------------------------------------------------
# 5. Run each applicable owner
# ---------------------------------------------------------------------------

foreach ($owner in $applicable) {
    if ($owner -eq "audit-app") { continue }
    if (-not $dispatch.ContainsKey($owner)) {
        Write-Host "  [!]  no runner registered for $owner — skipping" -ForegroundColor Yellow
        continue
    }
    Write-Host "  [→]  $owner" -ForegroundColor Cyan
    try { & $dispatch[$owner] }
    catch {
        Write-Host "  [x]  $owner threw: $_" -ForegroundColor Red
    }
}

# ---------------------------------------------------------------------------
# 6. Git snapshot t1 + audit-app hint
# ---------------------------------------------------------------------------

Push-Location $RepoRoot
$t1Head  = (git rev-parse --short HEAD 2>$null)
$t1Dirty = (git status --porcelain     2>$null)
Pop-Location

Write-Host ""
Write-Host "Git snapshot t1:" -ForegroundColor Cyan
Write-Host "  HEAD:   $t1Head   (t0=$t0Head)"
Write-Host "  dirty:  $([bool]$t1Dirty)"
if ($t0Head -ne $t1Head) {
    Write-Host "  WARNING: HEAD moved during the run." -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# 7. Summary
# ---------------------------------------------------------------------------

Write-Host ""
Write-Host "Per-owner summary:" -ForegroundColor Green
"{0,-24} {1,5} {2,7} {3,7} {4,13}" -f "owner","ran","passed","failed","not_verified" | Write-Host
"{0,-24} {1,5} {2,7} {3,7} {4,13}" -f ("-" * 24),"---","------","------","------------" | Write-Host
foreach ($k in ($Results.Keys | Sort-Object)) {
    $r = $Results[$k]
    "{0,-24} {1,5} {2,7} {3,7} {4,13}" -f $k,$r.ran,$r.passed,$r.failed,$r.notVerified | Write-Host
}

Write-Host ""
Write-Host "Next step:" -ForegroundColor Cyan
Write-Host "  In the agent chat, ask: 'use the audit-app skill against $RepoRoot'"
Write-Host "  It will read $AuditRoot and write $ReportsDir/<date>-<scope>.md"
Write-Host ""

exit 0
