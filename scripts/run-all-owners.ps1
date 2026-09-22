#!/usr/bin/env pwsh
# run-all-owners.ps1 — production-quality-ready v2.0
#
# Runs the instruments the plugin can run for the owners declared in
# gates.json (.agents/ or .claude/), filtered by the project's `platform`,
# and writes `.audit/<owner>/<producer>--<check>.evidence.yaml`.
#
# Contract (CONTRACTS §4.6): this script writes `result: PASS` ONLY for a
# check it executed, and every PASS carries `command:` and `log:` pointing
# at the captured output. Anything it cannot run is written as
# `NOT_VERIFIED / missing-instrument` with the reason — the gap is declared,
# never filled. It never templates a pass and never counts a "pass" it did
# not observe.
#
# Runs outside the model (CI or by hand). audit-app reads what it wrote.
#
# Usage:
#   pwsh scripts/run-all-owners.ps1 -RepoRoot .
#   pwsh scripts/run-all-owners.ps1 -RepoRoot . -Only ui-system,code-review
#   pwsh scripts/run-all-owners.ps1 -RepoRoot . -Skip commercial-readiness
#   pwsh scripts/run-all-owners.ps1 -RepoRoot . -DryRun
#   pwsh scripts/run-all-owners.ps1 -RepoRoot . -WebsiteUrl https://example.com
#
# Requires PowerShell 7+, git, Python 3, Node 18+. Installs nothing.

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

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# -Only a,b arrives as one string when invoked via `pwsh -File` from another shell.
$Only = @($Only | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$Skip = @($Skip | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })

