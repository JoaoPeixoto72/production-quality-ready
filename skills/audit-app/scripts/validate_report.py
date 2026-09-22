#!/usr/bin/env python3
"""Validação estrutural de um relatório de auditoria.

Verifica só o que é decidível a olhar para o documento: tokens do vocabulário,
IDs que existem no registo, um estado por linha, contagens que batem certo com
a tabela, e a tabela de verdade do verdict. **Não** verifica se a evidência é
verdadeira, se uma justificação chega, se uma análise foi mesmo completa, ou se
um `NOT_APPLICABLE` está bem fundamentado — isso não se decide por parsing, e
dizer que sim seria o mesmo erro que este validador existe para apanhar.

A verificação que mais vale é a das contagens: o relatório de 2026-09-06 dizia
`PROVEN: 6` com vinte linhas `PROVEN` na tabela, e `PROVEN` é o estado que conta
defeitos — um resumo errado ali é um verdict errado.

Exit codes:
  0  estruturalmente válido
  1  problemas encontrados
  2  não foi possível analisar (não é um relatório, ou é de outro major)
 64  erro de utilização
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_PROBLEMS = 1
EXIT_CANNOT_ANALYSE = 2
EXIT_USAGE = 64

ESTADOS = {"PENDING", "PROVEN", "CLEARED", "UNPROVEN", "NOT_APPLICABLE"}
COBERTURA_METODO = {"COMPLETA", "PARCIAL", "AMOSTRA"}
TIPOS_EVIDENCIA = {"EXECUCAO", "TESTE", "MEDICAO", "ANALISE_ESTATICA",
                   "LEITURA", "DOCUMENTO", "FONTE_EXTERNA"}
VERDICTS_PRODUTO = {"PASS", "CONCERNS", "FAIL"}
VERDICTS_COBERTURA = {"COMPLETE", "PARTIAL", "BLOCKED"}
PRIORIDADES = {"P0", "P1", "P2", "P3"}

DESTINO = "docs/auditorias"

# As colunas de que as verificações dependem, cada uma com as grafias que se
# aceitam. O cabeçalho do `relatorio.md` tem ainda `Artefacto` e `Nota`, que
# nenhuma verificação lê — exigi-las seria recusar um relatório por causa de
# uma coluna que ninguém usa.
COLUNAS_USADAS = (("id",), ("estado",), ("gate",),
                  ("evidência", "evidencia"), ("cobertura",))


def contrato_actual() -> tuple[str | None, str | None]:
    """(version, hash) of the plugin's contract.

    The contract lives at the plugin root (`CONTRACTS.md`), not inside this
    skill (POLICY §1.1). The version comes from the
    `**Contract version**: X.Y.Z` line (or the legacy Portuguese
    `**Versão do contrato**: X.Y.Z`, still accepted for compatibility with
    older reports). The hash is SHA-256 of `CONTRACTS.md` itself, normalized
    to LF so it is reproducible across machines (Windows delivers CRLF; Git
    may vary between check-outs — the hash must prove the contract, not the
    machine).

    Walks up the folders until it finds `CONTRACTS.md`; returns
    `(None, None)` if the plugin is installed without a contract alongside
    (in that case the validator says so, doesn't guess).
    """
    import hashlib
    p = Path(__file__).resolve()
    for candidate in [p.parent.parent.parent.parent, p.parent.parent.parent, p.parent.parent]:
        contract_path = candidate / "CONTRACTS.md"
        if contract_path.is_file():
            raw = contract_path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            text = raw.decode("utf-8")
            m = re.search(r"^\*\*(?:Contract version|Vers[ãa]o do contrato)\*\*:\s*(\d+\.\d+\.\d+)\s*$", text, re.M)
            version = m.group(1) if m else None
            digest = hashlib.sha256(raw).hexdigest()
            return version, digest
    return None, None

# Um ID de obrigação: `SEC-01` (registo v1) ou `owner::check` (contrato v2).
RE_ID_OBRIGACAO = re.compile(r"[A-Z0-9]+-\d+|[a-z][a-z0-9-]*::[A-Za-z0-9._-]+")
RE_CANONICO_V2 = re.compile(r"^\|\s*`([a-z][a-z0-9-]*)`\s*\|\s*`([^`]+)`(?:\s*…\s*`([^`]+)`)?\s*\|", re.M)
RE_FOR_CHECKS = re.compile(r"^\s+-\s+([A-Za-z0-9._-]+)\s*$", re.M)
RE_VERSAO = re.compile(r"\*{0,2}Contrato\*{0,2}:\s*vers[ãa]o\s*(\d+)\.(\d+)\.(\d+)", re.I)
# O digest aparece nu (`SHA-256 66e9…`) ou entre crases, que é como o markdown
# de um relatório real o escreve. Exigir o primeiro fazia o validador dizer
# "sem SHA-256 do contrato" a um relatório que o tinha — a mesma validação de
# tipografia que o comentário do RE_VERDICT, aqui ao lado, proíbe.
RE_HASH = re.compile(r"SHA-256[\s:`*]*([0-9a-f]{64})", re.I)
RE_CONTAGEM = re.compile(
    r"`?PROVEN`?:\s*~?(\d+).*?`?CLEARED`?:\s*~?(\d+).*?"
    r"`?UNPROVEN`?:\s*~?(\d+).*?`?NOT_APPLICABLE`?:\s*~?(\d+)", re.S)
# O separador entre os dois eixos é `·` no formato, mas um relatório real
# aparece com `|` (tabela), `-` ou `–`. Aceitam-se todos: recusar um relatório
# por causa do carácter que separa duas palavras seria validar tipografia.
# O nome do módulo aceita maiúsculas e dígitos: sem elas o `Global:` da secção 1
# não casava — a linha mais importante do relatório passava sem ser lida — e um
# módulo futuro chamado `a11y` ou `i18n` desapareceria pela mesma porta.
RE_VERDICT = re.compile(
    r"^\|?\s*`?([A-Za-z][A-Za-z0-9\-]*)`?\s*[|:]\s*(?:Produto:\s*)?\*{0,2}(PASS|CONCERNS|FAIL)\*{0,2}"
    r"\s*[|·\-–]\s*(?:Cobertura:\s*)?\*{0,2}(COMPLETE|PARTIAL|BLOCKED)\*{0,2}"
    r"\s*(?:\((\d+)\s*/\s*(\d+)\))?", re.M)
RE_FINDING = re.compile(r"^###\s+\*{0,2}([A-Z0-9]+-F\d+)\*{0,2}\s*[—-]", re.M)
RE_ID_FINDING = re.compile(r"\b([A-Z0-9]+-F\d+)\b")
# A memória de que achados já existiram. O `evals-corridos.md` fica de fora de
# propósito: cita IDs para falar de uma colisão entre relatórios, não para os
# registar como achados — deixá-lo entrar seria dar por bom qualquer ID que
# alguma vez tivesse aparecido num exemplo.
BASELINES_COM_ACHADOS = ("achados-resolvidos.md", "riscos-aceites.md",
                         "ultima-auditoria.md")
# A data de um bloco de baseline: no título (`## 2026-09-09 — full`) ou no
# campo (`**Data de resolução**: 2026-09-08`).
RE_DATA = re.compile(r"^#{2,3} (\d{4}-\d{2}-\d{2})|\*\*Data(?: de resolução)?\*\*:\s*(\d{4}-\d{2}-\d{2})",
                     re.M)
RE_PRIORIDADE = re.compile(r"\*\*Prioridade\*\*:\s*\*{0,2}(P[0-3])\*{0,2}")
RE_AREA = re.compile(r"\*\*[ÁA]rea\*\*:\s*\*{0,2}`?([A-Za-z][A-Za-z0-9\-]*)`?")
RE_MODIFICADOR = re.compile(
    r"\b(PROVEN|CLEARED|UNPROVEN|NOT_APPLICABLE)\s*\(([^)]+)\)")


def registo_v2(raiz_plugin: Path) -> dict:
    """O registo de obrigações do contrato v2, lido do próprio plugin.

    Críticas: as linhas da §7.4 do `CONTRACTS.md` (`owner::check`). Um
    intervalo (`sell-01-…` … `sell-06-…`) expande-se pelos checks com o mesmo
    prefixo no `instruments.yaml` do owner. Não críticas: tudo o que um owner
    declara em `for-checks`, mais o `<owner>.instrument-available` que o runner
    escreve quando falta o instrumento.
    """
    registo: dict[str, dict] = {}
    skills = raiz_plugin / "skills"
    declarados: dict[str, list[str]] = {}
    for manifesto in sorted(skills.glob("*/instruments.yaml")):
        owner = manifesto.parent.name
        declarados[owner] = RE_FOR_CHECKS.findall(manifesto.read_text(encoding="utf-8"))
        for check in declarados[owner] + [f"{owner}.instrument-available"]:
            registo[f"{owner}::{check}"] = {"module": owner, "critical": False}

    contrato = (raiz_plugin / "CONTRACTS.md").read_text(encoding="utf-8")
    inicio = contrato.find("### 7.4")
    fim = contrato.find("\n### ", inicio + 1)
    for owner, primeiro, ultimo in RE_CANONICO_V2.findall(contrato[inicio:fim]):
        checks = [primeiro]
        if ultimo:
            prefixo = re.match(r"[a-z]+-", primeiro)
            checks = [c for c in declarados.get(owner, [])
                      if prefixo and c.startswith(prefixo.group(0))] or [primeiro, ultimo]
        for check in checks:
            registo[f"{owner}::{check}"] = {"module": owner, "critical": True}
    return registo


class _Parser(argparse.ArgumentParser):
    def error(self, message: str):
        self.print_usage(sys.stderr)
        print(f"erro: {message}", file=sys.stderr)
        raise SystemExit(EXIT_USAGE)


def celulas(resto: str) -> list[str]:
    """As células de uma linha de tabela, sem o ID (que já foi consumido)."""
    return [c.strip() for c in resto.rstrip("|").split("|")]


def limpar(token: str) -> str:
    return token.replace("*", "").replace("`", "").strip()


def achados_anteriores(raiz: Path, ate: str | None = None) -> set[str]:
    """Os IDs de achado que os baselines conheciam **antes** de `ate`.

    É a única memória que existe de que números estão tomados. Se estiver
    vazia, citar uma auditoria anterior dá erro — e isso é a pressão certa:
    os baselines existem para ser escritos, e a fase 0 lê-os.

    O `ate` é a data do relatório a validar, e sem ela a regra não tem noção de
    tempo: os achados de um relatório entram nos baselines **depois** de ele
    ser escrito, e uma auditoria seguinte pode reutilizar um ID dele como
    reincidência. Nos dois casos, contá-los faz o relatório ser acusado de
    copiar de si próprio ou do seu futuro — que foi o que aconteceu ao
    `2026-09-08-full.md` assim que o índice ganhou a entrada de 2026-09-09.

    Um bloco sem data não se consegue pôr no tempo, e **não conta**. Errar
    para o lado de não acusar é deliberado: um validador que acusa documentos
    correctos deixa de ser lido, e esta regra é de higiene, não de segurança.
    """
    vistos: set[str] = set()
    for nome in BASELINES_COM_ACHADOS:
        try:
            texto = (raiz / "baselines" / nome).read_text(encoding="utf-8")
        except OSError:
            continue
        for bloco in re.split(r"(?=^#{2,3} )", texto, flags=re.M):
            if ate is not None:
                m = RE_DATA.search(bloco)
                data = (m.group(1) or m.group(2)) if m else None
                if data is None or data >= ate:
                    continue
            vistos |= set(RE_ID_FINDING.findall(bloco))
    return vistos


RE_CERCA = re.compile(r"^```.*?^```", re.M | re.S)


def sem_blocos_de_codigo(texto: str) -> str:
    """O texto sem as cercas ```…```, com o número de linhas preservado.

    A fase 4 **obriga** o relatório a propor os blocos prontos a colar nos
    baselines, e esses blocos trazem títulos `### XXX-Fnn` e citam IDs. Lidos
    como se fossem do relatório, faziam-no declarar achados que não são dele:
    a 2026-09-09 um relatório que propunha fechar o `LEGAL-F03` era acusado de
    reutilizar esse número. Cumprir o contrato produzia um documento inválido,
    que é o defeito que este ficheiro já tinha tido duas vezes por outras vias.
    """
    return RE_CERCA.sub(lambda m: "\n" * m.group(0).count("\n"), texto)


def blocos_de_finding(texto: str):
    """`(id, bloco)` de cada `### XXX-Fnn — ...` até ao título seguinte."""
    titulos = [m.start() for m in re.finditer(r"^#{2,4}\s", texto, re.M)]
    for m in RE_FINDING.finditer(texto):
        seguintes = [t for t in titulos if t > m.start()]
        yield m.group(1), texto[m.start():seguintes[0] if seguintes else len(texto)]


def prioridades_por_modulo(texto: str) -> tuple[dict[str, set[str]], dict[str, str]]:
    """A prioridade de cada finding, atribuída ao módulo que ele declara.

    Devolve `(por_módulo, sem_área)`. É decidível porque o `relatorio.md` obriga
    cada finding a trazer `**Área**: <módulo>` — sem isso, um P1 em `compliance`
    obrigaria `FAIL` em `ui-ux`, que é o defeito que isto corrige.

    Um finding com prioridade e sem área não se atribui a ninguém: vai para o
    segundo dicionário, conta para o verdict global, e quem o lê é avisado. É a
    diferença entre não saber e fingir que sabe.
    """
    por_modulo: dict[str, set[str]] = {}
    sem_area: dict[str, str] = {}
    for fid, bloco in blocos_de_finding(texto):
        mp = RE_PRIORIDADE.search(bloco)
        if not mp:
            continue
        ma = RE_AREA.search(bloco)
        if ma:
            por_modulo.setdefault(limpar(ma.group(1)).lower(), set()).add(mp.group(1))
        else:
            sem_area[fid] = mp.group(1)
    return por_modulo, sem_area


def validar(texto: str, registo: dict, caminho: Path,
            hash_actual: str | None = None,
            anteriores: set[str] | None = None,
            conhecidos: set[str] | None = None) -> tuple[list[str], list[str]]:
    problemas: list[str] = []
    avisos: list[str] = []
    erro = problemas.append
    anteriores = anteriores or set()
    # Duas perguntas diferentes, e confundi-las dá falsos positivos nos dois
    # sentidos: «este ID existe?» aceita tudo o que os baselines conhecem,
    # incluindo uma auditoria do mesmo dia; «este ID já era de alguém antes
    # de mim?» só olha para o que é estritamente anterior.
    conhecidos = conhecidos if conhecidos is not None else anteriores

    # Destino. O relatório tem morada fixa porque é o que torna o índice
    # possível (ver SKILL.md, Modo read-only).
    partes = caminho.as_posix().split("/")
    if DESTINO.split("/")[-1] not in partes:
        avisos.append(f"fora de `{DESTINO}/` — o índice não o encontra pela morada")

    mh = RE_HASH.search(texto)
    if not mh:
        erro("sem `SHA-256` do contrato — a versão sozinha não identifica as regras")
    elif hash_actual and mh.group(1).lower() != hash_actual:
        # Aviso, não erro: dentro do mesmo major o contrato pode ter mudado sem
        # quebrar o relatório. Mas quem compara duas auditorias precisa de saber
        # que não foram feitas exactamente sob as mesmas regras.
        avisos.append(f"hash do contrato `{mh.group(1)[:12]}…` não é o actual "
                      f"`{hash_actual[:12]}…` — as regras mudaram desde então")

    # Modificadores entre parênteses: `CLEARED (decisão)` não é um estado.
    for m in RE_MODIFICADOR.finditer(texto):
        if limpar(m.group(2)).upper() not in COBERTURA_METODO:
            erro(f"estado com modificador `{m.group(0)}` — um estado por linha, "
                 "e o resto na Nota")

    # A tabela das obrigações: a fonte da verdade do relatório.
    #
    # As colunas encontram-se pelo **cabeçalho**, não pela posição. Antes eram
    # posicionais, e bastava trocar duas colunas de sítio para as verificações
    # deixarem de ver o que verificavam — em silêncio, que é a pior maneira.
    vistos: dict[str, int] = {}
    contagem: dict[str, int] = {e: 0 for e in ESTADOS}
    modulos_na_tabela: set[str] = set()
    colunas: dict[str, int] | None = None

    for linha in texto.splitlines():
        crua = linha.strip()
        if not crua.startswith("|"):
            colunas = None
            continue
        celulas_linha = celulas(crua.lstrip("|"))
        chaves = [limpar(c).lower() for c in celulas_linha]
        if "id" in chaves and "estado" in chaves:
            colunas = {nome: i for i, nome in enumerate(chaves)}
            # Encontrar por nome só resolve metade: uma coluna que não exista
            # com o nome esperado faz o `cel()` devolver `""`, e um `""` faz a
            # verificação ser saltada **sem dizer nada** — o mesmo modo de
            # falha das colunas posicionais, mudado de sítio. Um cabeçalho com
            # `Tipo de evidencia` deixava passar um `ACHOMETRO`.
            for alternativas in COLUNAS_USADAS:
                if not any(a in colunas for a in alternativas):
                    erro(f"tabela de obrigações sem a coluna `{alternativas[0]}` "
                         "— o que dependia dela não seria verificado")
            continue
        if set("".join(chaves)) <= {"-", ":", " "}:
            continue  # linha separadora
        if colunas is None:
            continue

        def cel(nome: str) -> str:
            i = colunas.get(nome)
            return limpar(celulas_linha[i]) if i is not None and i < len(celulas_linha) else ""

        oid = cel("id")
        if not RE_ID_OBRIGACAO.fullmatch(oid):
            continue
        # Uma linha mais curta do que o cabeçalho tem as últimas colunas a
        # devolver `""`, e um `CLEARED` com cobertura `AMOSTRA` passaria por
        # a coluna Cobertura simplesmente não estar lá.
        if len(celulas_linha) < len(colunas):
            erro(f"`{oid}`: linha com {len(celulas_linha)} células para "
                 f"{len(colunas)} colunas — o que falta não é verificado")
        estado = cel("estado")
        if not estado:
            continue
        if estado not in ESTADOS:
            erro(f"`{oid}`: estado `{estado}` fora do vocabulário")
            continue
        if estado == "PENDING":
            erro(f"`{oid}`: `PENDING` — nenhuma obrigação fica por analisar no fim")
        vistos[oid] = vistos.get(oid, 0) + 1
        contagem[estado] += 1

        if oid not in registo:
            erro(f"`{oid}`: ID que não existe no registo de gates")
            continue
        meta = registo[oid]
        if meta["module"]:
            modulos_na_tabela.add(meta["module"])

        declarada = cel("gate").lower()
        if declarada in {"sim", "crítico", "critico", "não", "nao"}:
            e_critico = declarada in {"sim", "crítico", "critico"}
            if e_critico != meta["critical"]:
                erro(f"`{oid}`: linha diz crítica={e_critico}, registo diz "
                     f"{meta['critical']}")

        # Tipos de evidência: combinam-se com `+`, e cada parte tem de existir.
        # `SEM_PROVA` e o travessão são ausência declarada, não um tipo.
        evidencia = cel("evidência") or cel("evidencia")
        if evidencia and evidencia not in {"-", "—", "SEM_PROVA"}:
            for parte in re.split(r"[+/]", evidencia):
                parte = parte.strip().split("(")[0].strip()
                if parte and parte not in TIPOS_EVIDENCIA:
                    erro(f"`{oid}`: tipo de evidência `{parte}` fora do vocabulário")

        cobertura = cel("cobertura")
        if cobertura and cobertura not in {"-", "—"}:
            if cobertura not in COBERTURA_METODO:
                erro(f"`{oid}`: cobertura do método `{cobertura}` fora do vocabulário")
            elif cobertura == "AMOSTRA" and estado == "CLEARED":
                erro(f"`{oid}`: CLEARED com cobertura AMOSTRA — uma amostra não "
                     "fecha uma obrigação de universalidade")

    if not vistos:
        # Acrescentar, não substituir: devolver uma lista nova deitava fora o
        # que já se tinha encontrado — o hash em falta, um estado com
        # modificador — e quem lê corrigia a tabela para depois descobrir que
        # afinal havia mais dois problemas escondidos por trás dela.
        erro("sem tabela de obrigações — não há relatório para validar")
        return problemas, avisos

    # Gates críticos em falta. Decidível: o registo sabe o módulo de cada um, e
    # a tabela diz que módulos foram auditados. Só os críticos — as
    # contributivas activadas dependem do âmbito pedido, e inventar erros sobre
    # elas seria o falso positivo que este validador existe para não ter.
    for oid, meta in sorted(registo.items()):
        if (meta["critical"] and meta["module"] in modulos_na_tabela
                and oid not in vistos):
            erro(f"`{oid}`: gate crítico de `{meta['module']}` que falta na tabela")

    for oid, n in sorted(vistos.items()):
        if n > 1:
            erro(f"`{oid}`: aparece {n} vezes na tabela")

    # A verificação que mais vale: as contagens contam-se na tabela.
    mc = RE_CONTAGEM.search(texto)
    if not mc:
        avisos.append("sem linha de contagens (`PROVEN: n · CLEARED: n · ...`)")
    else:
        # O til é a hedge que o contrato proíbe em nome próprio: um número
        # contado não precisa de "cerca de". O relatório de 2026-09-06 escrevia
        # `CLEARED: ~52`, e foi debaixo desse til que passou o `PROVEN: 6`.
        if "~" in mc.group(0):
            erro("contagens com `~`: contam-se na tabela, não se estimam")
        declarado = {
            "PROVEN": int(mc.group(1)), "CLEARED": int(mc.group(2)),
            "UNPROVEN": int(mc.group(3)), "NOT_APPLICABLE": int(mc.group(4)),
        }
        for estado, n in declarado.items():
            if n != contagem[estado]:
                erro(f"contagem de `{estado}`: o resumo diz {n}, a tabela tem "
                     f"{contagem[estado]}")

    # Verdict: a tabela de verdade, e a fracção da cobertura.
    #
    # A prioridade pertence ao **módulo do finding**, não ao documento. Enquanto
    # foi global, um P1 em `compliance` obrigava `FAIL` em `ui-ux`, em `ipc` e
    # em todos os outros — e a regra de agregação do SKILL.md ("senão, qualquer
    # CONCERNS → global CONCERNS") ficava inalcançável, porque nunca sobrava um
    # módulo por onde ela pudesse passar. Um validador que acusa relatórios
    # correctos é um validador que se aprende a ignorar.
    fora_das_cercas = sem_blocos_de_codigo(texto)
    por_modulo, sem_area = prioridades_por_modulo(fora_das_cercas)
    todas = {p for ps in por_modulo.values() for p in ps} | set(sem_area.values())

    # Duas passagens, porque o `Global:` vem na secção 1 e a tabela dos módulos
    # a seguir: para julgar a agregação é preciso já saber quem falhou.
    linhas_verdict = []
    for mv2 in RE_VERDICT.finditer(texto):
        modulo, produto, cobertura, num, den = mv2.groups()
        if produto not in VERDICTS_PRODUTO or cobertura not in VERDICTS_COBERTURA:
            continue
        linhas_verdict.append((modulo, limpar(modulo).lower(), produto,
                               cobertura, num, den))

    globais = {"global", "geral"}
    modulos = {n for _, n, _, _, _, _ in linhas_verdict if n not in globais}
    modulos_falhados = sorted(n for _, n, p, _, _, _ in linhas_verdict
                              if p == "FAIL" and n not in globais)
    # Num relatório de um módulo só, um finding sem `**Área**` tem dono óbvio, e
    # deixá-lo escapar por causa de uma linha em falta seria trocar um defeito
    # por outro. Em `full` não há como adivinhar: conta para o global.
    unico = next(iter(modulos)) if len(modulos) == 1 else None
    for fid in sorted(sem_area):
        avisos.append(
            f"`{fid}`: tem `**Prioridade**` mas não declara `**Área**` — "
            + (f"atribuído a `{unico}`, o único módulo deste relatório"
               if unico else "conta para o global e para módulo nenhum"))

    for modulo, nome, produto, cobertura, num, den in linhas_verdict:
        e_global = nome in globais
        prioridades = todas if e_global else por_modulo.get(nome, set())
        if nome == unico:
            prioridades = prioridades | set(sem_area.values())
        if (prioridades & {"P0", "P1"}) and produto != "FAIL":
            erro(f"`{modulo}`: {produto} com P0/P1 aberto — a tabela de verdade "
                 "obriga a FAIL")
        if num is None:
            erro(f"`{modulo}`: cobertura `{cobertura}` sem a fracção (X/Y)")
        elif cobertura == "COMPLETE" and num != den:
            erro(f"`{modulo}`: COMPLETE com {num}/{den} — COMPLETE exige todos")
        if e_global and modulos_falhados and produto != "FAIL":
            erro(f"global `{produto}` com `{modulos_falhados[0]}` em FAIL — "
                 "a agregação do SKILL.md obriga a FAIL")

    # Findings referidos existem — neste relatório, ou na memória dos baselines.
    #
    # O `relatorio.md` manda reutilizar o ID de um achado que já existia, e o
    # fecho lista os resolvidos desde a auditoria anterior. Exigir secção `###`
    # para cada ID citado tornava isso impossível: era proibir precisamente o
    # que o contrato manda fazer. Um ID que nem é deste relatório nem os
    # baselines conhecem continua a ser erro — é aí que mora a gralha.
    declarados = set(RE_FINDING.findall(fora_das_cercas))
    for fid in sorted(set(RE_ID_FINDING.findall(fora_das_cercas))
                      - declarados - conhecidos):
        erro(f"`{fid}`: citado sem secção `### {fid} — ...` e desconhecido dos "
             "baselines — não é deste relatório nem de auditoria anterior")

    # Um ID que os baselines já conhecem tem dono. Reutilizá-lo para outro
    # defeito parte a chave do `achados-resolvidos.md`: a 2026-09-08, cinco IDs
    # nomeavam dois defeitos diferentes no mesmo dia, e o `DIST-F02` de um
    # relatório era o `DIST-F01` de outro. Ou é o mesmo defeito outra vez — e
    # então diz-se reincidência, como o `relatorio.md` manda — ou é outro, e
    # leva número livre.
    for fid, bloco in blocos_de_finding(fora_das_cercas):
        if fid in anteriores and "reincid" not in bloco.lower():
            erro(f"`{fid}`: número já usado numa auditoria anterior e este "
                 "relatório não o assinala como reincidência — se é outro "
                 "defeito, dar-lhe um número livre")

    return problemas, avisos


def main(argv: list[str] | None = None) -> int:
    ap = _Parser(description=__doc__,
                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("relatorio", help="ficheiro .md do relatório")
    ap.add_argument("--gates", default=None,
                    help="registo v1 em JSON; por omissão, o registo v2 do próprio plugin")
    args = ap.parse_args(argv)

    caminho = Path(args.relatorio)
    if not caminho.is_file():
        print(f"erro: {caminho} não é um ficheiro", file=sys.stderr)
        return EXIT_CANNOT_ANALYSE
    # Registo: o `--gates` explícito (v1), senão o próprio plugin (v2:
    # CONTRACTS.md §7.4 + instruments.yaml de cada owner).
    raiz_plugin = Path(__file__).resolve().parents[3]
    if args.gates:
        gates = Path(args.gates)
        if not gates.is_file():
            print(f"erro: registo de gates não encontrado em {gates}", file=sys.stderr)
            return EXIT_CANNOT_ANALYSE
        registo = json.loads(gates.read_text(encoding="utf-8"))
    elif (raiz_plugin / "CONTRACTS.md").is_file():
        registo = registo_v2(raiz_plugin)
    else:
        print(f"erro: sem --gates e sem CONTRACTS.md em {raiz_plugin}", file=sys.stderr)
        return EXIT_CANNOT_ANALYSE

    versao_contrato, hash_actual = contrato_actual()
    if versao_contrato is None:
        print("erro: não consegui ler `**Versão do contrato**` do SKILL.md — "
              "sem contrato não há por que regras julgar", file=sys.stderr)
        return EXIT_CANNOT_ANALYSE
    major_suportado = int(versao_contrato.split(".")[0])

    texto = caminho.read_text(encoding="utf-8", errors="replace")
    mv = RE_VERSAO.search(texto)
    # Sem versão declarada, ou de outro major, não se valida — e não se despeja
    # uma lista de erros. Um relatório escrito sob outras regras produziria
    # dezenas de "erros" que são só a diferença entre os dois contratos, e isso
    # esconderia os defeitos a sério em vez de os mostrar.
    if not mv:
        print(f"# Validação de {caminho.name}\n")
        print("Sem `Contrato: versão X.Y.Z` — não se sabe por que regras julgar isto.")
        print("Relatórios anteriores ao contrato versionado não se validam por aqui;")
        print("o estado deles diz-se no índice (`baselines/ultima-auditoria.md`).")
        print("\nNÃO ANALISÁVEL")
        return EXIT_CANNOT_ANALYSE
    if int(mv.group(1)) != major_suportado:
        print(f"# Validação de {caminho.name}\n")
        print(f"Relatório declara contrato {mv.group(1)}.{mv.group(2)}.{mv.group(3)}; "
              f"o contrato instalado é {versao_contrato}.")
        print("\nNÃO ANALISÁVEL — um relatório não se julga por regras que não são as dele.")
        return EXIT_CANNOT_ANALYSE

    raiz_skill = Path(__file__).resolve().parent.parent
    m_data = re.match(r"(\d{4}-\d{2}-\d{2})", caminho.name)
    problemas, avisos = validar(
        texto, registo, caminho, hash_actual,
        achados_anteriores(raiz_skill, m_data.group(1) if m_data else None),
        achados_anteriores(raiz_skill))
    print(f"# Validação de {caminho.name}\n")
    print(f"## Problemas: {len(problemas)}")
    for p in problemas:
        print(f"  ERRO   {p}")
    print(f"\n## Avisos: {len(avisos)}")
    for a in avisos:
        print(f"  aviso  {a}")
    print()
    if problemas:
        print("RELATÓRIO ESTRUTURALMENTE INVÁLIDO")
    else:
        print("RELATÓRIO ESTRUTURALMENTE VÁLIDO — "
              "CONTEÚDO E SUFICIÊNCIA DA EVIDÊNCIA NÃO VALIDADOS")
    return EXIT_OK if not problemas else EXIT_PROBLEMS


def _executar(fn) -> int:
    try:
        codigo = fn()
        sys.stdout.flush()
        return codigo
    except BrokenPipeError:
        import os
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0


if __name__ == "__main__":
    sys.exit(_executar(main))
