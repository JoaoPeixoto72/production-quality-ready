# Contract and evidence

**Hierarchy.** This file is the **operational translation** of the plugin's
root `CONTRACTS.md` for whoever runs an audit. It is not authoritative: where
the two disagree, `CONTRACTS.md` wins and this file is the defect.

| Here | `CONTRACTS.md` |
|---|---|
| `CANDIDATE` / `CONFIRMED` / `DISMISSED` / `ACCEPTED_RISK` / `OUT_OF_SCOPE` | detection vocabulary (informal) |
| `PROVEN` / `CLEARED` / `UNPROVEN` / `NOT_APPLICABLE` | §3.1 `result:` — `FAIL` / `PASS` / `NOT_VERIFIED` / `NOT_APPLICABLE` |
| `COMPLETE` / `PARTIAL` / `BLOCKED (n/m)` | coverage §4.3 |
| evidence types (`EXECUTION` / `TEST` / `MEASUREMENT` / `READING` / …) | §3.4 `evidence[].kind` (`source` / `screenshot` / `log` / `measurement` / `command-output` / `external`) |

This file carries the decision logic (funnel, precedence, exclusions, declared
coverage); the data format lives in `CONTRACTS.md`. A skill that emits evidence
writes the `CONTRACTS.md` schema, not this vocabulary. Loaded by **every**
module `audit-app` orchestrates; the only reference that is never optional.

## Funnel: from candidate to finding

Whatever a grep, linter, scanner, subagent or hunch produces enters as
`CANDIDATE`. It rises to `CONFIRMED` only after answering five questions:

1. **Path** — which file and line? Read, not presumed.
2. **Trigger** — which real usage sequence reaches it? If the sequence cannot
   be described, it is a hypothesis, not a finding.
3. **Material consequence** — what happens to the user or the buyer? "Not
   idiomatic" is not a consequence; "loses the edited subtitles when exporting
   a project open for over an hour" is.
4. **Reach** — always, under specific conditions, or only in theory? On which
   platforms?
5. **Still there** — confirmed in the current code, not only in an earlier
   audit's memory.

Failing any → `DISMISSED` (with one line saying why), or a hypothesis labelled
as such at the end of the report, with no priority.

`ACCEPTED_RISK` only with a matching entry in `baselines/accepted-risks.md`
**and** its reopening conditions not met. If they are met, the risk reopens as
`CANDIDATE`.

## A documented decision does not close an obligation

