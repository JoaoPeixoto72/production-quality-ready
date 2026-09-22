#!/usr/bin/env python3
"""Auditoria determinística do design system próprio.

Severidades:
  error -> falha em --strict (contrato violado, objetivamente verificável)
  warn  -> requer julgamento humano, não bloqueia
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

CODE_EXT = {".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte"}
STYLE_EXT = {".css", ".scss", ".sass", ".less"}
HTML_EXT = {".html", ".htm"}
SOURCE_EXT = CODE_EXT | STYLE_EXT | HTML_EXT

DEFAULT_IGNORED_DIRS = {
    ".git",
    ".claude",
    ".agents",
    ".wrangler",
    ".next",
    ".nuxt",
    ".svelte-kit",
    ".turbo",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "storybook-static",
    "vendor",
    "tests",
    "migrations",
}

HEX = re.compile(
    r"(?<![\w-])#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})(?![\w-])"
)
COLOR_FN = re.compile(
    r"\b(?:rgba?|hsla?|oklch|oklab|lab|lch|hwb|color)\s*\(", re.IGNORECASE
)
COLOR_MIX_OK = re.compile(r"color-mix\s*\(", re.IGNORECASE)
FONT_DECL = re.compile(
    r"""(?:font-family|fontFamily|--(?:ui-)?font[\w-]*)\s*:\s*([^;{}]*)""",
    re.IGNORECASE,
)
CUSTOM_PROP_DECLARATION = re.compile(r"--[\w-]+\s*:\s*.*?;", re.DOTALL)

GENERIC_FONTS = re.compile(r"\b(?:Inter|Roboto)\b", re.IGNORECASE)


def primary_font_is_generic(value: str) -> bool:
    """True only when Inter/Roboto is the *chosen* family: the first entry
    of the stack, after unwrapping var(--x, fallback). Roboto in the middle
    of `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, …` is a
    platform fallback, not a design decision, and is not flagged."""
    v = value.strip()
    # unwrap var(--font, <fallback-list>) -> <fallback-list>
    m = re.match(r"var\(\s*--[\w-]+\s*,\s*(.*)\)\s*$", v, re.DOTALL)
    if m:
        v = m.group(1)
    first = v.split(",", 1)[0].strip().strip("'\"")
    return bool(GENERIC_FONTS.fullmatch(first))

ARBITRARY_COLOR_UTILITY = re.compile(
    r"(?<![\w-])(?:bg|text|border|shadow|ring|from|via|to)-\[(?!var\(--)[^\]]+\]"
)
ARBITRARY_SPACE_UTILITY = re.compile(
    r"(?<![\w-])(?:p|px|py|pt|pb|pl|pr|m|mx|my|gap|space-[xy])-\[(?!var\(--)[^\]]+\]"
)

REMOTE_CSS_IMPORT = re.compile(
    r"""@import\s+(?:url\s*\()?\s*["']?\s*https?://""", re.IGNORECASE
)
REMOTE_URL = re.compile(r"""url\s*\(\s*["']?\s*https?://""", re.IGNORECASE)
REMOTE_LINK_TAG = re.compile(
    r"""<(?:link|script|img)\b[^>]*\b(?:href|src)\s*=\s*["']https?://""",
    re.IGNORECASE,
)
REMOTE_JS_RESOURCE = re.compile(
    r"""(?:\b(?:src|href)\s*=\s*["']https?://|\bfetch\s*\(\s*["']https?://|\bnew\s+FontFace\s*\([^,]+,\s*["']https?://)""",
    re.IGNORECASE,
)

DATA_UI = re.compile(r"""data-ui\s*=\s*["']([^"']+)["']""")
TRANSITION = re.compile(r"\b(?:transition|animation)(?:-[\w-]+)?\s*:")
REDUCED_MOTION = re.compile(r"@media\s*\([^)]*prefers-reduced-motion|\[data-reduce-motion")
BOOLEAN_STATE_SELECTOR = re.compile(
    r"""\[data-(pressed|disabled)\s*=\s*["'](?:true|false)["']\]""",
    re.IGNORECASE,
)

MODULE_SOURCE_PATTERNS = {
    "base-ui": re.compile(r"^@base-ui/react(?:$|/)", re.IGNORECASE),
    "base-ui-legacy": re.compile(r"^@base-ui-components/react(?:$|/)", re.IGNORECASE),
    "radix": re.compile(r"^(?:radix-ui|@radix-ui/)", re.IGNORECASE),
    "heroui": re.compile(r"^@heroui/", re.IGNORECASE),
}


@dataclass
class Finding:
    severity: str
    kind: str
    file: str
    line: int
    value: str
    message: str


@dataclass
class SlotUsage:
    """O que se sabe sobre os slots `data-ui` de um ficheiro.

    Os três eixos respondem a perguntas diferentes, e é por isso que não são um
    contador só: `counts` é o inventário que vai para o relatório, `emitted` é
    o que o design system promete no DOM, e `styled` é o que alguém se deu ao
    trabalho de desenhar. Um slot emitido e nunca estilizado é um componente
    que renderiza sem aspecto nenhum — e era o que passava despercebido.
    """

    counts: Counter = field(default_factory=Counter)
    #: slot -> (ficheiro, linha) da primeira vez que um componente **do design
    #: system** o emite. Só conta dentro de `ui_sources`: os `data-ui` que uma
    #: aplicação inventa são dela, e o sistema não responde por eles.
    emitted: dict[str, tuple[str, int]] = field(default_factory=dict)
    #: Slots que aparecem como selector em CSS, venha ele de onde vier — um
    #: projecto pode estilizar no seu próprio CSS um slot que o sistema emite.
    styled: set[str] = field(default_factory=set)

    def merge(self, other: "SlotUsage") -> None:
        self.counts.update(other.counts)
        for slot, origem in other.emitted.items():
            self.emitted.setdefault(slot, origem)
        self.styled |= other.styled


@dataclass
class AuditSettings:
    ui_sources: list[str]
    token_dirs: list[str]
    forbidden_ui_aliases: list[str]
    shadcn_alias_severity: str
    offline: bool
    config_path: str | None
    ignored_dirs: set[str]
    # quality.* flags from ui.config.json — default True (strict) when the key is absent.
    forbid_raw_brand_colors: bool = True
    forbid_generic_fonts: bool = True
    forbid_direct_external_ui_imports: bool = True
    require_focus_visible: bool = True


def is_inside(path: Path, root: Path, relative: str) -> bool:
    if not relative:
        return False
    try:
        path.resolve().relative_to((root / relative).resolve())
        return True
    except ValueError:
        pass
    try:
        path.resolve().relative_to(Path(relative).resolve())
        return True
    except ValueError:
        return False


def iter_files(root: Path, ignored_dirs: set[str] | None = None) -> Iterable[Path]:
    ignored = DEFAULT_IGNORED_DIRS if ignored_dirs is None else ignored_dirs
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if any(part in ignored for part in relative_parts[:-1]):
            continue
        if path.suffix.lower() in SOURCE_EXT:
            yield path


def strip_block_comments(content: str) -> list[str]:
    out, in_comment = [], False
    for line in content.splitlines():
        res, i = [], 0
        while i < len(line):
            if in_comment:
                j = line.find("*/", i)
                if j == -1:
                    break
                in_comment = False
                i = j + 2
            else:
                j = line.find("/*", i)
                if j == -1:
                    res.append(line[i:])
                    break
                res.append(line[i:j])
                i = j + 2
                in_comment = True
        out.append("".join(res))
    return out


def strip_html_comments(content: str) -> str:
    def repl(match):
        return "\n" * match.group(0).count("\n")
    return re.sub(r"<!--.*?-->", repl, content, flags=re.DOTALL)


def strip_js_comments(content: str) -> str:
    out: list[str] = []
    i = 0
    n = len(content)
    quote: str | None = None
    while i < n:
        ch = content[i]
        nxt = content[i + 1] if i + 1 < n else ""
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(content[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in {'"', "'", "`"}:
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "/":
            while i < n and content[i] != "\n":
                out.append(" ")
                i += 1
            continue
        if ch == "/" and nxt == "*":
            i += 2
            out.append("  ")
            while i + 1 < n and not (content[i] == "*" and content[i + 1] == "/"):
                if content[i] == "\n":
                    out.append("\n")
                else:
                    out.append(" ")
                i += 1
            out.append("  ")
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def line_number(content: str, index: int) -> int:
    return content.count("\n", 0, index) + 1


def skip_ws_comments(source: str, index: int) -> int:
    i = index
    n = len(source)
    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""
        if ch.isspace():
            i += 1
            continue
        if ch == "/" and nxt == "/":
            i += 2
            while i < n and source[i] != "\n":
                i += 1
            continue
        if ch == "/" and nxt == "*":
            i += 2
            while i + 1 < n and not (source[i] == "*" and source[i + 1] == "/"):
                i += 1
            i += 2
            continue
        break
    return i


def read_identifier(source: str, index: int) -> tuple[str, int]:
    i = index
    while i < len(source) and (source[i].isalnum() or source[i] in {"_", "$"}):
        i += 1
    return source[index:i], i


def parse_string_literal(source: str, index: int) -> tuple[str, int] | None:
    if index >= len(source) or source[index] not in {'"', "'"}:
        return None
    quote = source[index]
    i = index + 1
    buf: list[str] = []
    while i < len(source):
        ch = source[i]
        if ch == "\\" and i + 1 < len(source):
            buf.extend([ch, source[i + 1]])
            i += 2
            continue
        if ch == quote:
            return "".join(buf), i + 1
        buf.append(ch)
        i += 1
    return None


def extract_module_sources(content: str) -> list[tuple[str, int]]:
    refs: list[tuple[str, int]] = []
    i = 0
    n = len(content)
    while i < n:
        ch = content[i]
        if ch in {'"', "'", "`"}:
            quote = ch
            i += 1
            while i < n:
                if content[i] == "\\":
                    i += 2
                    continue
                if content[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        if not (ch.isalpha() or ch in {"_", "$"}):
            i += 1
            continue
        ident, j = read_identifier(content, i)
        if ident not in {"import", "export", "require"}:
            i = j
            continue

        current = skip_ws_comments(content, j)
        if ident == "require":
            if current < n and content[current] == "(":
                current = skip_ws_comments(content, current + 1)
                parsed = parse_string_literal(content, current)
                if parsed:
                    source, end = parsed
                    refs.append((source, line_number(content, current)))
                    i = end
                    continue
            i = current + 1
            continue

        if ident == "import" and current < n and content[current] == "(":
            current = skip_ws_comments(content, current + 1)
            parsed = parse_string_literal(content, current)
            if parsed:
                source, end = parsed
                refs.append((source, line_number(content, current)))
                i = end
                continue
            i = current + 1
            continue

        parsed = parse_string_literal(content, current)
        if ident == "import" and parsed:
            source, end = parsed
            refs.append((source, line_number(content, current)))
            i = end
            continue

        search = current
        found = False
        while search < n:
            search = skip_ws_comments(content, search)
            if search >= n:
                break
            if content[search].isalpha() or content[search] in {"_", "$"}:
                word, end = read_identifier(content, search)
                if word == "from":
                    after = skip_ws_comments(content, end)
                    parsed = parse_string_literal(content, after)
                    if parsed:
                        source, end2 = parsed
                        refs.append((source, line_number(content, after)))
                        i = end2
                        found = True
                        break
                search = end
                continue
            search += 1
        if not found:
            i = max(i + 1, search)
    return refs


def split_top_level_commas(inner: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    start = 0
    for idx, ch in enumerate(inner):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(inner[start:idx].strip())
            start = idx + 1
    parts.append(inner[start:].strip())
    return [part for part in parts if part]


def _top_level_percentages(inner: str) -> list[float]:
    depth, buf = 0, []
    for ch in inner:
        if ch == "(":
            depth += 1
            buf.append(" ")
        elif ch == ")":
            depth -= 1
            buf.append(" ")
        else:
            buf.append(ch if depth == 0 else " ")
    return [
        float(m.group(1))
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*%", "".join(buf))
    ]


def color_mix_percent_findings(content: str, rel: str) -> list[Finding]:
    out: list[Finding] = []
    for m in COLOR_MIX_OK.finditer(content):
        i = m.end() - 1
        depth, j = 0, i
        while j < len(content):
            if content[j] == "(":
                depth += 1
            elif content[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        inner = content[i + 1:j]
        args = split_top_level_commas(inner)
        if len(args) != 3:
            continue
        pcts = _top_level_percentages(inner)
        if len(pcts) < 2:
            continue
        total = sum(pcts)
        line = line_number(content, m.start())
        if total > 100.01:
            out.append(Finding(
                "error",
                "color-mix-sum",
                rel,
                line,
                inner.strip()[:120],
                f"color-mix() com percentagens a somar {total:g}%: o browser normaliza os pesos para 100. A proporção relativa preserva-se, mas os pesos efectivos diferem dos valores declarados.",
            ))
        elif total < 99.99:
            out.append(Finding(
                "error",
                "color-mix-sum",
                rel,
                line,
                inner.strip()[:120],
                f"color-mix() com percentagens a somar {total:g}%: o resto ({100 - total:g}%) torna-se transparência. Somar 100 ou declarar uma só percentagem.",
            ))
    return out


def check_oklch_contrast_pairs(content: str, rel: str) -> list[Finding]:
    """
    Heurística matemática de luminância OKLCH (|L_fg - L_bg| < 0.40).
    WCAG 2.1 AA exige contraste de 4.5:1 para texto normal. No espaço OKLCH,
    uma diferença de luminância |L1 - L2| inferior a 0.40 indica risco de reprovação.
    """
    out: list[Finding] = []
    OKLCH_PAT = re.compile(
        r'(--[\w-]+)\s*:\s*oklch\s*\(\s*([0-9.]+%?)\s+([0-9.]+)\s+([0-9.]+)',
        re.IGNORECASE
    )
    VAR_PAT = re.compile(r'(--[\w-]+)\s*:\s*var\s*\(\s*--([\w-]+)\s*\)', re.IGNORECASE)
    BLOCK_PAT = re.compile(r'([^{}]+)\{([^{}]+)\}')

    SEMANTIC_PAIRS = [
        ('foreground', 'background'),
        ('primary-foreground', 'primary'),
        ('secondary-foreground', 'secondary'),
        ('success-foreground', 'success'),
        ('warning-foreground', 'warning'),
        ('danger-foreground', 'danger'),
        ('accent-foreground', 'accent'),
        ('muted-foreground', 'background'),
    ]

    for block_match in BLOCK_PAT.finditer(content):
        block_start = block_match.start()
        body = block_match.group(2)
        tokens: dict[str, tuple[float, int]] = {}

        if 'var(--white)' in body:
            tokens['white'] = (1.0, block_start)
        if 'var(--black)' in body:
            tokens['black'] = (0.0, block_start)

        for m in OKLCH_PAT.finditer(body):
            name = m.group(1).lstrip('-')
            val_str = m.group(2)
            try:
                val = float(val_str.rstrip('%')) / 100.0 if '%' in val_str else float(val_str)
                if val > 1.0:
                    val /= 100.0
                line_no = line_number(content, block_start + m.start())
                tokens[name] = (val, line_no)
            except ValueError:
                continue

        for _ in range(3):
            for m in VAR_PAT.finditer(body):
                name = m.group(1).lstrip('-')
                ref = m.group(2)
                if ref in tokens and name not in tokens:
                    line_no = line_number(content, block_start + m.start())
                    tokens[name] = (tokens[ref][0], line_no)

        for fg, bg in SEMANTIC_PAIRS:
            if fg in tokens and bg in tokens:
                l_fg, fg_line = tokens[fg]
                l_bg, _ = tokens[bg]
                delta = abs(l_fg - l_bg)
                if delta < 0.40:
                    severity = "error" if (delta < 0.30 and fg in ("foreground", "primary-foreground")) else "warn"
                    out.append(Finding(
                        severity,
                        "oklch-contrast-low",
                        rel,
                        fg_line,
                        f"--{fg} (L={l_fg:.2f}) vs --{bg} (L={l_bg:.2f})",
                        f"Contraste OKLCH insuficiente entre '--{fg}' (L={l_fg:.2f}) e '--{bg}' (L={l_bg:.2f}): delta={delta:.2f} < 0.40 (risco de violação WCAG AA 4.5:1).",
                    ))
    return out


def css_custom_property_line_ranges(content: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for m in CUSTOM_PROP_DECLARATION.finditer(content):
        ranges.append((line_number(content, m.start()), line_number(content, m.end())))
    return ranges


def line_in_ranges(line: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= line <= end for start, end in ranges)


def extract_css_blocks(content: str, offset: int = 0) -> list[tuple[str, str, int]]:
    blocks: list[tuple[str, str, int]] = []
    i = 0
    start = 0
    while i < len(content):
        if content[i] == "{":
            selector = content[start:i].strip()
            depth = 1
            j = i + 1
            while j < len(content) and depth > 0:
                if content[j] == "{":
                    depth += 1
                elif content[j] == "}":
                    depth -= 1
                j += 1
            body = content[i + 1:j - 1]
            block_line = line_number(content, i) + offset - 1
            if selector:
                blocks.append((selector, body, block_line))
            blocks.extend(extract_css_blocks(body, block_line))
            start = j
            i = j
            continue
        i += 1
    return blocks


def has_top_level_box_shadow(body: str) -> bool:
    """True when a :focus block *draws* a ring with box-shadow.
    `box-shadow: none` (a reset that removes a ring) is not a ring."""
    depth = 0
    for decl in _top_level_declarations(body):
        name, _, value = decl.partition(":")
        if name.strip().lower() != "box-shadow":
            continue
        v = value.strip().lower().replace("!important", "").strip()
        if v in ("none", "initial", "unset", "inherit", ""):
            continue
        return True
    return False


def _top_level_declarations(body: str) -> list[str]:
    out: list[str] = []
    depth = 0
    cur: list[str] = []
    for ch in body:
        if ch == "{":
            depth += 1
            continue
        if ch == "}":
            depth -= 1
            continue
        if depth > 0:
            continue
        if ch == ";":
            out.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    if "".join(cur).strip():
        out.append("".join(cur))
    return out


def classify_module_source(source: str) -> str | None:
    for system, pattern in MODULE_SOURCE_PATTERNS.items():
        if pattern.search(source):
            return system
    return None


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        sys.stderr.write(f"Erro: Falha ao ler ficheiro JSON '{path}': {e}\n")
        sys.exit(2)


def resolve_settings(args: argparse.Namespace, root: Path) -> AuditSettings:
    config_path: Path | None = None
    if args.config:
        candidate = Path(args.config)
        if candidate.is_file():
            config_path = candidate.resolve()
        elif (root / candidate).is_file():
            config_path = (root / candidate).resolve()
        else:
            sys.stderr.write(f"Erro: Ficheiro de configuração explícito '--config {args.config}' não encontrado.\n")
            sys.exit(2)
    elif getattr(args, "profile", None):
        prof = args.profile.strip()
        candidates = [
            root / "profiles" / prof / "ui.config.json",
            root / "ui.config.json",
            Path(__file__).resolve().parents[1] / "profiles" / prof / "ui.config.json",
            root / f"ui.config.{prof}.json",
        ]
        for c in candidates:
            if c.is_file():
                config_path = c.resolve()
                break
        if not config_path:
            sys.stderr.write(f"Erro: Configuração para o perfil '--profile {prof}' não encontrada.\n")
            sys.exit(2)
    else:
        candidate = root / "ui.config.json"
        if candidate.is_file():
            config_path = candidate.resolve()

    config = load_json(config_path) if config_path else {}
    base_primitive = config.get("basePrimitive", {}) if isinstance(config, dict) else {}
    quality = config.get("quality", {}) if isinstance(config, dict) else {}
    migration = config.get("migration", {}) if isinstance(config, dict) else {}

    config_ui_sources: list[str] = []
    allowed_inside = base_primitive.get("allowedInside")
    if isinstance(allowed_inside, list):
        config_ui_sources.extend(str(v) for v in allowed_inside if v)
    if config.get("uiSource"):
        config_ui_sources.append(str(config["uiSource"]))

    config_token_dirs: list[str] = []
    for key in ("tokensSource", "cssSource"):
        if config.get(key):
            config_token_dirs.append(str(config[key]))

    default_ui_sources = ["packages/ui-react/src"]
    if (root / "assets").is_dir():
        default_ui_sources.append("assets")
    for p in root.glob("profiles/*/assets"):
        if p.is_dir():
            default_ui_sources.append(str(p.relative_to(root)).replace("\\", "/"))

    default_token_dirs = ["packages/ui-tokens/src", "packages/ui-css/src"]
    if (root / "assets" / "css").is_dir():
        default_token_dirs.append("assets/css")
    for p in root.glob("profiles/*/assets/css"):
        if p.is_dir():
            default_token_dirs.append(str(p.relative_to(root)).replace("\\", "/"))

    valid_config_token_dirs = [d for d in config_token_dirs if (root / d).exists() or Path(d).exists()]
    token_dirs = args.token_dir or valid_config_token_dirs or default_token_dirs

    valid_config_ui_sources = [d for d in config_ui_sources if (root / d).exists() or Path(d).exists()]
    ui_sources = args.ui_source or valid_config_ui_sources or default_ui_sources

    config_aliases = migration.get("legacyUiAliases", []) if isinstance(migration, dict) else []
    forbidden_ui_aliases = args.forbidden_ui_alias or list(config_aliases or [])
    offline = bool(config.get("offline")) or bool(quality.get("forbidRemoteFontLoading"))

    def flag(name: str, default: bool = True) -> bool:
        v = quality.get(name) if isinstance(quality, dict) else None
        return default if v is None else bool(v)

    ignored_dirs = set(DEFAULT_IGNORED_DIRS)
    ignored_dirs.update(args.ignore_dir or [])

    cfg_disp = None
    if config_path:
        try:
            cfg_disp = str(config_path.relative_to(root)).replace("\\", "/")
        except ValueError:
            cfg_disp = str(config_path).replace("\\", "/")

    return AuditSettings(
        ui_sources=ui_sources,
        token_dirs=token_dirs,
        forbidden_ui_aliases=forbidden_ui_aliases,
        shadcn_alias_severity=args.shadcn_alias_severity,
        offline=offline,
        config_path=cfg_disp,
        ignored_dirs=ignored_dirs,
        forbid_raw_brand_colors=flag("forbidRawBrandColorsInApplications"),
        forbid_generic_fonts=flag("forbidGenericFonts"),
        forbid_direct_external_ui_imports=flag("forbidDirectExternalUiImports"),
        require_focus_visible=flag("requireFocusVisible"),
    )


def scan(path: Path, root: Path, settings: AuditSettings):
    findings: list[Finding] = []
    slots = SlotUsage()

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return findings, slots, False, False

    rel = str(path.relative_to(root))
    ext = path.suffix.lower()
    in_ui_source = any(is_inside(path, root, src) for src in settings.ui_sources)
    in_tokens = any(is_inside(path, root, token_dir) for token_dir in settings.token_dirs)

    stripped_css_lines = strip_block_comments(content)
    body_css = "\n".join(stripped_css_lines)
    js_without_comments = strip_js_comments(content) if ext in CODE_EXT else content
    html_without_comments = strip_html_comments(content) if ext in HTML_EXT else content
    has_transition = ext in STYLE_EXT and bool(TRANSITION.search(body_css))
    has_reduced = bool(REDUCED_MOTION.search(body_css if ext in STYLE_EXT else content))

    raw_color_sev = "error" if settings.forbid_raw_brand_colors else "warn"

    if ext in CODE_EXT:
        for source, source_line in extract_module_sources(js_without_comments):
            system = classify_module_source(source)
            if system:
                if system == "base-ui" and in_ui_source:
                    continue
                findings.append(Finding(
                    "error" if settings.forbid_direct_external_ui_imports else "warn",
                    "external-ui-import",
                    rel,
                    source_line,
                    source,
                    f"Import directo de {system} fora da fronteira do package UI.",
                ))
            for alias in settings.forbidden_ui_aliases:
                normalized = alias.rstrip("/")
                if normalized and re.search(rf"^{re.escape(normalized)}(?:$|/)", source):
                    findings.append(Finding(
                        settings.shadcn_alias_severity,
                        "legacy-ui-alias",
                        rel,
                        source_line,
                        source,
                        f"Import via alias legado `{normalized}/*`. Confirmar se aponta para UI antiga a migrar ou para o package UI canónico.",
                    ))

        for n, line in enumerate(js_without_comments.splitlines(), start=1):
            for slot in DATA_UI.findall(line):
                slots.counts[slot] += 1
                if in_ui_source:
                    slots.emitted.setdefault(slot, (rel, n))
            for m in ARBITRARY_COLOR_UTILITY.finditer(line):
                findings.append(Finding(raw_color_sev, "arbitrary-color-utility", rel, n, m.group(0), "Cor arbitrária em utility. Usar um token semântico."))
            for m in ARBITRARY_SPACE_UTILITY.finditer(line):
                findings.append(Finding("warn", "arbitrary-space-utility", rel, n, m.group(0), "Espaçamento arbitrário. Confirmar se é cálculo estrutural local (permitido) ou devia ser token."))
            if re.search(r"\bstyle\s*=\s*\{\{", line):
                findings.append(Finding("warn", "inline-style", rel, n, line.strip()[:160], "Style inline. Confirmar que é valor dinâmico e não uma decisão de tema."))
            if settings.offline and REMOTE_JS_RESOURCE.search(line):
                findings.append(Finding("error", "remote-resource", rel, n, line.strip()[:160], "Recurso remoto proibido pela configuração actual da UI (offline / sem assets remotos)."))

    if ext in STYLE_EXT:
        allowed_token_ranges = css_custom_property_line_ranges(body_css) if in_tokens else []
        for n, line in enumerate(stripped_css_lines, start=1):
            for slot in DATA_UI.findall(line):
                slots.counts[slot] += 1
                slots.styled.add(slot)
            for m in BOOLEAN_STATE_SELECTOR.finditer(line):
                findings.append(Finding("error", "boolean-state-selector", rel, n, m.group(0), "Os atributos de estado booleanos do Base UI são renderizados sem valor: usar [data-pressed] em vez de [data-pressed=\"true\"]."))
            for m in HEX.finditer(line):
                if in_tokens and line_in_ranges(n, allowed_token_ranges):
                    continue
                findings.append(Finding(raw_color_sev, "raw-hex", rel, n, m.group(0), "Cor hexadecimal crua. O sistema usa tokens e mistura em oklch/oklab."))
            if settings.offline and (REMOTE_CSS_IMPORT.search(line) or REMOTE_URL.search(line)):
                findings.append(Finding("error", "remote-resource", rel, n, line.strip()[:160], "Recurso remoto proibido pela configuração actual da UI (offline / sem assets remotos)."))

        for m in COLOR_FN.finditer(body_css):
            if m.group(0).lower().startswith("color-mix"):
                continue
            match_line = line_number(body_css, m.start())
            if in_tokens and line_in_ranges(match_line, allowed_token_ranges):
                continue
            findings.append(Finding(raw_color_sev, "raw-color-function", rel, match_line, m.group(0), "Função de cor crua fora da camada de tokens. Usar token ou derivar com color-mix()."))

        findings.extend(color_mix_percent_findings(body_css, rel))
        findings.extend(check_oklch_contrast_pairs(body_css, rel))
        for selector, block_body, block_line in extract_css_blocks(body_css):
            if ":focus" not in selector:
                continue
            if has_top_level_box_shadow(block_body):
                findings.append(Finding("error" if settings.require_focus_visible else "warn", "focus-box-shadow", rel, block_line, selector[:120], "Anel de foco por box-shadow. Preferir outline com outline-offset; em forced-colors o box-shadow é suprimido."))

    if ext in HTML_EXT:
        for n, line in enumerate(html_without_comments.splitlines(), start=1):
            for slot in DATA_UI.findall(line):
                slots.counts[slot] += 1
                if in_ui_source:
                    slots.emitted.setdefault(slot, (rel, n))
            if settings.offline and (REMOTE_LINK_TAG.search(line) or REMOTE_CSS_IMPORT.search(line) or REMOTE_URL.search(line)):
                findings.append(Finding("error", "remote-resource", rel, n, line.strip()[:160], "Recurso remoto proibido pela configuração actual da UI (offline / sem assets remotos)."))

    if ext in SOURCE_EXT:
        body = body_css if ext in STYLE_EXT else (html_without_comments if ext in HTML_EXT else js_without_comments)
        for m in FONT_DECL.finditer(body):
            value = m.group(1)
            if primary_font_is_generic(value):
                findings.append(Finding("error" if settings.forbid_generic_fonts else "warn", "generic-font", rel, line_number(body, m.start()), value.strip()[:120], "Inter/Roboto como família primária são defaults genéricos de output gerado. Escolher uma família deliberada para o projecto (como fallback do sistema são aceites)."))

    return findings, slots, has_transition, has_reduced


def main() -> int:
    parser = argparse.ArgumentParser(description="Auditoria do design system próprio.")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--repo", default=None, help="Directório raiz (alias para positional root).")
    parser.add_argument("--out", default=None, help="Directório/ficheiro de saída markdown (alias para --markdown-output).")
    parser.add_argument("--config", default=None, help="Path explícito para ui.config.json.")
    parser.add_argument("--profile", default=None, help="Nome do perfil ativo em profiles/<nome>/ para carregar a sua configuração.")
    parser.add_argument("--ui-source", action="append", default=None, help="Onde imports privados de Base UI são permitidos. Repetível.")
    parser.add_argument("--token-dir", action="append", default=None, help="Directórios onde primitives de cor podem ser declarados. Repetível.")
    parser.add_argument("--json-output", default="ui-audit.json")
    parser.add_argument("--markdown-output", default="ui-audit.md")
    parser.add_argument("--strict", action="store_true", help="Exit code 1 se existir qualquer finding 'error'.")
    parser.add_argument("--forbidden-ui-alias", action="append", default=None, help="Alias legado de UI a sinalizar (ex.: @/components/ui). Repetível.")
    parser.add_argument("--shadcn-alias-severity", choices=["error", "warn"], default="warn", help="Severidade para aliases legacy de UI. Default: warn.")
    parser.add_argument("--ignore-dir", action="append", default=None, help="Nome de directório adicional a ignorar durante a auditoria. Repetível.")
    args = parser.parse_args()

    target_root = args.repo if args.repo is not None else args.root
    root = Path(target_root).resolve()
    if not root.is_dir():
        print(f"Root inválido: {root}", file=sys.stderr)
        return 2

    if args.out:
        args.markdown_output = args.out

    settings = resolve_settings(args, root)

    findings: list[Finding] = []
    slots = SlotUsage()
    scanned = 0
    motion_files: list[str] = []
    any_reduced_motion = False

    for path in iter_files(root, ignored_dirs=settings.ignored_dirs):
        local_findings, local_slots, has_transition, has_reduced = scan(path, root, settings)
        scanned += 1
        findings.extend(local_findings)
        slots.merge(local_slots)
        if path.suffix.lower() in STYLE_EXT:
            if has_transition:
                motion_files.append(str(path.relative_to(root)))
            if has_reduced:
                any_reduced_motion = True

    if scanned == 0:
        findings.append(Finding("error", "no-files-scanned", "<projecto>", 0, str(root), "Nenhum ficheiro suportado foi analisado."))

    # Slots que o design system promete no DOM e que ninguem desenha.
    #
    # A distincao entre os dois casos e' o que faz esta regra valer alguma
    # coisa. Um slot solto por estilizar e' muitas vezes deliberado: o contrato
    # `data-ui` existe **para** dar ganchos a quem tema, e nem todos precisam
    # de aspecto de fabrica. Mas um componente em que **nenhum** slot esta
    # estilizado nao e' um gancho — e' um componente que renderiza sem aspecto
    # nenhum. Foi assim que oito componentes inteiros (badge, card, popover,
    # select, switch, table, tabs e tooltip) sairam sem uma linha de CSS: o
    # auditor via os slots existirem e dava-os por bons.
    #
    # So se aplica ao que sai de `ui_sources`: os `data-ui` que uma aplicacao
    # inventa sao dela, e o sistema nao responde por eles.
    por_ficheiro: dict[str, list[tuple[str, int]]] = {}
    for slot, (ficheiro, linha) in slots.emitted.items():
        por_ficheiro.setdefault(ficheiro, []).append((slot, linha))

    for ficheiro, emitidos in sorted(por_ficheiro.items()):
        sem_estilo = sorted(s for s, _ in emitidos if s not in slots.styled)
        if not sem_estilo:
            continue
        if len(sem_estilo) == len(emitidos):
            primeira = min(linha for _, linha in emitidos)
            findings.append(Finding(
                "error",
                "unstyled-component",
                ficheiro,
                primeira,
                ", ".join(f'data-ui="{s}"' for s in sem_estilo),
                "Nenhum dos slots deste componente esta estilizado: ele "
                "renderiza sem aspecto nenhum. Dar-lhe CSS na camada ui.core.",
            ))
            continue
        for slot in sem_estilo:
            linha = next(l for s, l in emitidos if s == slot)
            findings.append(Finding(
                "warn",
                "unstyled-slot",
                ficheiro,
                linha,
                f'data-ui="{slot}"',
                "Slot emitido e nunca estilizado. Confirmar que e' um gancho "
                "deliberado para quem tema, e nao um esquecimento.",
            ))

    if motion_files and not any_reduced_motion:
        findings.append(Finding("error", "missing-reduced-motion", "<projecto>", 0, f"{len(motion_files)} ficheiro(s) com transições", "Existem transições ou animações mas nenhuma regra funcional de reduced motion no projecto."))

    errors = [f for f in findings if f.severity == "error"]
    warns = [f for f in findings if f.severity == "warn"]
    report = {
        "root": str(root),
        "config_used": settings.config_path,
        "ui_sources": settings.ui_sources,
        "token_dirs": settings.token_dirs,
        "offline": settings.offline,
        "forbidden_ui_aliases": settings.forbidden_ui_aliases,
        "files_scanned": scanned,
        "error_count": len(errors),
        "warn_count": len(warns),
        "summary": dict(sorted(Counter(f.kind for f in findings).items())),
        "stable_ui_slots": dict(slots.counts.most_common()),
        "findings": [asdict(f) for f in findings],
    }

    Path(args.json_output).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# UI audit",
        "",
        f"- Root: `{root}`",
        f"- Config: `{settings.config_path}`" if settings.config_path else "- Config: nenhuma",
        f"- Ficheiros analisados: {scanned}",
        f"- Errors: {len(errors)}",
        f"- Warnings: {len(warns)}",
        "",
        "## Resumo",
        "",
    ]
    lines += [f"- `{k}`: {v}" for k, v in report["summary"].items()] or ["- Sem ocorrências."]
    lines += ["", "## Slots estáveis", ""]
    lines += [f"- `{k}`: {v}" for k, v in slots.counts.most_common()] or ["- Nenhum `data-ui` estático encontrado."]

    for title, group in (("Errors", errors), ("Warnings", warns)):
        lines += ["", f"## {title}", ""]
        if not group:
            lines.append("Nenhum.")
            continue
        for finding in group:
            lines += [
                f"- `{finding.kind}` — `{finding.file}:{finding.line}`",
                f"  - Valor: `{finding.value}`",
                f"  - Nota: {finding.message}",
            ]

    Path(args.markdown_output).write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Analisados {scanned} ficheiros.")
    print(f"{len(errors)} errors, {len(warns)} warnings.")
    print(f"JSON: {args.json_output}")
    print(f"Markdown: {args.markdown_output}")

    if args.strict and errors:
        print(f"Strict falhou: {len(errors)} errors.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
