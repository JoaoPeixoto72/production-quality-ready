#!/usr/bin/env python3
"""Regressao do `validate_report.py`.

A fixture central e o erro que motivou este validador: o relatorio de
2026-09-06 resumia `PROVEN: 6` com vinte linhas PROVEN na tabela. `PROVEN` e o
estado que conta defeitos, por isso um resumo errado ali e um verdict errado —
e e um erro inteiramente decidivel a olhar para o documento.

Correr com o Python resolvido na fase 0 do SKILL.md:
    <python> -m unittest discover -s scripts -p "test_*.py"
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_report as vr  # noqa: E402

REGISTO = {
    "SEC-01": {"module": "security", "critical": True,
               "primary_reference": "seguranca-processos-caminhos.md"},
    "SEC-02": {"module": "security", "critical": True,
               "primary_reference": "seguranca-processos-caminhos.md"},
    "SEC-08": {"module": "security", "critical": False,
               "primary_reference": "seguranca-processos-caminhos.md"},
}

CABECALHO = (
    "# Auditoria\n\n"
    "Contrato: SHA-256 "
    "23bda95fb37c0d72206c336796e59bf0f38d2875e26180280034f82cf9ce4b25\n\n"
)

TABELA = (
    "| ID | Estado | Gate | Evidencia | Cobertura | Artefacto | Nota |\n"
    "|---|---|---|---|---|---|---|\n"
    "| SEC-01 | CLEARED | sim | LEITURA | COMPLETA | - | ok |\n"
    "| SEC-02 | PROVEN | sim | LEITURA | COMPLETA | - | defeito confirmado |\n"
    "| SEC-08 | UNPROVEN | nao | - | - | - | sem execucao |\n"
)

CONTAGENS = "PROVEN: 1 - CLEARED: 1 - UNPROVEN: 1 - NOT_APPLICABLE: 0\n"


def _validar(texto: str, nome: str = "docs/auditorias/2026-09-08-security.md",
             hash_actual: str | None = None):
    with tempfile.TemporaryDirectory() as tmp:
        caminho = Path(tmp) / "auditorias" / Path(nome).name
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(texto, encoding="utf-8")
        return vr.validar(texto, REGISTO, caminho, hash_actual)


class Contagens(unittest.TestCase):
    def test_resumo_que_nao_bate_com_a_tabela(self):
        # O erro de 2026-09-06, em ponto pequeno: diz 6, a tabela tem 1.
        texto = CABECALHO + TABELA + "\nPROVEN: 6 - CLEARED: 1 - UNPROVEN: 1 - NOT_APPLICABLE: 0\n"
        problemas, _ = _validar(texto)
        self.assertTrue(
            any("contagem de `PROVEN`" in p and "diz 6" in p and "tem 1" in p
                for p in problemas),
            f"nao apanhou o 6-versus-1: {problemas}")

    def test_resumo_correcto_passa(self):
        problemas, _ = _validar(CABECALHO + TABELA + "\n" + CONTAGENS)
        self.assertEqual(problemas, [], f"falsos positivos: {problemas}")


class Vocabulario(unittest.TestCase):
    def test_estado_com_modificador(self):
        texto = CABECALHO + TABELA + "\n" + CONTAGENS + "\nDIST-06 ficou CLEARED (decisao).\n"
        problemas, _ = _validar(texto)
        self.assertTrue(any("modificador" in p for p in problemas), problemas)

    def test_cobertura_do_metodo_nao_e_modificador(self):
        # `ANALISE_ESTATICA (COMPLETA)` é vocabulário legítimo, não um estado
        # esticado — não pode dar erro.
        texto = CABECALHO + TABELA + "\n" + CONTAGENS + "\nPROVEN (COMPLETA) na leitura.\n"
        problemas, _ = _validar(texto)
        self.assertFalse(any("modificador" in p for p in problemas), problemas)

    def test_id_desconhecido(self):
        linha = "| SEC-99 | CLEARED | sim | LEITURA | COMPLETA | - | inventado |\n"
        problemas, _ = _validar(CABECALHO + TABELA + linha + "\n" + CONTAGENS)
        self.assertTrue(any("SEC-99" in p and "nao existe" in p.replace("ã", "a")
                            for p in problemas), problemas)

    def test_id_repetido(self):
        linha = "| SEC-01 | CLEARED | sim | LEITURA | COMPLETA | - | outra vez |\n"
        texto = (CABECALHO + TABELA + linha + "\n"
                 + "PROVEN: 1 - CLEARED: 2 - UNPROVEN: 1 - NOT_APPLICABLE: 0\n")
        problemas, _ = _validar(texto)
        self.assertTrue(any("SEC-01" in p and "2 vezes" in p for p in problemas),
                        problemas)

    def test_criticidade_contra_o_registo(self):
        # SEC-08 nao e critica no registo; a linha diz que e.
        tabela = TABELA.replace("| SEC-08 | UNPROVEN | nao |",
                                "| SEC-08 | UNPROVEN | sim |")
        problemas, _ = _validar(CABECALHO + tabela + "\n" + CONTAGENS)
        self.assertTrue(any("SEC-08" in p and "critica" in p.replace("í", "i")
                            for p in problemas), problemas)

    def test_cleared_com_amostra(self):
        tabela = TABELA.replace("| SEC-01 | CLEARED | sim | LEITURA | COMPLETA |",
                                "| SEC-01 | CLEARED | sim | LEITURA | AMOSTRA |")
        problemas, _ = _validar(CABECALHO + tabela + "\n" + CONTAGENS)
        self.assertTrue(any("AMOSTRA" in p for p in problemas), problemas)


class Sondas(unittest.TestCase):
    """Os sete casos que passavam por baixo do validador.

    Cada um e um defeito que o contrato proibe em nome proprio e que a primeira
    versao deste validador declarava verificar sem verificar: `TIPOS_EVIDENCIA`
    e `PRIORIDADES` eram constantes mortas, e as colunas eram lidas por
    posicao. Um validador que diz VALIDO a um documento com estes defeitos e
    pior do que nenhum, porque produz confianca.
    """

    def test_contagem_com_til(self):
        texto = CABECALHO + TABELA + "\nPROVEN: ~1 - CLEARED: ~1 - UNPROVEN: ~1 - NOT_APPLICABLE: 0\n"
        problemas, _ = _validar(texto)
        self.assertTrue(any("~" in p for p in problemas), problemas)

    def test_tipo_de_evidencia_inventado(self):
        tabela = TABELA.replace("| SEC-01 | CLEARED | sim | LEITURA |",
                                "| SEC-01 | CLEARED | sim | ACHOMETRO |")
        problemas, _ = _validar(CABECALHO + tabela + "\n" + CONTAGENS)
        self.assertTrue(any("ACHOMETRO" in p for p in problemas), problemas)

    def test_sufixo_abolido_pelo_2_0_0(self):
        tabela = TABELA.replace("| SEC-01 | CLEARED | sim | LEITURA |",
                                "| SEC-01 | CLEARED | sim | ANALISE_ESTATICA_PARCIAL |")
        problemas, _ = _validar(CABECALHO + tabela + "\n" + CONTAGENS)
        self.assertTrue(any("ANALISE_ESTATICA_PARCIAL" in p for p in problemas),
                        problemas)

    def test_combinacao_de_tipos_validos_passa(self):
        tabela = TABELA.replace("| SEC-01 | CLEARED | sim | LEITURA |",
                                "| SEC-01 | CLEARED | sim | LEITURA+DOCUMENTO |")
        problemas, _ = _validar(CABECALHO + tabela + "\n" + CONTAGENS)
        self.assertEqual(problemas, [], problemas)

    def test_colunas_por_outra_ordem(self):
        # As colunas encontram-se pelo cabecalho: trocar duas de sitio nao pode
        # cegar a verificacao.
        texto = (CABECALHO
                 + "| ID | Estado | Cobertura | Gate | Evidencia | Nota |\n"
                   "|---|---|---|---|---|---|\n"
                   "| SEC-01 | CLEARED | AMOSTRA | sim | LEITURA | ok |\n"
                   "| SEC-02 | PROVEN | COMPLETA | sim | LEITURA | mau |\n"
                 + "\nPROVEN: 1 - CLEARED: 1 - UNPROVEN: 0 - NOT_APPLICABLE: 0\n")
        problemas, _ = _validar(texto)
        self.assertTrue(any("AMOSTRA" in p for p in problemas), problemas)

    def test_gate_critico_em_falta(self):
        tabela = TABELA.replace(
            "| SEC-02 | PROVEN | sim | LEITURA | COMPLETA | - | defeito confirmado |\n", "")
        texto = CABECALHO + tabela + "\nPROVEN: 0 - CLEARED: 1 - UNPROVEN: 1 - NOT_APPLICABLE: 0\n"
        problemas, _ = _validar(texto)
        self.assertTrue(any("SEC-02" in p and "falta" in p for p in problemas),
                        problemas)

    def test_pending_no_fim(self):
        linha = "| SEC-02 | PENDING | sim | - | - | - | por fazer |\n"
        tabela = TABELA.replace(
            "| SEC-02 | PROVEN | sim | LEITURA | COMPLETA | - | defeito confirmado |\n",
            linha)
        texto = CABECALHO + tabela + "\nPROVEN: 0 - CLEARED: 1 - UNPROVEN: 1 - NOT_APPLICABLE: 0\n"
        problemas, _ = _validar(texto)
        self.assertTrue(any("PENDING" in p for p in problemas), problemas)

    def test_estado_fora_do_vocabulario(self):
        tabela = TABELA.replace("| SEC-01 | CLEARED |", "| SEC-01 | PROVADO |")
        problemas, _ = _validar(CABECALHO + tabela + "\n" + CONTAGENS)
        self.assertTrue(any("PROVADO" in p for p in problemas), problemas)

    def test_hash_de_outro_contrato_avisa(self):
        problemas, avisos = _validar(CABECALHO + TABELA + "\n" + CONTAGENS,
                                     hash_actual="b" * 64)
        self.assertEqual(problemas, [], problemas)
        self.assertTrue(any("regras mudaram" in a for a in avisos), avisos)


class Contrato(unittest.TestCase):
    def test_le_o_hash_do_contracts_md(self):
        self.assertRegex(vr.contrato_actual() or "", r"^[0-9a-f]{64}$")

    def test_contrato_escreve_o_hash_e_sai(self):
        import contextlib, io
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            codigo = vr.main(["--contrato"])
        self.assertEqual(codigo, vr.EXIT_OK)
        self.assertEqual(saida.getvalue().strip(), vr.contrato_actual())


class Verdict(unittest.TestCase):
    def test_p1_aberto_obriga_a_fail(self):
        texto = (CABECALHO + "security: Produto: CONCERNS - Cobertura: PARTIAL (2/2)\n\n"
                 + TABELA + "\n" + CONTAGENS
                 + "\n### SEC-F01 - Uma coisa\n- **Prioridade**: P1\n")
        problemas, _ = _validar(texto)
        self.assertTrue(any("FAIL" in p for p in problemas), problemas)

    def test_cobertura_sem_fraccao(self):
        texto = CABECALHO + "security: Produto: PASS - Cobertura: COMPLETE\n\n" + TABELA + "\n" + CONTAGENS
        problemas, _ = _validar(texto)
        self.assertTrue(any("frac" in p for p in problemas), problemas)

    def test_complete_com_fraccao_incompleta(self):
        texto = CABECALHO + "security: Produto: PASS - Cobertura: COMPLETE (1/2)\n\n" + TABELA + "\n" + CONTAGENS
        problemas, _ = _validar(texto)
        self.assertTrue(any("COMPLETE" in p and "1/2" in p for p in problemas),
                        problemas)


class ContratoDoRelatorio(unittest.TestCase):
    def test_sem_hash_e_nao_analisavel(self):
        with tempfile.TemporaryDirectory() as tmp:
            gates = Path(tmp) / "gates.json"
            gates.write_text("{}", encoding="utf-8")
            rel = Path(tmp) / "antigo.md"
            rel.write_text("# Auditoria antiga\n\n| SEC-01 | CLEARED | sim |\n",
                           encoding="utf-8")
            codigo = vr.main([str(rel), "--gates", str(gates)])
        self.assertEqual(codigo, vr.EXIT_CANNOT_ANALYSE)

    def test_outro_hash_e_aviso_nao_recusa(self):
        _, avisos = _validar(CABECALHO + TABELA + CONTAGENS, hash_actual="b" * 64)
        self.assertTrue(any("as regras mudaram" in a for a in avisos), avisos)


def _finding(fid: str, prioridade: str, area: str | None) -> str:
    linhas = [f"### {fid} - titulo do defeito", "",
              "- **Estado**: CONFIRMED",
              f"- **Prioridade**: {prioridade}"]
    if area is not None:
        linhas.append(f"- **Area**: {area}")
    return "\n".join(linhas) + "\n\n"


class VerdictPorModulo(unittest.TestCase):
    """O defeito de maior valor dos evals de 2026-09-08.

    O `tem_p0p1` era global ao documento: a auditoria `full` desse dia tinha um
    P1 em `compliance` e um em `rust`, e o validador exigia `FAIL` nos doze
    modulos — dez erros falsos num relatorio correcto. Pior do que inutil: e
    assim que um validador se aprende a ignorar.
    """

    def test_p1_num_modulo_nao_contamina_outro(self):
        texto = (CABECALHO + "security: Produto: FAIL - Cobertura: COMPLETE (2/2)\n"
                 "ui-ux: Produto: PASS - Cobertura: COMPLETE (8/8)\n\n"
                 + TABELA + CONTAGENS + _finding("SEC-F01", "P1", "security"))
        problemas, _ = _validar(texto)
        self.assertEqual([], [p for p in problemas if "ui-ux" in p])

    def test_p1_no_proprio_modulo_continua_a_obrigar_fail(self):
        texto = (CABECALHO + "security: Produto: CONCERNS - Cobertura: COMPLETE (2/2)\n\n"
                 + TABELA + CONTAGENS + _finding("SEC-F01", "P1", "security"))
        problemas, _ = _validar(texto)
        self.assertTrue(any("security" in p and "FAIL" in p for p in problemas),
                        f"nao acusou o modulo que tem mesmo o P1: {problemas}")

    def test_p2_nao_obriga_fail(self):
        texto = (CABECALHO + "security: Produto: CONCERNS - Cobertura: COMPLETE (2/2)\n\n"
                 + TABELA + CONTAGENS + _finding("SEC-F01", "P2", "security"))
        problemas, _ = _validar(texto)
        self.assertEqual([], [p for p in problemas if "FAIL" in p])

    def test_finding_sem_area_avisa_e_conta_para_o_global(self):
        """Nao se atribui a ninguem, mas tambem nao se esquece."""
        texto = (CABECALHO + "Global: Produto: CONCERNS - Cobertura: COMPLETE (2/2)\n\n"
                 + TABELA + CONTAGENS + _finding("SEC-F01", "P1", None))
        problemas, avisos = _validar(texto)
        self.assertTrue(any("SEC-F01" in a and "Área" in a for a in avisos), avisos)
        self.assertTrue(any("FAIL" in p for p in problemas),
                        f"o P1 orfao devia obrigar o global a FAIL: {problemas}")


class Agregacao(unittest.TestCase):
    def test_a_linha_global_e_lida(self):
        """`Global:` tem maiuscula, e a regex antiga so aceitava minusculas:
        a linha mais importante do relatorio passava sem ser lida."""
        texto = (CABECALHO + "Global: Produto: PASS - Cobertura: COMPLETE (1/2)\n\n"
                 + TABELA + CONTAGENS)
        problemas, _ = _validar(texto)
        self.assertTrue(any("COMPLETE exige todos" in p for p in problemas),
                        f"a linha Global nao foi lida: {problemas}")

    def test_global_nao_passa_com_um_modulo_em_fail(self):
        texto = (CABECALHO + "Global: Produto: CONCERNS - Cobertura: COMPLETE (2/2)\n"
                 "security: Produto: FAIL - Cobertura: COMPLETE (2/2)\n\n"
                 + TABELA + CONTAGENS + _finding("SEC-F01", "P1", "security"))
        problemas, _ = _validar(texto)
        self.assertTrue(any("agrega" in p for p in problemas),
                        f"a agregacao do SKILL.md nao foi verificada: {problemas}")


class SemTabela(unittest.TestCase):
    def test_os_problemas_ja_encontrados_nao_se_perdem(self):
        """Devolver uma lista nova deitava fora o que ja se sabia: corrigia-se
        a tabela para so entao descobrir os outros dois problemas."""
        texto = ("# Auditoria\n\nContrato:\n\n"
                 "SEC-01 ficou CLEARED (decisao)\n")
        problemas, _ = _validar(texto)
        self.assertTrue(any("tabela de obriga" in p for p in problemas), problemas)
        self.assertTrue(any("SHA-256" in p for p in problemas),
                        f"o hash em falta desapareceu: {problemas}")
        self.assertTrue(any("modificador" in p for p in problemas),
                        f"o modificador desapareceu: {problemas}")


class ColunasQueFaltam(unittest.TestCase):
    """Encontrar as colunas por nome resolveu metade do problema: o `cel()`
    devolve `""` para o que nao encontra, e um `""` faz a verificacao ser
    saltada em silencio. Duas sondas dos evals de 2026-09-08 passaram limpas
    exactamente assim."""

    def _validar_tabela(self, tabela: str):
        texto = (CABECALHO + "security: Produto: CONCERNS - Cobertura: COMPLETE (2/2)\n\n"
                 + tabela + CONTAGENS)
        return _validar(texto)[0]

    def test_cabecalho_com_a_coluna_de_evidencia_renomeada(self):
        tabela = (
            "| ID | Estado | Gate | Tipo de evidencia | Cobertura | Nota |\n"
            "|---|---|---|---|---|---|\n"
            "| SEC-01 | CLEARED | sim | ACHOMETRO | COMPLETA | ok |\n")
        problemas = self._validar_tabela(tabela)
        self.assertTrue(any("evid" in p for p in problemas),
                        f"a coluna renomeada passou sem se dizer nada: {problemas}")

    def test_linha_mais_curta_do_que_o_cabecalho(self):
        """Sem a coluna Cobertura, um CLEARED com AMOSTRA passaria."""
        tabela = (
            "| ID | Estado | Gate | Evidencia | Cobertura | Artefacto | Nota |\n"
            "|---|---|---|---|---|---|---|\n"
            "| SEC-01 | CLEARED | sim | LEITURA |\n")
        problemas = self._validar_tabela(tabela)
        self.assertTrue(any("SEC-01" in p and "colunas" in p for p in problemas),
                        f"a linha curta passou: {problemas}")

    def test_cabecalho_completo_nao_se_queixa(self):
        problemas = self._validar_tabela(TABELA)
        self.assertEqual([], [p for p in problemas if "coluna" in p or "célula" in p])


class HashDoContrato(unittest.TestCase):
    """O relatorio ui-ux de 2026-09-08 escrevia o digest entre crases, como o
    markdown de um relatorio real o escreve, e o validador respondia "sem
    SHA-256 do contrato" — a um documento que o tinha."""

    def _sem_hash(self, cabecalho: str):
        texto = (cabecalho + "security: Produto: CONCERNS - Cobertura: COMPLETE (2/2)\n\n"
                 + TABELA + CONTAGENS)
        problemas, _ = _validar(texto)
        return [p for p in problemas if "SHA-256" in p]

    def test_digest_entre_crases(self):
        digest = "a" * 64
        self.assertEqual([], self._sem_hash(
            f"# Auditoria\n\nContrato: SHA-256 `{digest}`\n\n"))

    def test_digest_nu(self):
        digest = "a" * 64
        self.assertEqual([], self._sem_hash(
            f"# Auditoria\n\nContrato: SHA-256 {digest}\n\n"))

    def test_sem_digest_nenhum_continua_a_ser_erro(self):
        self.assertNotEqual([], self._sem_hash(
            "# Auditoria\n\nContrato:\n\n"))


