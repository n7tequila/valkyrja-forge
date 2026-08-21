# Valkyrja Forge

**English** | [简体中文](README.zh-CN.md)

A trio of Claude Code skills that turn loose requirement discussions into traceable AI-written code — three governance layers: product contracts (PRD), technical contracts (architecture), and verifiable delivery (OpenSpec).

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
| **valkyrja-spec** | Consume the Released PRD plus the technical foundation, drive the OpenSpec loop | Verified on a real project through the full pre-apply chain (baseline → rebaseline interlock) |

### valkyrja-prd

Governs loose discussion into traceable product state. Nine actions: `discuss`, `decide`, `import`, `prototype`, `bootstrap`, `status`, `synthesize`, `release`, `check` — `prototype` ingests externally-made system prototypes (Figma exports, generated HTML) into a governed genre: machine-checked against the release's UI requirements, human-reviewed, then blessed as the visual baseline via a DEC. You never type an action name — the skill routes on what you say. `decide` and `release` are privileged and require explicit human confirmation.

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

Ships a **convention catalog** under `skills/valkyrja-arch/references/conventions/`, organized on two axes (concern × stack), every entry carrying provenance and license fields. `adopt` drops a self-contained copy into the project and mints an ADEC recording the deltas. Entries are driven by gaps real projects actually hit; regression-backed rules take priority.

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

The three verbs (propose / apply / archive) run as a **shell**: gates first, confirmation in the middle, delegation to official OpenSpec last, automatic post-checks after — saying `next` walks the pipeline one step at a time without ever skipping a privileged confirmation.

> `trace` and the official `verify` check two different kinds of consistency:
> `trace` covers **PRD ↔ spec**, official `verify` covers **implementation code ↔ change artifacts**.
> They complement each other; neither substitutes for the other.

---

## Slash commands

Two entry points, namespaced for cohesion:

```
/valkyrja:prd    <anything, in natural language>
/valkyrja:arch   <anything, in natural language>
/valkyrja:spec   <anything, in natural language>
```

They are deliberately thin — pure delegation with no routing logic of their own, so the intent-routing table inside each `SKILL.md` stays the single source of truth. Examples:

```
/valkyrja:prd   let's talk about pausing the recording
   → routes to discuss

/valkyrja:prd   ok, that's decided
   → routes to decide (privileged, requires handshake)

/valkyrja:spec  can this change be archived?
   → routes to trace
```

> **Slash commands are Claude Code-specific.** They are a convenience layer, not the mechanism.
> The skills route on natural language by design, so on any other harness you can drop the commands
> entirely, place the `skills/` directories where that tool expects them, and everything still works —
> you just say "build the baseline" instead of `/valkyrja:spec build the baseline`.
> `SKILL.md` itself is plain Markdown with YAML frontmatter, a format many harnesses now consume.

---

## Installation

Skills install into your **target product repository** — this repo is only the source.

```bash
# Install into the current project (.claude/, shared via the repo)
scripts/install-skills.sh --project

# Install machine-wide (~/.claude/, applies to every project)
scripts/install-skills.sh --system

# Upgrade in place (old version is backed up to .backup/ automatically)
scripts/install-skills.sh --project --force

# Install one skill only (slash commands are skipped in this mode,
# so a command can never point at a skill that isn't installed)
scripts/install-skills.sh --project valkyrja-prd

# Preview and inspect
scripts/install-skills.sh --project --dry-run
scripts/install-skills.sh --project --list
```

Before installing, each skill is validated: `SKILL.md` must exist and its frontmatter must carry `name` and `description`. Anything failing that is skipped with an error, without affecting the rest.

### Requirements

`valkyrja-prd` has no external dependencies.

`valkyrja-spec` needs the [OpenSpec](https://github.com/Fission-AI/OpenSpec) CLI ≥ 1.9.0:

```bash
npm install -g @fission-ai/openspec
openspec init --tools claude    # run inside the target product repo
```

`openspec init` generates the official workflow skills according to your current profile. Note the official `core` profile **does not include `verify`** — and the full loop needs it. The skill's preflight check will tell you.

---

## Design principles

These run through both skills and explain every tradeoff in the design:

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
├── README.md / README.zh-CN.md / NOTICE.md
├── commands/valkyrja/             # slash-command namespace → /valkyrja:{prd,arch,spec}
├── docs/design/                   # design records & evolution logs for all three skills (D-series ruling ledger)
├── scripts/install-skills.sh      # installs skills + commands
└── skills/
    ├── valkyrja-prd/              # SKILL.md + templates/
    ├── valkyrja-arch/             # SKILL.md + templates/ + references/conventions/ (catalog)
    └── valkyrja-spec/             # SKILL.md + templates/ + references/
                                   #   + tools/trace.py (deterministic trace, ships with the skill; CI-gate exit code)
```

---

## Status and next steps

- `valkyrja-prd` has been validated on a real project; the PRD it produced was good enough to feed straight into development.
- `valkyrja-spec` has been through several rounds of review and revision, and its format contracts are all empirically verified against OpenSpec v1.9.0 (the `Sources:` line does not trip `validate`, survives the merge into the main spec, and is machine-extractable). **The full pipeline has not yet had a single real end-to-end run.**

Planned:

- [ ] First end-to-end run against a real PRD: baseline → decompose → propose → trace → apply → verify → trace → archive
- [ ] Split `SKILL.md` into reference files (progressive disclosure)
- [ ] Push the purely deterministic checks (traceability, set reconciliation) down into scripts and CI
- [ ] CI rule forbidding edits to already-released `prd/releases/**`
- [ ] Multi-harness adapters generated from `skills/` as the single source

---

## License

MIT
