# Migrar de `auditar-app` 2.3.x para `audit-app` universal

**Contexto.** A `auditar-app` do JustClip é a origem histórica deste
orquestrador. O motor genérico (`contrato-e-evidencia.md`, `relatorio.md`)
está agora aqui; o pack de gates específico do JustClip fica no repo JustClip
como `.claude/gates.json`. Este documento explica o que muda para quem
mantém o JustClip.

## Estado desejado

```
JustClip/                                    production-quality-ready/ (este plugin)
├── .claude/                                 ├── skills/audit-app/
│   ├── gates.json          ← lê             │   ├── SKILL.md
│   └── skills/                              │   ├── references/
│       ├── auditar-app/    ← congelada      │   │   ├── contrato-e-evidencia.md
│       │   (2.3.x fica     │   │   └── relatorio.md
│       │    viva até       │   ├── scripts/
│       │    migração       │   └── migration/
│       │    concluída)     │       └── from-auditar-app-2.3.md (este ficheiro)
│       ├── comecar-trabalho/  (adapter local de start-work)
│       ├── rever-mudanca/     (adapter local de review-change)
│       ├── fechar-trabalho/   (adapter local de close-work)
│       └── verify/            (adapter local de verify)
└── .audit/                                  (produzido pelos owners)
    ├── code-review-runtime/
    ├── design-pro/
    └── ...
```

## Coexistência durante a migração

Os dois orquestradores coexistem enquanto o pack de gates novo ainda não
fecha todos os `DIST-*`, `SEC-*`, `A11Y-*` que a `2.3.x` fecha hoje.
Regras:

- **`auditar-app` 2.3.x continua a produzir relatórios em
  `docs/auditorias/`** — nada é apagado, nada é editado. Os relatórios
  antigos ficam válidos porque nada da 2.3.x mudou.
- **`audit-app` universal produz relatórios em `docs/auditorias-v3/`**
  durante a migração, para não colidir com os antigos.
- **`Contract SHA-256` da 2.3.x fica fechado.** O motor extraído nasce em
  1.0.0 com `evidence-schema: 1.3.0`. Relatórios da 2.3.x mantêm o hash
  antigo; relatórios do audit-app universal têm hash novo.
- **Migração de auditoria completa** só quando o pack de gates novo tem
  cobertura equivalente à 2.3.x — auditado por diff entre dois relatórios
  para o mesmo commit.

## Mapa de correspondências (parcial)

Os módulos da `auditar-app` mapeiam para owners do plugin assim:

| Módulo da 2.3.x | Owner do plugin |
|---|---|
| `architecture` | `code-review-contract` |
| `rust` | `code-review-runtime` |
| `react` | `code-review-runtime` |
| `ipc` | `code-review-contract` |
| `security` | `security-audit` |
| `ui-ux` | `design-pro` (régua) + `ui-system` (instrumento) |
| `performance` | `performance-audit` |
| `tests` | `code-review-runtime` (subtema) |
| `persistence` | `reliability-audit` |
| `release` | `release-audit` |
| `compliance` | `commercial-readiness` (subtema `legal`) |
| `support` | `observability` |

## Baselines

`baselines/riscos-aceites.md`, `baselines/achados-resolvidos.md`,
`baselines/ultima-auditoria.md`, `baselines/evals-corridos.md` **ficam no
repo JustClip** dentro da `auditar-app` 2.3.x congelada. **Não migram** para
este plugin nem para o `audit-app` universal — são estado do projecto, não
contrato.

## Quando fechar a migração

Quando o `audit-app` universal, correndo com o `JustClip/.claude/gates.json`
gerado a partir do template `justclip.gates.json.template`, produzir um
relatório equivalente (em módulos cobertos e verdicts) ao último da 2.3.x
para o mesmo commit. Diferenças exigem justificação em `docs/DECISOES.md`
do JustClip antes de a 2.3.x ser removida.

## O que **não** migra

- `MIGRACAO.md` da 2.3.x — vive lá, não é útil aqui.
- `EVALS.md` da 2.3.x — vive lá.
- Referências específicas do JustClip (`rust-tauri.md`, `ipc-e-contratos.md`,
  etc.) — não são referências genéricas do motor. Ficam no repo JustClip
  como conteúdo dos adapters locais dos owners aplicáveis.
- `Contract SHA-256` da 2.3.x — não faz sentido no plugin novo, que usa
  `evidence-schema` para compatibilidade.