class AchadosCitados(unittest.TestCase):
    """O `relatorio.md` manda reutilizar o ID de um achado que ja existia, e o
    fecho lista os resolvidos desde a auditoria anterior. Exigir seccao `###`
    para cada ID citado proibia exactamente isso: o full de 2026-09-08 foi
    recusado por citar o DIAG-F01, que estava no achados-resolvidos.md."""

    def _com(self, corpo: str, anteriores=None, conhecidos=None):
        texto = (CABECALHO + "security: Produto: CONCERNS - Cobertura: COMPLETE (2/2)\n\n"
                 + TABELA + CONTAGENS + corpo)
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "auditorias" / "2026-09-08-security.md"
            caminho.parent.mkdir(parents=True)
            caminho.write_text(texto, encoding="utf-8")
            return vr.validar(texto, REGISTO, caminho, None, anteriores,
                              conhecidos)

    def test_id_de_auditoria_anterior_nao_e_erro(self):
        problemas, _ = self._com("Ver DIAG-F01, resolvido desde entao.\n",
                                 {"DIAG-F01"})
        self.assertEqual([], [p for p in problemas if "DIAG-F01" in p])

    def test_id_que_ninguem_conhece_continua_a_ser_erro(self):
        problemas, _ = self._com("Ver SEC-F99.\n", {"DIAG-F01"})
        self.assertTrue(any("SEC-F99" in p for p in problemas), problemas)

    def test_todos_os_soltos_sao_reportados(self):
        """Havia um `break` no laco: dois IDs pendurados davam um erro so, e o
        segundo so aparecia depois de o primeiro ser corrigido."""
        problemas, _ = self._com("Ver SEC-F98 e SEC-F99.\n", set())
        self.assertTrue(any("SEC-F98" in p for p in problemas), problemas)
        self.assertTrue(any("SEC-F99" in p for p in problemas), problemas)

    def test_o_que_tem_seccao_no_proprio_relatorio_passa(self):
        problemas, _ = self._com(_finding("SEC-F01", "P2", "security")
                                 + "Ver SEC-F01.\n", set())
        self.assertEqual([], [p for p in problemas if "SEC-F01" in p])

    def test_numero_ja_usado_sem_dizer_reincidencia(self):
        """A 2026-09-08, cinco IDs nomeavam dois defeitos diferentes no mesmo
        dia: o DIST-F02 de um relatorio era o DIST-F01 de outro. O ID e' a
        chave do achados-resolvidos.md."""
        problemas, _ = self._com(_finding("SEC-F01", "P2", "security"),
                                 {"SEC-F01"})
        self.assertTrue(any("SEC-F01" in p and "reincid" in p for p in problemas),
                        f"o numero tomado foi reutilizado em silencio: {problemas}")

    def test_numero_ja_usado_assinalado_como_reincidencia(self):
        bloco = _finding("SEC-F01", "P2", "security").rstrip() + \
            "\n- **Nota**: reincidencia da auditoria de 2026-09-06\n\n"
        problemas, _ = self._com(bloco, {"SEC-F01"})
        self.assertEqual([], [p for p in problemas if "reincid" in p])

    def test_numero_livre_nao_se_queixa(self):
        problemas, _ = self._com(_finding("SEC-F02", "P2", "security"),
                                 {"SEC-F01"})
        self.assertEqual([], [p for p in problemas if "SEC-F02" in p])

    def _indice(self, raiz: Path):
        (raiz / "baselines").mkdir()
        (raiz / "baselines" / "ultima-auditoria.md").write_text(
            "# indice\n\n"
            "## 2026-09-09 — full\n\nSEC-F03\n"
            "## 2026-09-08 — full\n\nSEC-F01, SEC-F02\n"
            "## 2026-09-06 — full\n\nDIAG-F01\n",
            encoding="utf-8")

    def test_um_relatorio_nao_e_acusado_pelo_seu_proprio_futuro(self):
        """Os achados de um relatorio entram nos baselines depois de ele ser
        escrito, e uma auditoria seguinte pode reutilizar um ID dele como
        reincidencia. Sem nocao de tempo, o 2026-09-08-full.md era acusado de
        copiar de si proprio assim que o indice ganhou a entrada de
        2026-09-09."""
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            self._indice(raiz)

            antes = vr.achados_anteriores(raiz, "2026-09-08")
            self.assertIn("DIAG-F01", antes, "perdeu a memoria do que e' anterior")
            self.assertNotIn("SEC-F01", antes, "acusou-o dos seus proprios IDs")
            self.assertNotIn("SEC-F03", antes, "acusou-o do seu futuro")

    def test_sem_data_a_memoria_e_toda(self):
        """A pergunta "este ID existe?" nao tem nada que ver com o tempo."""
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            self._indice(raiz)
            todos = vr.achados_anteriores(raiz)
            self.assertEqual({"DIAG-F01", "SEC-F01", "SEC-F02", "SEC-F03"}, todos)

    def test_citar_uma_auditoria_do_mesmo_dia_nao_e_erro(self):
        """Uma auditoria de modulo cita o `full` do mesmo dia. Se a citacao
        fosse julgada pela memoria "estritamente anterior", os quatro
        relatorios de modulo de 2026-09-09 eram todos invalidos."""
        problemas, _ = self._com("A causa-raiz e' o REACT-F01.\n",
                                 anteriores=set(), conhecidos={"REACT-F01"})
        self.assertEqual([], [p for p in problemas if "REACT-F01" in p], problemas)

    def test_bloco_proposto_para_os_baselines_nao_declara_achados(self):
        """A fase 4 obriga o relatorio a propor os blocos prontos a colar, e
        esses blocos trazem titulos `### XXX-Fnn`. Lidos como se fossem do
        relatorio, a 2026-09-09 um relatorio que propunha fechar o LEGAL-F03
        era acusado de reutilizar esse numero: cumprir o contrato produzia um
        documento invalido."""
        proposto = ("## Para registar nos baselines\n\n```markdown\n"
                    "### SEC-F01 - O defeito original\n\n"
                    "- **Resolvido em**: hoje\n```\n")
        problemas, _ = self._com(proposto, {"SEC-F01"})
        self.assertEqual([], [p for p in problemas if "SEC-F01" in p], problemas)

    def test_o_que_esta_fora_das_cercas_continua_a_contar(self):
        problemas, _ = self._com(_finding("SEC-F01", "P2", "security"),
                                 {"SEC-F01"})
        self.assertTrue(any("SEC-F01" in p for p in problemas), problemas)

    def test_os_baselines_sao_a_memoria(self):
        """Lidos do disco do projecto, e sem o evals-corridos.md (que cita IDs
        para falar de uma colisao entre relatorios, nao para os registar).

        No plugin agnostico nao ha baselines: sao do repo auditado, nao da
        skill. O teste escreve uma fixture em tmp e prova que a funcao a le
        correctamente, e que a lista `BASELINES_COM_ACHADOS` nao inclui o
        `evals-corridos.md`.
        """
        self.assertNotIn("evals-corridos.md", vr.BASELINES_COM_ACHADOS)
        with tempfile.TemporaryDirectory() as tmp:
            baselines = Path(tmp) / "baselines"
            baselines.mkdir()
            (baselines / "achados-resolvidos.md").write_text(
                "## 2026-09-14 — teste\n"
                "\n"
                "### DIAG-F01 — fixture\n"
                "- **Data de resolução**: 2026-09-14\n",
                encoding="utf-8",
            )
            self.assertIn("DIAG-F01", vr.achados_anteriores(Path(tmp)))
        # E sem baselines, devolve conjunto vazio, sem excepcao.
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(set(), vr.achados_anteriores(Path(tmp)))


