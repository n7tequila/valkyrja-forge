# Valkyrja Forge

**English** | [简体中文](README.zh-CN.md)

A trio of shared Codex and Claude Code skills that turn loose requirement discussions into traceable AI-written code — three governance layers: product contracts (PRD), technical contracts (architecture), and verifiable delivery (OpenSpec).

The core claim: **AI participates in the whole loop — from gathering requirements to writing code — but every step stays auditable, and product semantics never get quietly rewritten.**

---

## Why this exists

Handing an AI a requirements document and telling it to start coding runs into the same three problems every time:

1. **Conversation is not memory.** End the session and every conclusion you reached evaporates. Next time you start over.
2. **AI silently fills the gaps.** Where a requirement is vague, the model tends to assume a plausible answer and keep going rather than stopping to ask — so product semantics get rewritten without anyone noticing.
3. **"Done" doesn't mean complete.** The feature works, but whether that one security requirement or performance target actually landed is a question nothing can answer.

This workflow solves the first with the **filesystem**, the second with **privileged-action handshakes**, and the third with a **bidirectional traceability chain**.

---

## The pipeline

```
Loose discussion (human + AI, many rounds)
      │
      │  valkyrja-prd
      ▼
Released PRD  ──────────────────── the product API: the only thing downstream may consume
      │
      │            tech discussion ── valkyrja-arch ──→ docs/architecture/
      │                        (ADEC decisions · adopted conventions · shared contracts)
      │  valkyrja-spec                     │ consumed by design.md (依据: ADEC-*)
      ▼                                    ▼
Requirement Baseline (per-requirement rulings on how it lands)
      │
      ▼
Change decomposition ──→ OpenSpec change (proposal / specs / design / tasks)
      │
      │  official OpenSpec: apply → verify
      ▼
trace (PRD ↔ spec reconciliation) → archive
      │
      ▼
openspec/specs/  (source of truth for what the system does today)
```

The traceability chain is the thread running through all of it:

```
RN / DEC  →  PRD's REQ/BR/SEC/NFR  →  OpenSpec Requirement's Sources:  →  main spec  →  code
```

Any requirement can be traced backward to *why it exists*, and any released requirement forward to *whether it shipped*.

---

## The three skills

| Skill | Responsibility | Status |
|---|---|---|
| **valkyrja-prd** | Discuss / decide / import / synthesize / release a PRD (the WHAT) | Proven end-to-end on a real project |
| **valkyrja-arch** | Technical decisions (ADEC) / adopted conventions / shared interface contracts (the foundation of HOW) | First real adopt / decide / contract / publish cycle completed |
| **valkyrja-spec** | Consume the Released PRD plus the technical foundation, drive the OpenSpec loop | Completed its first full real-project loop, archive and V6 ledger included |

### valkyrja-prd

Governs loose discussion into traceable product state. Ten actions: `discuss`, `decide`, `import`, `prototype`, `bootstrap`, `status`, `synthesize`, `release`, `check`, `view` — `prototype` ingests externally-made system prototypes (Figma exports, generated HTML) into a governed genre: machine-checked against the release's UI requirements, human-reviewed, then blessed as the visual baseline via a DEC. You never type an action name — the skill routes on what you say. `decide` and `release` are privileged and require explicit human confirmation. `view` writes a human-readable digest — the PRD with its decisions, discussion history and open items in one file, by default `docs/product/views/<slug>.md` — on demand only; it is never a requirement source.

Workspace layout:

```
docs/product/initiatives/<slug>/
├── STATUS.md              # the only derived cache; everything else is recomputed
├── requirements/          # RN-*   normalized requirement notes
├── discussions/           # DISC-* one file per topic, append-only
├── decisions/             # DEC-*  one file per decision
├── tech-memos/            # TM-*   technical notes (never create requirements)
├── prototype/             # system prototype: original/vN raw + vN blessed baseline pack
├── others/originals/      # external source files, read-only
└── prd/
    ├── current.md         # regenerable draft
    └── releases/vX.Y.md   # frozen on release; the only downstream-consumable API
```

### valkyrja-arch

