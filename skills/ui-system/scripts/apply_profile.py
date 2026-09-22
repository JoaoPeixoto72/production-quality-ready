#!/usr/bin/env python3
"""
apply_profile.py — instala o design system num projeto consumidor.

Copia a fundação (tokens, core, temas e os componentes) e, por cima, o overlay
do perfil pedido; depois escreve o `index.css` de entrada com a ordem das
camadas e com imports que **resolvem a partir do projeto**.

Escrever o `index.css` aqui é o ponto todo. O `index.css` de um perfil importa
`../../../../assets/css/index.css` — um caminho que só faz sentido dentro da
skill. Copiado tal e qual para um projeto, apontava para fora dele e o build
partia-se; o consumidor tinha de montar a árvore à mão para descobrir porquê.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

EXIT_OK, EXIT_ERRO, EXIT_USO = 0, 1, 64

#: A entrada gerada. As camadas declaram-se **antes** de qualquer `@import`:
#: um `@import` tem de preceder tudo o que não seja `@charset` ou uma `@layer`
#: vazia, e tê-la a meio faz o PostCSS avisar a cada arranque.
MODELO_INDEX = """/* Gerado por `scripts/apply_profile.py` — perfil `{perfil}`.
 *
 * Tudo o que vem do sistema vive numa `@layer`. CSS sem camada ganha sempre a
 * CSS com camada, seja qual for a ordem de carregamento: é isso que deixa o
 * CSS que o projeto já tinha continuar a mandar no seu próprio aspecto
 * enquanto a migração anda, sem uma única regra de força.
 */
@layer ui.reset, ui.tokens, ui.core, ui.theme;
{fontes}
/* Fundação: primitivos invariantes, mecânica dos slots `data-ui`, e o tema. */
@import "./tokens.css";
@import "./core.css";
{temas}{overlay}"""

AVISO_FONTES = """
/* As fontes do perfil não vêm nesta skill: os binários são do projeto.
 * Instalar, e trazer estas duas linhas para fora do comentário — sem CDN,
 * que uma fonte remota é erro de auditoria em `offline: true`, e uma fonte
 * que não carrega não dá erro: dá outra fonte em silêncio.
 *
 *   npm i {pacotes}
 *
{imports}
 */
