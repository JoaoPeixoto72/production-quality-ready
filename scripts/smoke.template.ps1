# smoke.template.ps1 — o smoke da app, no formato que o owner `verify` espera.
#
# Copia para o projeto (ex.: `scripts/smoke.ps1`), ajusta a lista de verificações
# e declara em `.agents/gates.json`:
#
#   "adapter-hints": { "smoke-command": "pwsh -NoProfile -File scripts/smoke.ps1" }
#
# O contrato que este script tem de respeitar:
#   - correr contra o ambiente REAL (não contra um mock);
#   - imprimir uma linha por verificação, para o log dizer o que correu;
#   - sair != 0 quando qualquer verificação falha.
# Sem output, o instrumento devolve NOT_VERIFIED: um smoke silencioso não prova nada.

$ErrorActionPreference = "Continue"
$base = "https://SUBSTITUIR.example"
$fail = 0

function Check($name, $ok, $detail = "") {
    if (-not $ok) { $script:fail++ }
    "{0,-28} {1}  {2}" -f $name, $(if ($ok) { "OK" } else { "FALHA" }), $detail
}

# 1. as páginas públicas respondem 200
foreach ($p in @("/", "/precos", "/entrar")) {
    $code = curl.exe -s -o NUL -w "%{http_code}" "$base$p"
    Check "$p" ($code -eq "200") "GET $code"
}

# 2. o fluxo crítico completo (substituir pelo fluxo do produto)
#    $body = curl.exe -s -X POST "$base/api/..." -H "content-type: application/json" -d '{...}'
#    Check "checkout" ($body -match '"ok":true')

# 3. o id de correlação existe na resposta
$headers = curl.exe -s -D - -o NUL "$base/"
Check "x-request-id" (($headers -join "`n") -match "(?im)^x-request-id:") "cabecalho de correlacao"

# 4. o ambiente serve o artefacto esperado (não uma versão antiga)
#    $version = (curl.exe -s "$base/api/health" | ConvertFrom-Json).version
#    Check "versao" ($version -eq "X.Y.Z") "esperado X.Y.Z, servido $version"

""
"FALHAS: $fail"
exit $fail