The technical-contract layer, structurally identical to valkyrja-prd (discuss → decide) but deciding engineering matters. Eight actions: `bootstrap`, `discuss`, `decide`, `adopt`, `contract`, `status`, `check`, `publish` — `bootstrap` is the entry flow that detects existing technical facts, reads product-side constraints, and drives the foundational decisions (tech stack, repo layout) **before the first apply**. The boundary test is **acceptance observability**: anything acceptance-testable belongs to the product side; engineering-internal constraints are ruled here as ADECs. Output lands in `docs/architecture/` (decisions / adopted convention copies / versioned shared contracts / a common-object inventory / a rule-candidate backlog).

Ships a **convention catalog** under `valk/skills/valkyrja-arch/references/conventions/`, organized on two axes (concern × stack), every entry carrying provenance and license fields. `adopt` drops a self-contained copy into the project and mints an ADEC recording the deltas. Entries are driven by gaps real projects actually hit; regression-backed rules take priority.

### valkyrja-spec

A governance layer. Standard propose / apply / archive are delegated to the official OpenSpec skills and CLI; this skill only does what they don't and shouldn't. Six actions:

| Action | Responsibility |
|---|---|
| `baseline` | Parse a release, rule on each requirement (direct / split / deferred / non-software / external / conflicted) |
| `decompose` | Decide the change breakdown, emit a handover sheet |
| `trace` | Bidirectional PRD ↔ spec reconciliation, **gates releases** (mandatory before apply and before archive) |
| `status` | Recomputed coverage ledger |
| `check` | Whole-workspace contract audit |
| `rebaseline` | Incremental baseline for a new release (digest comparison, five-state classification) |

Output lands in `docs/product/baselines/<DOMAIN>-vX.Y.md`.

The four verbs (propose / apply / verify / archive) run as a **shell**: gates first, confirmation in the middle, delegation to official OpenSpec last, automatic post-checks after — saying `next` walks the pipeline one step at a time without ever skipping a privileged confirmation.

> `trace` and the official `verify` check two different kinds of consistency:
> `trace` covers **PRD ↔ spec**, official `verify` covers **implementation code ↔ change artifacts**.
> They complement each other; neither substitutes for the other.

---

## Entry points

Codex has no command layer: invoke a skill by its registered name (or let the
opt-in-aware descriptions route natural language). With the plugin install the
names carry the plugin prefix:

```text
$valk:valkyrja-prd   let's talk about pausing the recording
$valk:valkyrja-arch  review the technical foundation
$valk:valkyrja-spec  can this change be archived?
```

With the copy installer the names are bare: `$valkyrja-prd`, `$valkyrja-arch`,
`$valkyrja-spec`. `/skills` lists what is actually registered. The protocol and all
confirmation gates are the same as in Claude Code.

Three entry points, namespaced for cohesion:

```
/valk:prd    <anything, in natural language>
/valk:arch   <anything, in natural language>
/valk:spec   <anything, in natural language>
```

They are deliberately thin — pure delegation with no routing logic of their own, so the intent-routing table inside each `SKILL.md` stays the single source of truth. Examples:

```
/valk:prd   let's talk about pausing the recording
   → routes to discuss

/valk:prd   ok, that's decided
   → routes to decide (privileged, requires handshake)

/valk:spec  can this change be archived?
   → routes to trace
```

> The short `/valk:*` aliases remain Claude Code-specific. Codex consumes the same
> `SKILL.md`, references, templates and trace script, with no duplicate skill tree.
> After the first governance files land, the skill proposes a guard block for the
> instruction file the active host actually reads — `AGENTS.md` for Codex; for Claude
> Code, `CLAUDE.md` if it exists, otherwise an existing `AGENTS.md` (Claude Code reads it
> then, so no `CLAUDE.md` is created), and a new `CLAUDE.md` only when neither exists —
> and writes it only after you confirm. The block text is the same for both hosts;
> everything outside it is untouched. The guard template holds the authoritative rule.

---

## Installation

### Codex

For local development, register this checkout explicitly and install either plugin:

```bash
codex plugin marketplace add /absolute/path/to/valkyrja-forge
codex plugin add valk@valkyrja-forge
codex plugin add valk-tools@valkyrja-forge  # optional, independent toolbox
```