class RegistoV2(unittest.TestCase):
    """Sem `--gates`, o registo vem do próprio plugin: CONTRACTS.md §7.4."""

    REGISTO = vr.registo_v2(Path(__file__).resolve().parents[3])

    def test_canonicos_do_contrato_sao_criticos(self):
        criticos = {k for k, m in self.REGISTO.items() if m["critical"]}
        self.assertIn("security-audit::sec.secrets-not-committed", criticos)
        # O intervalo `sell-01-…` … `sell-06-…` expande para os seis.
        self.assertEqual(6, sum(k.startswith("commercial-readiness::sell-0")
                                for k in criticos))
        self.assertFalse(self.REGISTO["ui-system::ui.focus-ring"]["critical"])

    def test_ids_owner_check_sao_lidos_e_os_criticos_em_falta_apontados(self):
        texto = (CABECALHO
                 + "| ID | Estado | Gate | Evidencia | Cobertura | Artefacto | Nota |\n"
                 "|---|---|---|---|---|---|---|\n"
                 "| `ui-system::ui.architectural-boundary` | CLEARED | sim | EXECUCAO | COMPLETA | - | ok |\n"
                 "| `ui-system::ui.focus-ring` | CLEARED | nao | EXECUCAO | COMPLETA | - | ok |\n"
                 "| `security-audit::sec.deps-no-cve` | CLEARED | sim | EXECUCAO | COMPLETA | - | ok |\n"
                 "\nPROVEN: 0 - CLEARED: 3 - UNPROVEN: 0 - NOT_APPLICABLE: 0\n")
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "auditorias" / "2026-09-23-full.md"
            caminho.parent.mkdir(parents=True)
            problemas, _ = vr.validar(texto, self.REGISTO, caminho)
        self.assertTrue(any("sec.secrets-not-committed" in p and "falta" in p
                            for p in problemas), problemas)
        self.assertFalse(any("ui.architectural-boundary" in p for p in problemas), problemas)
        self.assertFalse(any("contagem" in p for p in problemas), problemas)


if __name__ == "__main__":
    unittest.main()