"""


def _copiar(origem: Path, destino: Path, seco: bool) -> None:
    if seco:
        print(f"[seco] {origem.name} -> {destino}")
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, destino)


def _pasta_ui(alvo: Path, explicito: str | None) -> Path:
    if explicito:
        return alvo / explicito
    for candidato in ("src/ui", "packages/ui/src", "packages/ui-react/src"):
        if (alvo / candidato).exists():
            return alvo / candidato
    return alvo / "src/ui"


def _fontes_do_perfil(config: dict) -> tuple[list[str], list[str]]:
    """Os pacotes npm e os `@import` das fontes que o perfil declara."""
    fontes = (config.get("styling") or {}).get("fonts") or {}
    pacotes, imports = [], []
    for chave in ("sans", "mono", "serif"):
        nome = fontes.get(chave)
        if not nome:
            continue
        # "Instrument Sans Variable" -> @fontsource-variable/instrument-sans
        base = nome.replace(" Variable", "").strip().lower().replace(" ", "-")
        pacote = f"@fontsource-variable/{base}" if "Variable" in nome else f"@fontsource/{base}"
        pacotes.append(pacote)
        imports.append(f' * @import "{pacote}";')
    return pacotes, imports


def aplicar(skill: Path, alvo: Path, perfil: str | None, seco: bool, ui_dir: str | None,
            com_tailwind: bool, with_react: bool = False) -> int:
    if perfil:
        pasta_perfil = skill / "profiles" / perfil
        if not pasta_perfil.is_dir():
            print(f"Erro: perfil '{perfil}' não existe em {pasta_perfil}", file=sys.stderr)
            pasta_perfis = skill / "profiles"
            disponiveis = sorted(p.name for p in pasta_perfis.iterdir() if p.is_dir()) if pasta_perfis.is_dir() else []
            print(f"Perfis disponíveis: {', '.join(disponiveis) or '(nenhum — usar o perfil base sem argumento)'}", file=sys.stderr)
            return EXIT_ERRO
    else:
        perfil = "base"
        pasta_perfil = skill / "assets"

    ui = _pasta_ui(alvo, ui_dir)
    css = ui / "css"
    rel_ui = ui.relative_to(alvo).as_posix()
    print(f"==> perfil '{perfil}' em {alvo}  (UI em {rel_ui}/)")

    config_perfil = pasta_perfil / "ui.config.json"
    config = json.loads(config_perfil.read_text(encoding="utf-8")) if config_perfil.is_file() else {}

    # -- 1. Fundação: tokens, core e os componentes -------------------------
    for nome in ("tokens.css", "core.css"):
        _copiar(skill / "assets" / "css" / nome, css / nome, seco)

    if com_tailwind:
        _copiar(skill / "assets" / "css" / "tailwind-bridge.css",
                css / "tailwind-bridge.css", seco)

    # Components are a React pack (packs/react-components); only copied when
    # the profile (or --with-react) asks for it. hono/jsx, Svelte, vanilla
    # and Tauri-without-React projects take tokens + core + themes only.
    quer_react = bool(config.get("react")) or with_react
    if quer_react:
        componentes = sorted((skill / "packs" / "react-components").glob("*.ts*"))
        for f in componentes:
            _copiar(f, ui / "components" / f.name, seco)
        print(f"  · {len(componentes)} componentes React (packs/react-components)")
    else:
        print("  · componentes React não copiados (sem 'react' no perfil; usar --with-react)")

    # -- 2. Só os temas que o perfil declara --------------------------------
    temas = config.get("themes") or (config.get("styling") or {}).get("themes") or ["neutral"]
    for tema in temas:
        origem = skill / "assets" / "css" / "themes" / f"{tema}.css"
        if origem.is_file():
            _copiar(origem, css / "themes" / f"{tema}.css", seco)
    print(f"  · temas: {', '.join(temas)}")

    # -- 3. O overlay do perfil, à parte da fundação ------------------------
    #    Fica em `css/profile/` de propósito: o que é do perfil vê-se pelo
    #    caminho, e uma actualização da fundação não lhe passa por cima.
    overlay = []
    perfil_css = pasta_perfil / "assets" / "css"
    def _ordem(nome: str) -> int:
        # A mesma ordem da fundação: primeiro o que define, depois o que
        # desenha, e o tema por último.
        return {"tokens.css": 0, "core.css": 1}.get(nome, 2)

    ficheiros = sorted(perfil_css.glob("*.css")) + sorted(perfil_css.glob("themes/*.css"))
    for origem in sorted(ficheiros, key=lambda f: (_ordem(f.name), f.name)):
        if origem.name.startswith("index"):
            continue  # a entrada é gerada, não copiada
        destino_nome = origem.name if origem.parent.name != "themes" else f"tema-{origem.name}"
        _copiar(origem, css / "profile" / destino_nome, seco)
        overlay.append(destino_nome)

    # -- 4. A entrada, com imports que resolvem daqui -----------------------
    pacotes, imports = _fontes_do_perfil(config)
    bloco_fontes = ""
    if pacotes:
        bloco_fontes = AVISO_FONTES.format(pacotes=" ".join(pacotes), imports="\n".join(imports))

    bloco_temas = "".join(f'@import "./themes/{t}.css";\n' for t in temas if (skill / "assets" / "css" / "themes" / f"{t}.css").is_file())
    bloco_overlay = ""
    if overlay:
        bloco_overlay = ("\n/* O overlay do perfil por cima da fundação. */\n"
                         + "".join(f'@import "./profile/{n}";\n' for n in overlay))

    index = MODELO_INDEX.format(perfil=perfil, fontes=bloco_fontes,
                                temas=bloco_temas, overlay=bloco_overlay)
    if seco:
        print(f"[seco] escreveria {css / 'index.css'}")
    else:
        (css).mkdir(parents=True, exist_ok=True)
        (css / "index.css").write_text(index, encoding="utf-8")
    print(f"  · {rel_ui}/css/index.css")

    # -- 5. O ui.config.json, apontado para onde a UI ficou mesmo -----------
    if config:
        config["uiSource"] = rel_ui
        config["tokensSource"] = f"{rel_ui}/css"
        config["cssSource"] = f"{rel_ui}/css"
        base = config.get("basePrimitive")
        if isinstance(base, dict):
            base["allowedInside"] = [rel_ui]
        if seco:
            print(f"[seco] escreveria {alvo / 'ui.config.json'}")
        else:
            (alvo / "ui.config.json").write_text(
                json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("  · ui.config.json")

    print("\nA seguir:")
    if pacotes:
        print(f"  npm i @base-ui/react {' '.join(pacotes)}")
    else:
        print("  npm i @base-ui/react")
    print(f"  importar `{rel_ui}/css/index.css` no arranque da app")
    print(f"  python {skill / 'scripts' / 'audit_ui.py'} {alvo} --profile {perfil} --strict")
    return EXIT_OK


class _Parser(argparse.ArgumentParser):
    def error(self, message: str):
        self.print_usage(sys.stderr)
        print(f"erro de utilizacao: {message}", file=sys.stderr)
        raise SystemExit(EXIT_USO)


def main() -> int:
    ap = _Parser(description="Instala o design system e um perfil num projeto.")
    ap.add_argument("profile", nargs="?", default=None,
                    help="Perfil em profiles/<nome>/ (opcional; sem argumento usa assets/ui.config.json)")
    ap.add_argument("--target", default=".", help="Projeto destino (default: .)")
    ap.add_argument("--ui-dir", default=None,
                    help="Onde pôr a UI, relativo ao destino (default: src/ui, ou o que já existir)")
    ap.add_argument("--tailwind", action="store_true",
                    help="Inclui a ponte para Tailwind v4. Sem isto, só CSS.")
    ap.add_argument("--with-react", action="store_true",
                    help="Copia também o pack de componentes React (packs/react-components).")
    ap.add_argument("--dry-run", action="store_true", help="Simula, sem escrever")
    args = ap.parse_args()

    skill = Path(__file__).resolve().parents[1]
    alvo = Path(args.target).resolve()
    if not alvo.is_dir():
        print(f"Erro: destino '{alvo}' não é um directório", file=sys.stderr)
        return EXIT_ERRO
    return aplicar(skill, alvo, args.profile, args.dry_run, args.ui_dir, args.tailwind, args.with_react)


if __name__ == "__main__":
    sys.exit(main())