The marketplace remains shared with Claude Code; each plugin also has a portable
root `plugin.json`. Local marketplace installation is a CLI path, not publication
to the public directory. Start a new session after installation or an upgrade.

For an offline, project-scoped installation into a **consuming product repo**:

```bash
scripts/install-skills.sh --harness codex --project /path/to/your-product-repo
scripts/install-skills.sh --harness codex --plugin valk-tools --system
```

Codex copies go to `<project>/.agents/skills/` or `~/.agents/skills/`, with no
command files. Pick either plugin installation or copies for a given host, not
both: duplicate registrations can silently select a stale version. An existing
Claude installation is left intact; no private catalog or project documents move.

### Claude Code plugin

This repo is a plugin marketplace (`.claude-plugin/`). Inside Claude Code:

```
/plugin marketplace add n7tequila/valkyrja-forge
/plugin install valk
```

Versioning, upgrades (`/plugin marketplace update`), enable/disable, and uninstall all come
from the official plugin mechanism. Under the plugin, skill names are namespaced
(e.g. `valk:valkyrja-spec`) and the slash commands are `/valk:prd|arch|spec`.

#### Second plugin: `valk-tools`

This marketplace hosts **two independent plugins**. `valk-tools` is a personal-workflow
toolbox — context handoff, Claude ↔ Codex work handoff, cross-forge PR drafting and a review-only refactoring gate —
that travels with the person rather than with the project:

```
/plugin install valk-tools
```

It carries its own version and installs, upgrades and uninstalls separately; it shares
this repo's git history with `valk` but not its release cadence, and the two have no
dependency on each other. It ships **skills only, no command layer** — invoke them
directly as `/valk-tools:context-handoff`, `/valk-tools:host-handoff`, `/valk-tools:merge-pr` and
`/valk-tools:refactor-review`.
See [valk-tools/README.md](valk-tools/README.md).

The fallback installer covers either plugin; select the toolbox with
`--plugin valk-tools`. The default remains `valk` on Claude Code for compatibility.

### Fallback path: copy-based installer (offline / no-git scenarios)

Skills install into your **target product repository** — this repo is only the source.
The examples below assume **cwd is the forge repo root** — omitting the directory
argument to `--project` would install into the forge itself; to target a product repo, pass
`--project <path>` or `cd` there first and call this script by absolute path:

```bash
# Install into a specific product repo (recommended form)
scripts/install-skills.sh --project /path/to/your-product-repo

# Or: enter the target repo first, then call the script from the forge checkout
cd /path/to/your-product-repo && /path/to/valkyrja-forge/scripts/install-skills.sh --project

# Install machine-wide (~/.claude/, applies to every project)
scripts/install-skills.sh --system

# Upgrade in place (old version backed up; --no-backup skips it)
scripts/install-skills.sh --system --force

# Install one skill only (slash commands are skipped in this mode,
# so a command can never point at a skill that isn't installed)
scripts/install-skills.sh --project /path/to/your-product-repo valkyrja-prd

# Preview and inspect
scripts/install-skills.sh --system --dry-run
scripts/install-skills.sh --system --list
```

Add `--harness codex` to these commands for Codex. Codex skill backups live under
`.agents/.valkyrja-backup/skills/`, outside the skill discovery tree.

Before installing, each skill is validated: `SKILL.md` must exist and its frontmatter must carry `name` and `description`. Anything failing that is skipped with an error, without affecting the rest. The script deliberately has no version tracking or uninstall — those are the plugin path's job, and the fallback does not re-invent them.

### Prerequisites

bash (installer), python3 >= 3.7 (the trace.py gate), and the OpenSpec CLI (below).
The installer and workflow are validated on macOS/Linux only; Windows users should prefer the plugin path.

### Requirements

`valkyrja-prd` has no external dependencies.