A written decision (the comment beside the code, the line in the agent's map)
or a risk entry proves the condition is **conscious** and, where applicable,
**accepted**. It does not turn an unmet obligation into `CLEARED`: `CLEARED`
says the problematic condition is absent, and no decision makes it absent.

| Situation | Obligation state | Also recorded |
|---|---|---|
| The condition is met | `CLEARED` | — |
| Not met, no decision | `PROVEN` | finding |
| Not met, valid decision | `PROVEN` | `ACCEPTED_RISK` |
| Allowed alternative, met and proven | `CLEARED` | the alternative's evidence |
| Alternative only documented | `UNPROVEN` | decision not yet met |

This covers what usually appears justified instead of verified: missing CI,
`fmt`/`clippy` nobody runs, accepted advisories, missing logs or automated
tests, unmaintained dependencies. An accepted risk changes the verdict's
**aggregation** through its residual priority (`SKILL.md`), not the technical
reality recorded in the row.

## Evidence types

Strongest first:

| Type | What it is | Care |
|---|---|---|
| `EXECUTION` | Behaviour observed running the app or binary | Record command, environment, version, what was seen |
| `TEST` | A reproducible test that fails/passes because of this | It must fail for the right reason |
| `MEASUREMENT` | A number obtained with a declared method | Without baseline and workload, a number is not evidence |
| `STATIC_ANALYSIS` | A tool that analyses without running: typecheck, compiler, linter, grep, scanner | Worth what the tool guarantees and the declared [coverage](#method-coverage). With `PARTIAL` or `SAMPLE` it **never sustains a finding alone** |
| `READING` | Code read with the reasoning explained | Valid if a third party can verify the reasoning |
| `DOCUMENT` | `CLAUDE.md`/`AGENTS.md`, a code comment | Proves intent, not behaviour |
| `EXTERNAL_SOURCE` | Official docs of the installed version | See [external sources](#external-sources) |

## Method coverage

The evidence type says **how** one looked, not **how much**. Each row declares
both, and the second decides what the first can close:

| Coverage | Meaning |
|---|---|
| `COMPLETE` | Complete within the universe **declared in the note** — not "the files that seemed relevant" |
| `PARTIAL` | Part of the universe was not examined, and which part is known |
| `SAMPLE` | Some cases, picked for convenience or representativeness |

- `SAMPLE` **never closes** an obligation that demands universality ("no
  `unwrap` outside tests", "no missing key"). The best it yields is
  `UNPROVEN`, with what was seen in the note.
- `PARTIAL` does not yield `CLEARED` if the unexamined part could change the
  conclusion.
- `COMPLETE` requires the note to say **which universe** and **which
  exclusions**. Without that it is `PARTIAL` by another name.

A positive observation about a mechanism stays valid under `SAMPLE`; it just
does not close the obligation over occurrences nobody opened. When a tool
declares its own coverage, the row copies it; ignoring it invents coverage the
tool refused to give.

## Proving an absence

"X does not exist" is the easiest claim to write and the hardest to sustain: a
grep that finds nothing is equally silent when X is absent and when one looked
in the wrong place. An absence is a universal claim, so it **requires
`COMPLETE` coverage** — with `SAMPLE` or `PARTIAL` the result is `UNPROVEN`.

The note of an absence declares four things:

1. **Universe** — which files and extensions, from which root.
2. **Exclusions** — what was left out (`target/`, `node_modules/`, generated)
   and why.
3. **Terms** — what was searched. A dependency is searched in the manifest
   **and** the lockfile; a feature by every name it could have.
4. **What would escape** — names built by concatenation, macros, re-exports,
   dynamic calls, code in another language.

## Precedence

When two pieces of evidence disagree:

`EXECUTION` > `TEST` > `MEASUREMENT` > `STATIC_ANALYSIS` > `READING` >
`DOCUMENT` > `EXTERNAL_SOURCE`

Within one type, the wider coverage wins; one step apart, coverage breaks the
tie: a `STATIC_ANALYSIS` over a `SAMPLE` does not beat a `READING` that walked
the whole path. When a document says one thing and the code does another, the
code wins, and the divergence is itself a candidate.

## Confidence levels

Each finding declares one:

- `HIGH` — reproduced, or proven by two independent strong pieces of evidence.
- `MEDIUM` — code read and path identified, not reproduced.
- `LOW` — plausible inference from partial reading. Allowed in P2/P3. **Never
  sustains a `CONFIRMED` P0/P1**: a serious suspicion without proof goes to
  `PRECAUTIONARY ALERT` (`report.md`).

`HIGH` never compensates for lack of time.

## Unavailable tools

When a planned command is missing or fails:

1. Record the exact command and the exact error.
2. Mark the obligation `UNPROVEN` with that reason.
3. Apply the module reference's fallback, if any, and say it is a fallback
   (less coverage).
4. **Install nothing.**
5. **Do not turn the missing tool into a finding about the app.** `cargo-deny`
   absent on this machine is not the project's defect; CI never running it may
   be, and that is verified in CI.

## Avoiding false positives

- **Working directory.** Either run from the repo root with full paths, or
  enter the folder and use paths relative to it — never `cd src-tauri`
  followed by `src-tauri/src/...`. Each command in the report says where it ran.
- **Counts.** Never derive a number from `tail -5`. Use the tool's structured
  output or count explicitly; if no reliable way exists, say so.
- **Dead code vs code grep did not find.** Before calling something unused,
  search re-exports, dynamic calls, concatenated names, macros, tests, and the
  other side of the IPC.
- **Existing suppressions.** An `allow`, `eslint-disable` or tool baseline may
  be deliberate: read the comment beside it and the baselines first.
- **Platform differences.** A Windows-only problem is a finding with its
  platform declared.
- **Generated noise.** Ignore generated files, `target/`, `dist/`,
  `node_modules/` and automatic bindings, unless generation is the subject.

## External sources

- Prefer the project's official source (Tauri, React, Rust, the crate itself).
- **Confirm the version** read from the lockfile, not the latest release nor
  the one remembered.
- Cite the source and the date consulted.
- A version that cannot be confirmed makes it a hypothesis, said as such.
- An external recommendation is not a finding until the concrete defect it
  solves here is shown.

## Declaring exclusions

The report states, one sentence each: modules not requested; `NOT_APPLICABLE`
obligations and why; platforms not tested; areas where execution capability was
`STATIC` or `ASSISTED`; files or zones deliberately not read, and why. A
declared exclusion is honest; a silent one is how a buyer finds the problem
before the seller.

## Temporary artefacts, and the report

**Raw material** stays outside the repository, in `/tmp/audit-<YYYY-MM-DD>/`:

```
/tmp/audit-2026-09-06/
├── commands.log        # command, cwd, exit code, duration
├── outputs/            # full stdout/stderr of the tools
├── captures/           # screenshots, named after the captured state
└── measurements/       # raw performance data
```

**The report** goes to `docs/audits/YYYY-MM-DD-<scope>.md` and says where its
artefacts are. Writing rules (order relative to the Git comparison, never over
an earlier report) are in `SKILL.md`, read-only mode.

## Closing with verifiable coverage

"I audited what I could" is not an ending. End with:

1. The obligations table from `report.md`, one row per activated obligation,
   and `Checklist: X/Y` with a separate count for critical gates. The two
   verdict axes (product and coverage) are always reported together.
2. The `UNPROVEN` list, each with its reason.
3. The `NOT_APPLICABLE` list, each with its justification.
4. The `OUT_OF_SCOPE` detected, and the recommended module.
5. Residual risks: what is still unknown after this audit.

Empty first three lists in a `full` audit are suspicious and get re-examined.