$PythonExe = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } elseif (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { "py" }
$NodeExe   = if (Get-Command node -ErrorAction SilentlyContinue) { "node" } else { $null }

# ---------------------------------------------------------------- 0. paths

$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
if (-not $PluginRoot) { $PluginRoot = Split-Path -Parent $PSScriptRoot }
$PluginRoot = (Resolve-Path -LiteralPath $PluginRoot).Path

$GatesPath = $null
foreach ($rel in @(".agents/gates.json", ".claude/gates.json")) {
    $p = Join-Path $RepoRoot $rel
    if (Test-Path $p) { $GatesPath = $p; break }
}
$AuditRoot  = Join-Path $RepoRoot ".audit"
$ReportsDir = Join-Path $RepoRoot "docs/auditorias"

Write-Host "run-all-owners.ps1 (v2.0)" -ForegroundColor Cyan
Write-Host "  repo:   $RepoRoot"
Write-Host "  plugin: $PluginRoot"
Write-Host "  gates:  $GatesPath"

if (-not $GatesPath) {
    Write-Host "gates.json missing (.agents/gates.json or .claude/gates.json). Run bootstrap-project first." -ForegroundColor Red
    exit 2
}
$gates = Get-Content -Raw -LiteralPath $GatesPath | ConvertFrom-Json
if (-not $gates.owners) { Write-Host "gates.json has no 'owners' block." -ForegroundColor Red; exit 2 }

$Platform = if ($gates.PSObject.Properties['platform']) { [string]$gates.platform } else { "" }
if (-not $Platform) {
    Write-Host "gates.json has no 'platform' (web | desktop | both). Required by CONTRACTS §5.4." -ForegroundColor Red
    exit 2
}
Write-Host "  platform: $Platform"
Write-Host ""

# ---------------------------------------------------- 1. owner manifests

function Read-OwnerPlatforms {
    param([string]$Owner)
    $f = Join-Path $PluginRoot "skills/$Owner/instruments.yaml"
    if (-not (Test-Path $f)) { return @("web", "desktop") }
    $m = Select-String -LiteralPath $f -Pattern '^platforms:\s*\[([^\]]*)\]' | Select-Object -First 1
    if (-not $m) { return @("web", "desktop") }
    return ($m.Matches[0].Groups[1].Value -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

function Test-PlatformApplies {
    param([string[]]$OwnerPlatforms)
    if ($Platform -eq "both") { return $true }
    return $OwnerPlatforms -contains $Platform
}

$applicable = @()
foreach ($prop in $gates.owners.PSObject.Properties) {
    $name = $prop.Name; $cfg = $prop.Value
    if ($cfg -and $cfg.PSObject.Properties['not-applicable']) {
        Write-Host "  [skip] $name — not-applicable: $($cfg.'not-applicable')" -ForegroundColor DarkGray; continue
    }
    if (-not (Test-Path (Join-Path $PluginRoot "skills/$name"))) {
        Write-Host "  [!!]  $name declared in gates.json but not in the plugin — owner-undeclared" -ForegroundColor Yellow; continue
    }
    $plats = Read-OwnerPlatforms $name
    if (-not (Test-PlatformApplies $plats)) {
        Write-Host "  [skip] $name — platforms [$($plats -join ', ')] do not include '$Platform'" -ForegroundColor DarkGray; continue
    }
    if ($Only.Count -gt 0 -and $Only -notcontains $name) { continue }
    if ($Skip -contains $name) { continue }
    $applicable += $name
}
if ($applicable.Count -eq 0) { Write-Host "No applicable owners after filtering." -ForegroundColor Yellow; exit 1 }

Write-Host "Applicable owners ($($applicable.Count)):" -ForegroundColor Green
$applicable | ForEach-Object { Write-Host "  - $_" }
Write-Host ""

# ---------------------------------------------------------- 2. git t0

Push-Location $RepoRoot
$t0Head  = (git rev-parse --short HEAD 2>$null)
$t0Dirty = (git status --porcelain 2>$null)
Pop-Location
Write-Host "Git t0: HEAD=$t0Head dirty=$([bool]$t0Dirty)`n" -ForegroundColor Cyan

# --------------------------------------------------- 3. evidence writer

function Write-Evidence {
    param(
        [Parameter(Mandatory)][string]$Owner,
        [Parameter(Mandatory)][string]$Producer,
        [Parameter(Mandatory)][string]$Instrument,
        [Parameter(Mandatory)][string]$Check,
        [Parameter(Mandatory)][string]$Rule,
        [string]$RuleVersion = "1.0",
        [Parameter(Mandatory)][ValidateSet("PASS","FAIL","NOT_VERIFIED","NOT_APPLICABLE")][string]$Result,
        [string]$Severity = "",
        [string]$Command = "",
        [string]$Log = "",
        [string]$Reason = "",
        [string[]]$EvidenceLines = @()
    )
    if ($Result -eq "PASS" -and (-not $Command -or -not $Log)) {
        throw "Write-Evidence: refusing to write PASS for $Owner::$Check without command+log (CONTRACTS §4.6)"
    }
    if ($Result -eq "PASS" -and -not (Test-Path (Join-Path $RepoRoot $Log))) {
        throw "Write-Evidence: refusing to write PASS for $Owner::$Check — log not on disk: $Log"
    }
    $confidence = if ($Command -and $Log) { "OBSERVED" } elseif ($Result -eq "FAIL") { "INFERRED" } else { "UNKNOWN" }
    if ($DryRun) { Write-Host "       [dry-run] would write $Owner::$Check = $Result" -ForegroundColor DarkGray; return $null }

    $dir = Join-Path $AuditRoot $Owner
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $file = Join-Path $dir "$Producer--$Check.evidence.yaml"
    $now = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

    $sb = [System.Text.StringBuilder]::new()
    [void]$sb.AppendLine("check: $Check")
    [void]$sb.AppendLine("owner: $Owner")
    [void]$sb.AppendLine("producer: $Producer")
    [void]$sb.AppendLine("instrument: $Instrument")
    [void]$sb.AppendLine("rule: $Rule")
    [void]$sb.AppendLine("rule-version: `"$RuleVersion`"")
    [void]$sb.AppendLine("evidence-schema: 1.3.0")
    [void]$sb.AppendLine("methods:")
    [void]$sb.AppendLine("  - $Instrument")
    if ($EvidenceLines.Count -gt 0) {
        [void]$sb.AppendLine("evidence:")
        foreach ($e in $EvidenceLines) {
            $one = ($e -replace "[`r`n]+", " ") -replace '"', "'"
            if ($one.Length -gt 200) { $one = $one.Substring(0, 200) + "..." }
            [void]$sb.AppendLine("  - path: `"$one`"")
            [void]$sb.AppendLine("    kind: command-output")
        }
    } elseif ($Log) {
        [void]$sb.AppendLine("evidence:")
        [void]$sb.AppendLine("  - path: $Log")
        [void]$sb.AppendLine("    kind: command-output")
    } else {
        [void]$sb.AppendLine("evidence: []")
    }
    [void]$sb.AppendLine("result: $Result")
    if ($Severity) { [void]$sb.AppendLine("severity: $Severity") }
    [void]$sb.AppendLine("confidence: $confidence")
    if ($Command) {
        $cmdOut = ($Command -replace '\\', '/') -replace '"', "'"
        [void]$sb.AppendLine("command: `"$cmdOut`"")
    }
    if ($Log)     { [void]$sb.AppendLine("log: $Log") }
    if ($Reason)  { [void]$sb.AppendLine("reason: |"); ($Reason -split "`n") | ForEach-Object { [void]$sb.AppendLine("  $_") } }
    [void]$sb.AppendLine("context:")
    [void]$sb.AppendLine("  head: $t0Head")
    [void]$sb.AppendLine("  platform: $Platform")
    [void]$sb.AppendLine("  captured-at: $now")
    [void]$sb.AppendLine("  producer-script: scripts/run-all-owners.ps1@2.0.0")

    Set-Content -LiteralPath $file -Value $sb.ToString() -Encoding UTF8 -NoNewline
    return $file
}

function Invoke-Logged {
    # Runs a shell command in the repo root, captures output to $LogRel, returns $true on exit 0.
    param([string]$Cmd, [string]$LogRel)
    $logAbs = Join-Path $RepoRoot $LogRel
    if ($DryRun) { Write-Host "       [dry-run] $Cmd  -> $LogRel" -ForegroundColor DarkGray; return $null }
    New-Item -ItemType Directory -Force -Path (Split-Path $logAbs) | Out-Null
    Push-Location $RepoRoot
    try {
        & pwsh -NoProfile -Command $Cmd *> $logAbs
        $ok = ($LASTEXITCODE -eq 0)
    } catch { $ok = $false; Add-Content -LiteralPath $logAbs -Value "`n[runner] exception: $_" }
    Pop-Location
    return $ok
}

function Invoke-JsonInstrument {
    <#
      Runs a Python instrument that prints {results:[{check,result,severity,reason,evidence}]}
      on stdout, and turns every result into an evidence file. The instrument's
      own stdout is the log, so every PASS carries command + log (CONTRACTS §4.6).
      Returns @{ran;passed;failed;notVerified} or $null in dry-run / on failure.
    #>
    param(
        [Parameter(Mandatory)][string]$Owner,
        [Parameter(Mandatory)][string]$Script,      # absolute path
        [Parameter(Mandatory)][string]$Instrument,  # id declared in instruments.yaml
        [string]$Rule = "declared-by-owner",
        [string]$RuleVersion = "1.0",
        [string[]]$ExtraArgs = @()
    )
    if (-not (Test-Path $Script)) {
        Write-MissingInstrument $Owner $Instrument "instrument not found at $Script"
        return $null
    }
    $logRel  = ".audit/$Owner/$Instrument.log"
    $jsonRel = ".audit/$Owner/$Instrument.json"
    $argLine = ($ExtraArgs | ForEach-Object { $_ }) -join ' '
    $cmd = "$PythonExe `"$Script`" --repo `"$RepoRoot`" $argLine"
    if ($DryRun) { Write-Host "       [dry-run] $cmd" -ForegroundColor DarkGray; return $null }

    New-Item -ItemType Directory -Force -Path (Join-Path $AuditRoot $Owner) | Out-Null
    Push-Location $RepoRoot
    try {
        $stdout = & pwsh -NoProfile -Command "$cmd 2> `"$(Join-Path $RepoRoot $logRel)`""
    } catch {
        $stdout = $null
        Add-Content -LiteralPath (Join-Path $RepoRoot $logRel) -Value "[runner] exception: $_"
    }
    Pop-Location
    if (-not $stdout) {
        Write-MissingInstrument $Owner $Instrument "instrument produced no output (see $logRel)"
        return $null
    }
    Set-Content -LiteralPath (Join-Path $RepoRoot $jsonRel) -Value ($stdout -join "`n") -Encoding UTF8
    try { $report = ($stdout -join "`n") | ConvertFrom-Json } catch {
        Write-MissingInstrument $Owner $Instrument "instrument output is not valid JSON (see $jsonRel)"
        return $null
    }

    $ran = 0; $passed = 0; $failed = 0; $nv = 0
    foreach ($r in $report.results) {
        $ev = @()
        if ($r.PSObject.Properties['evidence'] -and $r.evidence) { $ev = @($r.evidence) }
        $sev = if ($r.PSObject.Properties['severity']) { [string]$r.severity } else { "" }
        $params = @{
            Owner = $Owner; Producer = $Owner; Instrument = $Instrument
            Check = [string]$r.check; Rule = $Rule; RuleVersion = $RuleVersion
            Result = [string]$r.result; Reason = [string]$r.reason; EvidenceLines = $ev
        }
        if ($sev) { $params.Severity = $sev }
        # Only a result the instrument actually observed carries the trace.
        if ($r.result -eq 'PASS' -or $r.result -eq 'FAIL') { $params.Command = $cmd; $params.Log = $logRel }
        Write-Evidence @params | Out-Null
        $ran++
        switch ([string]$r.result) {
            'PASS' { $passed++ }
            'FAIL' { $failed++ }
            default { $nv++ }
        }
    }
    Register-Owner -Owner $Owner -Ran $ran -Passed $passed -Failed $failed -NotVerified $nv
    return @{ ran = $ran; passed = $passed; failed = $failed; notVerified = $nv }
}

$Results = @{}
function Register-Owner { param([string]$Owner, [int]$Ran, [int]$Passed, [int]$Failed, [int]$NotVerified)
    $Results[$Owner] = @{ ran=$Ran; passed=$Passed; failed=$Failed; notVerified=$NotVerified } }

function Write-MissingInstrument {
    param([string]$Owner, [string]$Instrument, [string]$Why)
    Write-Evidence -Owner $Owner -Producer $Owner -Instrument $Instrument `
        -Check "$Owner.instrument-available" -Rule "instrument-present" -Result NOT_VERIFIED `
        -Reason "missing-instrument: $Why" | Out-Null
    Register-Owner -Owner $Owner -Ran 1 -Passed 0 -Failed 0 -NotVerified 1
}

# -------------------------------------------------------- 4. runners

function Invoke-CodeReview {
    $owner = "code-review"
    $hints = $gates.'adapter-hints'
    $pairs = @(
        @{ check="runtime.build-passes"; key="build-command";     instrument="build-runner"; rule="release-clean" },
        @{ check="runtime.types-check";  key="typecheck-command"; instrument="build-runner"; rule="typecheck-clean" },
        @{ check="runtime.tests-pass";   key="tests-command";     instrument="test-runner";  rule="suite-green" }
    )
    $ran=0; $passed=0; $failed=0; $nv=0
    foreach ($p in $pairs) {
        $cmd = if ($hints -and $hints.PSObject.Properties[$p.key]) { [string]$hints.($p.key) } else { "" }
        if (-not $cmd) {
            Write-Evidence -Owner $owner -Producer $owner -Instrument $p.instrument -Check $p.check -Rule $p.rule `
                -Result NOT_VERIFIED -Reason "adapter-hints.$($p.key) not declared in gates.json" | Out-Null
            $ran++; $nv++; continue
        }
        $logRel = ".audit/$owner/$($p.check).log"
        $ok = Invoke-Logged -Cmd $cmd -LogRel $logRel
        if ($null -eq $ok) { $ran++; $nv++; continue }  # dry-run
        if ($ok) {
            Write-Evidence -Owner $owner -Producer $owner -Instrument $p.instrument -Check $p.check -Rule $p.rule `
                -Result PASS -Command $cmd -Log $logRel | Out-Null; $passed++
        } else {
            Write-Evidence -Owner $owner -Producer $owner -Instrument $p.instrument -Check $p.check -Rule $p.rule `
                -Result FAIL -Severity BLOCKER -Command $cmd -Log $logRel | Out-Null; $failed++
        }
        $ran++
    }
    # Checks that need a human/agent reading of the diff or tests are declared, not faked.
    foreach ($c in @("runtime.tests-have-oracles","runtime.concurrency-safe","runtime.no-silent-panics","runtime.cancellation-cleaned",
                     "contract.timeout-declared","contract.retry-idempotent","contract.schema-compat","contract.failure-modes-declared",
                     "contract.input-not-trusted","contract.side-effects-bounded","contract.cancellation-honoured","contract.layer-direction",
                     "perf.budgets-declared","perf.bundle-within-budget","perf.hot-path-met","perf.no-regressions")) {
        Write-Evidence -Owner $owner -Producer $owner -Instrument static-analysis -Check $c -Rule "declared-by-owner" `
            -Result NOT_VERIFIED -Reason "missing-instrument: requires the code-review owner to run its review against the diff and cite the test that proves it; this runner only executes build/typecheck/tests." | Out-Null
        $ran++; $nv++
    }
    Register-Owner -Owner $owner -Ran $ran -Passed $passed -Failed $failed -NotVerified $nv
}

function Invoke-UiSystem {
    $owner = "ui-system"
    $script = Join-Path $PluginRoot "skills/ui-system/scripts/audit_ui.py"
    $cfg    = Join-Path $RepoRoot "ui.config.json"
    if (-not (Test-Path $script)) { Write-MissingInstrument $owner "audit_ui.py" "audit_ui.py not found at $script"; return }
    if (-not (Test-Path $cfg))    { Write-MissingInstrument $owner "audit_ui.py" "ui.config.json not present at repo root — instrument has no target"; return }

    $jsonRel = ".audit/$owner/audit_ui.json"; $mdRel = ".audit/$owner/audit_ui.md"; $logRel = ".audit/$owner/audit_ui.log"
    $cmd = "$PythonExe `"$script`" --repo `"$RepoRoot`" --config `"$cfg`" --json-output `"$(Join-Path $RepoRoot $jsonRel)`" --markdown-output `"$(Join-Path $RepoRoot $mdRel)`""
    # owners.ui-system.ignore-dirs: folders that are not UI (e.g. a server
    # inside a desktop repo); without it their findings fail the owner.
    $uiCfg = $gates.owners.PSObject.Properties['ui-system']
    if ($uiCfg -and $uiCfg.Value -and $uiCfg.Value.PSObject.Properties['ignore-dirs']) {
        foreach ($d in @($uiCfg.Value.'ignore-dirs')) { if ($d) { $cmd += " --ignore-dir `"$d`"" } }
    }
    $ok = Invoke-Logged -Cmd $cmd -LogRel $logRel
    if ($null -eq $ok) { Register-Owner -Owner $owner -Ran 0 -Passed 0 -Failed 0 -NotVerified 0; return }
    $jsonAbs = Join-Path $RepoRoot $jsonRel
    if (-not (Test-Path $jsonAbs)) { Write-MissingInstrument $owner "audit_ui.py" "audit_ui.py produced no JSON (see $logRel)"; return }
    $report = Get-Content -Raw -LiteralPath $jsonAbs | ConvertFrom-Json

    # finding kind -> canonical check (ui-system/SKILL.md §6)
    $map = [ordered]@{
        "ui.architectural-boundary"   = @("external-ui-import")
        "ui.legacy-package"           = @("legacy-ui-alias")
        "ui.invalid-boolean-selector" = @("boolean-state-selector")
        "ui.color-mix-sum"            = @("color-mix-sum")
        "ui.oklch-delta-l"            = @("oklch-contrast-low","raw-hex","raw-color-function","arbitrary-color-utility")
        "ui.remote-fonts"             = @("remote-resource")
        "ui.ai-generic-fonts"         = @("generic-font")
        "ui.focus-ring"               = @("focus-box-shadow")
        "ui.reduced-motion"           = @("missing-reduced-motion")
        "ui.unstyled-component"       = @("unstyled-component")
    }
    $ran=0; $passed=0; $failed=0
    foreach ($check in $map.Keys) {
        $kinds = $map[$check]
        $hits = @($report.findings | Where-Object { $kinds -contains $_.kind })
        $errs = @($hits | Where-Object { $_.severity -eq "error" })
        if ($errs.Count -gt 0) {
            $lines = @($errs | Select-Object -First 5 | ForEach-Object { "$($_.file):$($_.line) [$($_.kind)] $($_.value)" })
            Write-Evidence -Owner $owner -Producer $owner -Instrument audit_ui.py -Check $check -Rule "data-ui-contract" `
                -Result FAIL -Severity HIGH -Command $cmd -Log $logRel -EvidenceLines $lines `
                -Reason "$($errs.Count) error finding(s) of kind [$($kinds -join ', ')]; full list in $mdRel" | Out-Null
            $failed++
        } else {
            Write-Evidence -Owner $owner -Producer $owner -Instrument audit_ui.py -Check $check -Rule "data-ui-contract" `
                -Result PASS -Command $cmd -Log $logRel -EvidenceLines @($jsonRel) `
                -Reason "0 error findings of kind [$($kinds -join ', ')] across $($report.files_scanned) files" | Out-Null
            $passed++
        }
        $ran++
    }
    Register-Owner -Owner $owner -Ran $ran -Passed $passed -Failed $failed -NotVerified 0
}

function Invoke-AuditWebsite {
    $owner = "audit-website"
    $engine = Join-Path $PluginRoot "skills/audit-website/scripts/run_website_audit.mjs"
    $seo    = Join-Path $PluginRoot "skills/audit-website/seo/run_seo_audit.mjs"
    if (-not $NodeExe) { Write-MissingInstrument $owner "run_website_audit.mjs" "node not on PATH"; return }
    if (-not (Test-Path $engine)) { Write-MissingInstrument $owner "run_website_audit.mjs" "engine not found at $engine"; return }
    $target = if ($WebsiteUrl) { "--url=$WebsiteUrl" } elseif ($WebsiteDir) { "--dir=$WebsiteDir" } else { "" }
    if (-not $target) {
        Write-MissingInstrument $owner "run_website_audit.mjs" "no target: pass -WebsiteUrl <https://...> or -WebsiteDir <dist>"; return
    }
    $ran=0; $passed=0; $failed=0; $nv=0
    foreach ($e in @(@{ name="run_website_audit.mjs"; path=$engine; check="web.readiness-clean" },
                     @{ name="run_seo_audit.mjs";     path=$seo;    check="web.seo-technical" })) {
        if (-not (Test-Path $e.path)) { $nv++; $ran++; continue }
        $logRel = ".audit/$owner/$($e.name).log"
        $cmd = if ($e.name -eq "run_seo_audit.mjs") { "$NodeExe `"$($e.path)`" $target --out-dir=`"$(Join-Path $AuditRoot $owner)`"" } else { "$NodeExe `"$($e.path)`" $target" }
        $ok = Invoke-Logged -Cmd $cmd -LogRel $logRel
        if ($null -eq $ok) { $ran++; $nv++; continue }
        if ($ok) { Write-Evidence -Owner $owner -Producer $owner -Instrument $e.name -Check $e.check -Rule "sarif-2.1.0" -RuleVersion "sarif-2.1.0" -Result PASS -Command $cmd -Log $logRel | Out-Null; $passed++ }
        else     { Write-Evidence -Owner $owner -Producer $owner -Instrument $e.name -Check $e.check -Rule "sarif-2.1.0" -RuleVersion "sarif-2.1.0" -Result FAIL -Severity HIGH -Command $cmd -Log $logRel -Reason "engine exited non-zero; see log and SARIF" | Out-Null; $failed++ }
        $ran++
    }
    Register-Owner -Owner $owner -Ran $ran -Passed $passed -Failed $failed -NotVerified $nv
}

function Invoke-SecurityAudit {
    $owner = "security-audit"
    $ran=0; $passed=0; $failed=0; $nv=0
    # dep-scanner by stack detection
    $depCmd = ""
    if (Test-Path (Join-Path $RepoRoot "package-lock.json")) { $depCmd = "npm audit --audit-level=high" }
    elseif (Test-Path (Join-Path $RepoRoot "Cargo.lock")) { if (Get-Command cargo-audit -ErrorAction SilentlyContinue) { $depCmd = "cargo audit" } }
    if ($depCmd) {
        $logRel = ".audit/$owner/sec.deps-no-cve.log"
        $ok = Invoke-Logged -Cmd $depCmd -LogRel $logRel
        if ($null -ne $ok) {
            if ($ok) { Write-Evidence -Owner $owner -Producer $owner -Instrument dep-scanner -Check "sec.deps-no-cve" -Rule "owasp-asvs-5.0 V10" -RuleVersion "owasp-asvs-5.0" -Result PASS -Command $depCmd -Log $logRel | Out-Null; $passed++ }
            else     { Write-Evidence -Owner $owner -Producer $owner -Instrument dep-scanner -Check "sec.deps-no-cve" -Rule "owasp-asvs-5.0 V10" -RuleVersion "owasp-asvs-5.0" -Result FAIL -Severity HIGH -Command $depCmd -Log $logRel | Out-Null; $failed++ }
        } else { $nv++ }
        $ran++
    } else {
        Write-Evidence -Owner $owner -Producer $owner -Instrument dep-scanner -Check "sec.deps-no-cve" -Rule "owasp-asvs-5.0 V10" -RuleVersion "owasp-asvs-5.0" -Result NOT_VERIFIED -Reason "missing-instrument: no lockfile-based scanner available (npm audit / cargo audit)" | Out-Null
        $ran++; $nv++
    }
    # secret-scanner: secret_scan.py prefers the gitleaks report CI leaves in
    # .audit/ (only if its .head sidecar matches HEAD), then gitleaks on PATH,
    # then its built-in ruleset. The verdict names the engine it used.
    $glArgs = @()
    $glReport = Join-Path $AuditRoot "gitleaks-report.json"
    if (Test-Path $glReport) { $glArgs = @("--gitleaks-report", "`"$glReport`"") }
    $sec = Invoke-JsonInstrument -Owner $owner -Instrument secret-scanner `
        -Script (Join-Path $PluginRoot "skills/security-audit/scripts/secret_scan.py") `
        -Rule "owasp-asvs-5.0 V14" -RuleVersion "owasp-asvs-5.0" -ExtraArgs $glArgs
    if ($sec) { $ran += $sec.ran; $passed += $sec.passed; $failed += $sec.failed; $nv += $sec.notVerified }
    # threat model presence (file exists = declared; content is the owner's call)
    $tm = @("docs/threat-model.md","THREAT_MODEL.md","docs/seguranca/threat-model.md") | Where-Object { Test-Path (Join-Path $RepoRoot $_) } | Select-Object -First 1
    if ($tm) {
        $logRel = ".audit/$owner/sec.threat-model-declared.log"
        $cmd = "git log -1 --format=%H -- $tm"
        $ok = Invoke-Logged -Cmd $cmd -LogRel $logRel
        $hash = ""
        if ($ok) { $raw = Get-Content -LiteralPath (Join-Path $RepoRoot $logRel) -Raw -ErrorAction SilentlyContinue; if ($raw) { $hash = ([string]$raw).Trim() } }
        if ($null -eq $ok) { $nv++ }
        elseif ($hash -match '^[0-9a-f]{40}$') {
            Write-Evidence -Owner $owner -Producer $owner -Instrument threat-model-check -Check "sec.threat-model-declared" -Rule "owasp-asvs-5.0 V1" -RuleVersion "owasp-asvs-5.0" -Result PASS -Command $cmd -Log $logRel -EvidenceLines @("$tm@$($hash.Substring(0,12))") | Out-Null; $passed++
        } else {
            # file exists but is not committed: the contract says "versioned file, referenced by commit hash"
            Write-Evidence -Owner $owner -Producer $owner -Instrument threat-model-check -Check "sec.threat-model-declared" -Rule "owasp-asvs-5.0 V1" -RuleVersion "owasp-asvs-5.0" -Result FAIL -Severity MEDIUM -Command $cmd -Log $logRel -Reason "$tm exists but has no commit yet (uncommitted); the threat model must be versioned" | Out-Null; $failed++
        }
    } else {
        Write-Evidence -Owner $owner -Producer $owner -Instrument threat-model-check -Check "sec.threat-model-declared" -Rule "owasp-asvs-5.0 V1" -RuleVersion "owasp-asvs-5.0" -Result FAIL -Severity HIGH -Reason "no threat model file found (docs/threat-model.md or THREAT_MODEL.md)" | Out-Null; $failed++
    }
    $ran++
    Register-Owner -Owner $owner -Ran $ran -Passed $passed -Failed $failed -NotVerified $nv
}

function Invoke-ReleaseAudit {
    $owner = "release-audit"
    $ran=0; $passed=0; $failed=0; $nv=0
    # lockfile present
    $lock = @("package-lock.json","pnpm-lock.yaml","yarn.lock","Cargo.lock") | Where-Object { Test-Path (Join-Path $RepoRoot $_) } | Select-Object -First 1
    if ($lock) {
        $logRel = ".audit/$owner/release.lockfiles-immutable.log"
        $cmd = "git ls-files --error-unmatch $lock"
        $ok = Invoke-Logged -Cmd $cmd -LogRel $logRel
        if ($null -ne $ok) {
            if ($ok) { Write-Evidence -Owner $owner -Producer $owner -Instrument reproducibility-run -Check "release.lockfiles-immutable" -Rule "lockfile-committed" -Result PASS -Command $cmd -Log $logRel -EvidenceLines @($lock) -Reason "lockfile tracked by git; CI must install frozen (checked by ci-inspection)" | Out-Null; $passed++ }
            else     { Write-Evidence -Owner $owner -Producer $owner -Instrument reproducibility-run -Check "release.lockfiles-immutable" -Rule "lockfile-committed" -Result FAIL -Severity HIGH -Command $cmd -Log $logRel | Out-Null; $failed++ }
        } else { $nv++ }
    } else {
        Write-Evidence -Owner $owner -Producer $owner -Instrument reproducibility-run -Check "release.lockfiles-immutable" -Rule "lockfile-committed" -Result FAIL -Severity HIGH -Reason "no lockfile found" | Out-Null; $failed++
    }
    $ran++
    # sbom
    $sbom = Join-Path $RepoRoot "sbom.json"
    if (Test-Path $sbom) {
        $logRel = ".audit/$owner/release.sbom-present.log"
        $cmd = "$NodeExe -e `"const s=require('./sbom.json');const p=require('./package.json');if((s.metadata||{}).component&&s.metadata.component.version!==p.version){console.error('SBOM version '+s.metadata.component.version+' != package '+p.version);process.exit(1)}console.log('sbom ok '+p.version)`""
        if ($NodeExe -and (Test-Path (Join-Path $RepoRoot "package.json"))) {
            $ok = Invoke-Logged -Cmd $cmd -LogRel $logRel
            if ($null -ne $ok) {
                if ($ok) { Write-Evidence -Owner $owner -Producer $owner -Instrument sbom-verifier -Check "release.sbom-present" -Rule "cyclonedx-synced" -Result PASS -Command $cmd -Log $logRel -EvidenceLines @("sbom.json") | Out-Null; $passed++ }
                else     { Write-Evidence -Owner $owner -Producer $owner -Instrument sbom-verifier -Check "release.sbom-present" -Rule "cyclonedx-synced" -Result FAIL -Severity MEDIUM -Command $cmd -Log $logRel | Out-Null; $failed++ }
            } else { $nv++ }
        } else {
            Write-Evidence -Owner $owner -Producer $owner -Instrument sbom-verifier -Check "release.sbom-present" -Rule "cyclonedx-synced" -Result NOT_VERIFIED -Reason "sbom.json exists but no node/package.json to verify version sync" | Out-Null; $nv++
        }
    } else {
        Write-Evidence -Owner $owner -Producer $owner -Instrument sbom-verifier -Check "release.sbom-present" -Rule "cyclonedx-synced" -Result FAIL -Severity MEDIUM -Reason "sbom.json not found at repo root" | Out-Null; $failed++
    }
    $ran++

    # ci-inspection: reads CI, manifests and git log to settle the release.* checks.
    $ci = Invoke-JsonInstrument -Owner $owner -Instrument ci-inspection `
        -Script (Join-Path $PluginRoot "skills/release-audit/scripts/ci_inspection.py") `
        -Rule "clean-clone-one-command" -ExtraArgs @("--platform", $Platform)
    if ($ci) { $ran += $ci.ran; $passed += $ci.passed; $failed += $ci.failed; $nv += $ci.notVerified }

    # Desktop-only distribution checks: declared here only when they apply.
    if ($Platform -ne "web") {
        foreach ($c in @("release.signed-artifact", "release.updater-verified")) {
            Write-Evidence -Owner $owner -Producer $owner -Instrument signature-verifier -Check $c -Rule "declared-by-owner" `
                -Result NOT_VERIFIED -Reason "missing-instrument: needs the signed installer/updater manifest and a verification run" | Out-Null
            $ran++; $nv++
        }
    }
    Register-Owner -Owner $owner -Ran $ran -Passed $passed -Failed $failed -NotVerified $nv
}

function Invoke-ReliabilityAudit {
    $owner = "reliability-audit"
    $ran=0; $passed=0; $failed=0; $nv=0

    # §1 persistence — migration harness replays the whole chain from empty.
    $mh = Invoke-JsonInstrument -Owner $owner -Instrument migration-harness `
        -Script (Join-Path $PluginRoot "skills/reliability-audit/scripts/migration_harness.py") `
        -Rule "no-data-loss"
    if ($mh) { $ran += $mh.ran; $passed += $mh.passed; $failed += $mh.failed; $nv += $mh.notVerified }

    # The project's own migration verifier settles migration-immutable only when
    # the harness did not run: both write the same evidence file, and one check
    # must not be counted twice.
    $hints = $gates.'adapter-hints'
    $mig = if ($hints -and $hints.PSObject.Properties['migrations-verify-command']) { [string]$hints.'migrations-verify-command' } else { "" }
    if ($mig -and -not $mh) {
        $logRel = ".audit/$owner/reliability.migration-immutable.log"
        $ok = Invoke-Logged -Cmd $mig -LogRel $logRel
        if ($null -ne $ok) {
            if ($ok) { Write-Evidence -Owner $owner -Producer $owner -Instrument migration-harness -Check "reliability.migration-immutable" -Rule "published-migrations-unchanged" -Result PASS -Command $mig -Log $logRel | Out-Null; $passed++ }
            else     { Write-Evidence -Owner $owner -Producer $owner -Instrument migration-harness -Check "reliability.migration-immutable" -Rule "published-migrations-unchanged" -Result FAIL -Severity BLOCKER -Command $mig -Log $logRel | Out-Null; $failed++ }
            $ran++
        }
    }

    # §2 diagnosability — static inspection of the logging surface.
    $li = Invoke-JsonInstrument -Owner $owner -Instrument log-inspection `
        -Script (Join-Path $PluginRoot "skills/reliability-audit/scripts/log_inspection.py") `
        -Rule "diagnosable-in-production" -ExtraArgs @("--platform", $Platform)
    if ($li) { $ran += $li.ran; $passed += $li.passed; $failed += $li.failed; $nv += $li.notVerified }

    # What still needs a project harness: atomicity under crash, resume.
    $gaps = @("reliability.atomic-write", "reliability.resume-after-reopen")
    if ($Platform -ne "web") { $gaps += @("reliability.crash-mid-write", "reliability.no-double-flush") }
    foreach ($c in $gaps) {
        $inst = if ($c -like "*crash*" -or $c -like "*flush*") { "crash-harness" } else { "migration-harness" }
        Write-Evidence -Owner $owner -Producer $owner -Instrument $inst -Check $c -Rule "declared-by-owner" `
            -Result NOT_VERIFIED -Reason "missing-instrument: requires a project-local $inst that kills the process mid-write (or races two concurrent writers) and reopens" | Out-Null
        $ran++; $nv++
    }
    Register-Owner -Owner $owner -Ran $ran -Passed $passed -Failed $failed -NotVerified $nv
}

function Invoke-DeclaredGap { param([string]$Owner, [string]$Instrument)
    Write-MissingInstrument $Owner $Instrument "requires a project-local $Instrument the plugin cannot ship (see skills/$Owner/SKILL.md)" }

$dispatch = @{
    "audit-app"            = $null
    "bootstrap-project"    = $null
    "start-work"           = $null
    "review-change"        = $null
    "close-work"           = $null
    "code-review"          = { Invoke-CodeReview }
    "ui-system"            = { Invoke-UiSystem }
    "audit-website"        = { Invoke-AuditWebsite }
    "security-audit"       = { Invoke-SecurityAudit }
    "release-audit"        = { Invoke-ReleaseAudit }
    "reliability-audit"    = { Invoke-ReliabilityAudit }
    "design-pro"           = { Invoke-DeclaredGap -Owner design-pro           -Instrument screenshot-sample }
    "verify"               = { Invoke-DeclaredGap -Owner verify               -Instrument adapter-local }
    "drive-app-window"     = { Invoke-DeclaredGap -Owner drive-app-window     -Instrument gui.ps1 }
    "commercial-readiness" = { Invoke-DeclaredGap -Owner commercial-readiness -Instrument billing-harness }
}

# ----------------------------------------------------------- 5. run

foreach ($owner in $applicable) {
    if (-not $dispatch.ContainsKey($owner)) { Write-Host "  [!]  no runner for $owner — skipping" -ForegroundColor Yellow; continue }
    if ($null -eq $dispatch[$owner]) { continue }
    Write-Host "  [->] $owner" -ForegroundColor Cyan
    # A check this run no longer writes (e.g. desktop-only on web) must not
    # survive from an earlier run and be read by audit-app as current.
    $ownerDir = Join-Path $AuditRoot $owner
    if (-not $DryRun -and (Test-Path $ownerDir)) { Remove-Item -LiteralPath $ownerDir -Recurse -Force }
    try { & $dispatch[$owner] } catch { Write-Host "  [x]  $owner threw: $_" -ForegroundColor Red }
}

# ------------------------------------------------- 6. validate + t1

Push-Location $RepoRoot
$t1Head = (git rev-parse --short HEAD 2>$null)
Pop-Location
if ($t0Head -ne $t1Head) { Write-Host "WARNING: HEAD moved during the run ($t0Head -> $t1Head)." -ForegroundColor Yellow }

$validator = Join-Path $PluginRoot "skills/audit-app/scripts/validate_evidence.py"
if ((Test-Path $validator) -and -not $DryRun) {
    Write-Host "`nvalidate_evidence.py:" -ForegroundColor Cyan
    & $PythonExe $validator --repo $RepoRoot --plugin $PluginRoot | Select-Object -Last 3 | ForEach-Object { Write-Host "  $_" }
}

Write-Host "`nPer-owner summary:" -ForegroundColor Green
"{0,-22} {1,5} {2,7} {3,7} {4,13}" -f "owner","ran","passed","failed","not_verified" | Write-Host
"{0,-22} {1,5} {2,7} {3,7} {4,13}" -f ("-"*22),"---","------","------","------------" | Write-Host
foreach ($k in ($Results.Keys | Sort-Object)) { $r=$Results[$k]; "{0,-22} {1,5} {2,7} {3,7} {4,13}" -f $k,$r.ran,$r.passed,$r.failed,$r.notVerified | Write-Host }

Write-Host "`nNext: ask the agent to run audit-app against $RepoRoot (reads $AuditRoot, writes $ReportsDir)." -ForegroundColor Cyan
exit 0