`valkyrja-spec` needs the [OpenSpec](https://github.com/Fission-AI/OpenSpec) CLI ≥ 1.9.0:

```bash
npm install -g @fission-ai/openspec
openspec init --tools claude    # run inside the target product repo
# Codex instead:
openspec init --tools codex
```

`openspec init` generates the official workflow skills according to your current profile. The official `core` profile **does not include `verify`**. For the full loop, use `openspec config profile` to select a custom workflow set including propose, apply, verify, sync, and archive, then run `openspec update` in the product repo. This is an explicit user configuration choice; the skill never silently changes a global profile. See [OpenSpec compatibility](valk/skills/valkyrja-spec/references/openspec-compatibility.md) for host-specific paths and calls.

---

## Design principles

These run through all three skills and explain every tradeoff in the design:

1. **The filesystem is memory; conversation is not.** Any conclusion not written to disk does not exist next session.
2. **Humans keep decision authority; AI only extracts and proposes.** Product decisions and releases are privileged actions requiring explicit confirmation. A hesitant phrasing counts as a leaning, not a decision.
3. **Never store what can be derived.** Hashes, counts, coverage, status are all recomputed, so records can't drift. The single exemption is `STATUS.md`, which holds minimal state and no statistics.
4. **IDs are never renumbered.** Structure is `TYPE-DOMAIN-NUMBER`. DOMAIN is a permanent namespace: frozen on first use, globally unique, and never version-flavored.
5. **WHAT is separate from HOW.** Requirement documents describe observable behavior only; implementation belongs to the downstream design layer. Technology names must never appear in acceptance scenarios — otherwise any refactor breaks the spec.
6. **Format contracts precede tooling.** Any format a machine will parse gets verified by hand first, then a parser is written against it — never the reverse.

---

## Repository layout

```
valkyrja-forge/
├── README.md / README.zh-CN.md / NOTICE.md (pointer; the authoritative notices ship with the catalog)
├── AGENTS.md                      # Codex pointer to the shared repository editing rules
├── CLAUDE.md                      # single authority for those rules (not a consumer guard)
├── .claude-plugin/marketplace.json # shared marketplace; register explicitly in Codex CLI
├── docs/design/                   # design records & evolution logs for all three skills (D-series ruling ledger)
├── scripts/install-skills.sh      # fallback installer (offline / no-git; the plugin is the primary path)
├── tests/                         # trace, installer and packaging regressions (not distributed)
├── evals/                         # model-backed behavior checks (not distributed)
├── scripts/check-sanitization.sh # D6 sanitization gate (private wordlist, pre-push/CI)
├── valk/
│   ├── plugin.json / .claude-plugin/plugin.json # portable / Claude manifests
│   ├── commands/                 # Claude-only short aliases
│   └── skills/
│       ├── valkyrja-prd/          # SKILL.md + templates/
│       ├── valkyrja-arch/         # SKILL.md + templates/ + convention catalog
│       └── valkyrja-spec/         # SKILL.md + templates/ + references/ + tools/trace.py
└── valk-tools/                    # independent manifests + four personal-workflow skills
```

---

## Status and next steps

- `valkyrja-prd` has been validated on a real project; the PRD it produced was good enough to feed straight into development.
- `valkyrja-spec` has been through several rounds of review and revision, and its format contracts are all empirically verified against OpenSpec (verified range [1.9, 1.10]: the `Sources:` line does not trip `validate`, survives the merge into the main spec, is machine-extractable, and nested capabilities archive under their full paths). **The full pipeline has completed its first real end-to-end run — archive, the first V6 eight-block ledger, and a full post-run review with fixes included.**

Planned:

- [x] First end-to-end run against a real PRD: baseline → decompose → propose → trace → apply → verify → trace → archive (archived 2026-08-21)
- [ ] Split `SKILL.md` into reference files (progressive disclosure)
- [ ] Push the purely deterministic checks (traceability, set reconciliation) down into scripts and CI
- [ ] CI rule forbidding edits to already-released `prd/releases/**`
- [x] Plugin-ized (`.claude-plugin/`, v0.9.0): versioning/upgrade/uninstall via the official mechanism, install.sh demoted to fallback
- [x] Codex adapter: shared skills, one host-neutral guard block, host-specific OpenSpec calls, portable manifests, tested copy installer; behavior checks via `claude plugin eval` and `evals/run_codex.py`. Behavior runs are evidence, not proof of a full Codex product lifecycle.

Current migration evidence and remaining gaps: [Codex migration assessment](docs/design/codex-migration.md).

---

## License

MIT
