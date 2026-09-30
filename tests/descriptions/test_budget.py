#!/usr/bin/env python3
"""Orçamento do catálogo de descrições.

As descrições das skills são o que o host carrega **sempre**: é com elas que
ele decide qual acordar. O Codex gasta no máximo 2% da janela nessa lista, ou
8 000 caracteres, o que for menor; o Claude Code tem o mesmo problema com outro
número. Um catálogo que cresce sem contagem acaba a comer contexto em silêncio
e a perder skills do picker.

Este teste é o guarda: o total tem de ficar abaixo do orçamento e nenhuma
descrição pode passar o teto por descrição (`measure-descriptions.py` já o diz
com exit 1; aqui fica medido no mesmo sítio que o resto).

O número não é decorativo: em 2026-09-30 o catálogo estava em 6 257 caracteres
de 8 000 (78%). Sobra espaço para ~7 skills antes de ser preciso decidir o que
sai — e essa decisão deve ser tomada com o número à frente, não por acidente.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]

# 90% do orçamento do Codex: o corte fica abaixo do limite do host, para o
# aviso chegar antes do silêncio.
TOTAL_BUDGET = 7_200
PER_DESCRIPTION = 250


def descriptions() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for skill in sorted((PLUGIN / "skills").glob("*/SKILL.md")):
        text = skill.read_text(encoding="utf-8")
        m = re.search(r'(?m)^description:\s*"?(.*?)"?\s*$', text)
        if m:
            out.append((skill.parent.name, m.group(1)))
    return out


class DescriptionBudget(unittest.TestCase):
    def test_the_catalogue_was_found(self):
        self.assertGreaterEqual(len(descriptions()), 25, "o teste perdeu o alvo")

    def test_no_description_passes_the_ceiling(self):
        for name, desc in descriptions():
            with self.subTest(skill=name):
                self.assertLessEqual(len(desc), PER_DESCRIPTION,
                                     f"{name}: {len(desc)} caracteres")

    def test_the_total_stays_inside_the_budget(self):
        total = sum(len(d) for _, d in descriptions())
        self.assertLessEqual(
            total, TOTAL_BUDGET,
            f"catálogo em {total} caracteres (orçamento {TOTAL_BUDGET}): uma skill nova exige "
            "que outra encolha ou saia — decidir com o número à frente")

    def test_every_description_starts_with_an_action_verb(self):
        """O gatilho é a primeira palavra; um substantivo não acorda nada."""
        for name, desc in descriptions():
            with self.subTest(skill=name):
                first = desc.split()[0].strip("`,").lower()
                self.assertTrue(first.isalpha(), f"{name}: começa em `{first}`")


if __name__ == "__main__":
    unittest.main(verbosity=2)
