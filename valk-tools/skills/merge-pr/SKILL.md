---
name: merge-pr
description: Draft or open a pull/merge request from one branch into another (e.g. develop into main). Accepts source and target branch as arguments, works with GitHub via gh CLI, and falls back to drafting title+body plus a direct compare/new-PR URL for self-hosted forges (Gitea/GitLab/Bitbucket) when gh isn't available or isn't authenticated for that host. Use when the user asks to "open a PR", "merge develop into main", "create a merge request", "帮我开个PR", "把 X 分支合并到主分支", or similar.
---

# Merge PR

Draft (and, when possible, actually create) a PR/MR that merges a source branch into a target branch. Works across git forges — GitHub, Gitea, GitLab, Bitbucket — by degrading gracefully when no CLI/API access is available.

## Arguments

`args` (optional): `<source-branch>` or `<source-branch> <target-branch>`.

- **Source omitted** → use the current branch (`git branch --show-current`).
- **Target omitted** → auto-detect the repo's main branch (see step 1).
- Both may be omitted — the skill infers as much as it safely can and only asks the user when inference is genuinely ambiguous.

## Steps

### 1. Resolve source & target branches

- Parse `args` for `<source> [target]`.
- If source omitted: `git branch --show-current`.
- If target omitted, try in order, first match wins:
  1. `git symbolic-ref refs/remotes/origin/HEAD` (strip `refs/remotes/origin/`)
  2. A branch literally named `main` on `origin`
  3. A branch literally named `master` on `origin`
  4. Repo docs: check root `CLAUDE.md` / `AGENTS.md` / `README.md` for an explicit "main branch" note (this codebase's own `CLAUDE.md` says so directly — respect it over guessing)
  5. If still ambiguous, use **AskUserQuestion** listing the candidate branches — do not guess silently.
- Confirm both branches exist on `origin`: `git ls-remote --heads origin <branch>`. If either is missing, stop and report — do not create a branch or push one into existence as a side effect.

### 2. Safety checks (never skip)

- `git fetch origin <source> <target>` to make sure comparisons use up-to-date remote refs, not stale local ones.
- `git log --oneline origin/<target>..origin/<source>` — if **empty**, tell the user there's nothing to merge (source is not ahead of target) and stop. Don't draft an empty PR.
- `git log --oneline origin/<source>..origin/<target>` — if **non-empty**, target has commits source doesn't (normal after prior merges, e.g. this repo's `Merge pull request ... from develop into main` commits). Mention it in the summary; it's informational, not a blocker.
- `git status --short` on the working tree — if dirty, note that uncommitted local changes exist and are **not** part of this PR (the PR is built from what's already pushed to `origin/<source>`, never from the working tree).
- **Never** push, force-push, create, or delete a branch as part of this skill. If the user's local `<source>` has commits not yet on `origin/<source>`, report that gap and ask whether to push — do not push silently (pushing is a "visible to others" action per the standing git safety rules).

### 3. Gather the real diff — full history, not just the tip

Per this environment's git-workflow rules: analyze the **full** commit range, not only the latest commit.

```bash
git log --format='%h %s' origin/<target>..origin/<source>
git log --format='%h %s%n%b' origin/<target>..origin/<source>   # with bodies, for drafting
git diff --stat origin/<target>...origin/<source>                # triple-dot: merge-base diff
```

If the range is very large (dozens of commits / many files), keep the drafted summary high-level (group by theme/feature) and cite the aggregate diffstat rather than enumerating every file.

### 4. Draft title and body

- **Detect conventions first**: read root `CLAUDE.md` / `AGENTS.md` / any `git-workflow.md` / `CONTRIBUTING.md` for commit-message language and format (e.g. this repo's convention is `<type>: <中文描述>` — Conventional Commits prefix + Chinese body). Mirror whatever the actual commit messages in the range are already using — don't impose a different language or style.
- **Title**:
  - Exactly one commit in range → reuse that commit's subject line verbatim.
  - Multiple commits → look for an existing multi-commit PR naming pattern in this repo's own merge history (`git log --merges --oneline origin/<target> | head -20`, read the PR titles referenced there). If a pattern exists (e.g. `"Develop -> Main YYYYMMDD"`), follow it using today's date. Otherwise default to `<source> → <target> YYYY-MM-DD`.
- **Body** — Markdown, matching the language of the commits:
  - `## Summary` — a synthesized, grouped bullet list of what's changing (by feature/theme, not a raw `git log` paste). Read each commit's full message (subject + body) to understand *why*, not just *what*, and reflect that.
  - `## Test plan` — a checklist. Mark items `[x]` only when the commit messages / session context genuinely indicate they were verified (tests run, build green, etc.); leave genuinely unverified items (deployment checks, manual QA, visual regression) as `[ ]` TODOs. Never mark something done that wasn't actually verified.

### 5. Determine how to actually open it

- Inspect `git remote get-url origin` to identify the forge:
  - Contains `github.com` → **GitHub**
  - Anything else with a `/pulls` or `/merge_requests`-style web UI → **self-hosted forge** (Gitea/Gogs/GitLab/Bitbucket) — do not assume GitHub-specific tooling works.
- **GitHub path**: if `gh` is installed (`command -v gh`) and authenticated (`gh auth status`), confirm with the user before creating (PR creation is visible to others — always confirm, even though this skill was explicitly invoked), then:
  ```bash
  gh pr create --base "<target>" --head "<source>" --title "<title>" --body "$(cat <<'EOF'
  <body>
  EOF
  )"
  ```
  Report the returned PR URL back to the user.
- **No `gh`, or `gh` not usable for this host** (the common case for self-hosted forges — confirmed in this session: no `gh` binary present at all): **do not** attempt to reconstruct API calls using credentials pulled from a credential helper (osxkeychain, etc.) — extracting stored secrets for a purpose the user didn't explicitly ask for is overreach. Instead:
  - Construct the human "compare / new PR" URL from the remote's web origin (strip `.git`, convert SSH to HTTPS form if needed):
    - GitHub: `https://github.com/<owner>/<repo>/compare/<target>...<source>?expand=1`
    - Gitea/Gogs (matches the `.../pulls/new/<branch>` link Gitea prints after `git push`): `<repo-web-url>/compare/<target>...<source>` (Gitea's compare view lets the target be picked explicitly; prefer it over `/pulls/new/<source>` alone since that form defaults target to the repo's default branch)
    - GitLab: `<repo-web-url>/-/merge_requests/new?merge_request[source_branch]=<source>&merge_request[target_branch]=<target>`
  - Output the URL plus the drafted title/body in copy-pasteable blocks (see Output Format below) so the user can paste directly into the web UI.
  - If the user says they have a personal access token for that host and want it created via API, ask them to provide the token for this one call rather than searching for it yourself.

### 6. Never merge automatically

This skill drafts/opens the PR. It never merges it, never approves it, and never bypasses review — even if `gh pr merge` exists and is technically available. Merging is a separate, explicitly-requested action.

## Output Format

**When created via `gh`:**

```
## PR Created

**URL:** <pr-url>
**Title:** <title>
**Base:** <target>  ←  **Head:** <source>
```

**When drafted only (no CLI/API path available):**

```
## PR Draft — open here and paste

**Open:** <compare-or-new-pr-url>

### Title
```
<title>
```

### Body
```markdown
<body>
```
```

## Guardrails

- Never fabricate commit content — every bullet in the summary must trace back to an actual commit subject/body or diffstat in the resolved range.
- Never guess source/target when genuinely ambiguous — ask via **AskUserQuestion**.
- Never push, force-push, create, delete, or merge branches as a side effect of drafting a PR.
- Never pull credentials out of credential stores to call a forge API on the user's behalf unless they explicitly hand you a token for that purpose in the conversation.
- Match the repository's actual commit-message language/format — don't impose English on a Chinese-convention repo or vice versa.
- If the diff range is empty, say so plainly and stop; don't invent a PR for a no-op.
