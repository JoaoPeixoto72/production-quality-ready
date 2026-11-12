# smoke.template.ps1 — the app's smoke test, in the format the `verify` owner expects.
#
# Copy it into the project (e.g. `scripts/smoke.ps1`), adjust the checks, and declare
# in `.agents/gates.json`:
#
#   "adapter-hints": { "smoke-command": "pwsh -NoProfile -File scripts/smoke.ps1" }
#
# Contract: run against the REAL environment (not a mock); print one line per check;
# exit != 0 when any check fails. No output is NOT_VERIFIED: a silent smoke proves nothing.

$ErrorActionPreference = "Continue"
$base = "https://REPLACE.example"
$fail = 0

function Check($name, $ok, $detail = "") {
    if (-not $ok) { $script:fail++ }
    "{0,-28} {1}  {2}" -f $name, $(if ($ok) { "OK" } else { "FAIL" }), $detail
}

# 1. public pages answer 200
foreach ($p in @("/", "/pricing", "/login")) {
    $code = curl.exe -s -o NUL -w "%{http_code}" "$base$p"
    Check "$p" ($code -eq "200") "GET $code"
}

# 2. the full critical flow (replace with the product's)
#    $body = curl.exe -s -X POST "$base/api/..." -H "content-type: application/json" -d '{...}'
#    Check "checkout" ($body -match '"ok":true')

# 3. the correlation id is in the response
$headers = curl.exe -s -D - -o NUL "$base/"
Check "x-request-id" (($headers -join "`n") -match "(?im)^x-request-id:") "correlation header"

# 4. the environment serves the expected artefact (not an old version)
#    $version = (curl.exe -s "$base/api/health" | ConvertFrom-Json).version
#    Check "version" ($version -eq "X.Y.Z") "expected X.Y.Z, served $version"

""
"FAILURES: $fail"
exit $fail
