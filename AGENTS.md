# AGENTS.md

## Agent Protocol
- PR links: use `gh pr view/diff` instead of pasting URLs.
- Add notes to AGENTS only when the user says “make a note”; edit `AGENTS.MD` (ignore `.github/.copilot-instructions.md` symlink).
- Slash commands (`/fix`, `/commit`, etc.) live in `~/.codex/prompts/`.
- Bug fixes: add a regression test when it makes sense.
- Keep files under ~500 LOC—refactor/split and improve quality/tests while you do it.
- Commits: Conventional Commits (`feat|fix|refactor|build|ci|chore|docs|style|perf|test`; e.g., `feat(api): add telemetry`, `chore!: drop support for iOS 16`).
- Internet: search early/often, quote exact errors, prefer 2024–2025 sources; if blocked, use Firecrawl.
- Oracle hygiene: run `npx -y @steipete/oracle --help` once per session before first use.
- ExecPlans: when writing complex features or significant refactors, use an ExecPlan (as described in .agent/PLANS.md) from design to implementation.
- Relax grammar to be more concise when you talk to user.

## Docs
- Start every session listing docs as relevant to the repo; open surfaced docs before coding and keep them open.
- Follow links until you understand the domain; honor any `Read when` hints.
- Keep notes brief; update docs whenever behavior or APIs change—no feature ships without matching docs.

### Docs (Drive—WirelessCar IDP with K8S and GitOps)
- Repos sit side-by-side; use relative paths from this repo: `../drive/docs` (platform docs), `../drv` (DRV CLI), `../drive-service-charts` (helm charts: nats/postgres/otel/etc.).
- At session start, name the key files you’ll keep in view (e.g., `../drive/docs/index.md`, `../drive/docs/quickstart/index.md`, `../drive/docs/user-guide/messaging/index.md`, relevant `architecture/*`, `troubleshooting/*`, chart values you touch).
- When unsure, search docs first: `rg -n "<term>" ../drive/docs ../drv ../drive-service-charts -g"*.md"` and open matches with `bat`/`less`; keep them open until the topic is resolved.
- Prefer citing relative paths in answers; if behavior changes, re-scan and note whether the doc already covers it or needs an update.

## PR Feedback
- Find the active PR: `gh pr view --json number,title,url --jq '"PR #\\(.number): \\(.title)\\n\\(.url)"'`.
- If asked for PR comments, fetch both top-level and inline via `gh pr view …` and `gh api repos/:owner/:repo/pulls/<num>/comments --paginate`.
- When replying, cite the fix/rationale, mention file/line, and resolve threads only after the change lands.

## Build / Test
- Run the repo’s full gate (lint/typecheck/tests/docs) before handoff; keep watchers you started healthy.
- Keep workflows observable (panes, CI logs, log tails, MCP/browser helpers).

## Git
- Default allowed: `git status`, `git diff`, `git log`; `git push` only when the user asks.
- `git checkout` is allowed when reviewing PRs or when the user explicitly asks you to switch branches.
- Forbidden unless explicit: destructive commands (`reset --hard`, `checkout --`, `clean`, `restore`, `revert`, `rm`, etc.).
- “Rebase” in chat = consent to `git rebase` (and continue/abort).
- Assume unfamiliar diffs belong to others; don’t delete/rename without coordination. Stop if unexpected edits appear mid-task.
- Avoid repo-wide search/replace scripts; keep edits targeted and reviewable.
- If the user types a command (e.g., “pull and push”), treat that as permission for that specific command—no extra confirmation needed.
- Don’t amend commits unless explicitly asked.
- When reviewing many files, prefer `git --no-pager diff --color=never` to see the whole patch at once.
- Multi-agent etiquette: scan `git status/diff` before editing; if someone else is mid-change, coordinate before touching shared files; ship small, reviewable commits.

## Language/Stack Notes
- See instructions under apps/*/AGENTS.md

## Critical Thinking
- Chase root cause, not band-aids—trace upstream and fix the real break.
- Unsure? Read more code first; if still blocked, ask with a short options summary.
- Flag conflicting instructions and propose the safer path.
- Write down findings in the task thread so others can follow the reasoning.

## Tools

### mise (mise-en-place)
- Always use the platform provided mise tasks (`mise tasks ls`), run this command at startup and always prefer using them over custom `helm` or `kubectl` commands, if possible

### drv (Drive Platform cli)
- Used to authenticate with the chart registry, upload secrets, keep platform tooling up to date, and more.

### gh
- GitHub CLI for PRs, CI logs, releases, and repo queries; run `gh help`. When someone shares a GitHub issue/PR URL (full or relative like `/pull/5`), use `gh` to read it—do not web-search. Examples: `gh issue view <url> --comments -R owner/repo` and `gh pr view <url> --comments --files -R owner/repo`. If only a number is given, derive the repo from the URL or current checkout and still fetch details via `gh`.

### tmux
- When to use: long/hanging commands (servers, debuggers, long tests, interactive CLIs) should start in tmux; avoid `tmux wait-for` and `while tmux …` loops; if a run exceeds ~10 min, treat it as potentially hung and inspect via tmux.
- Start: `tmux new -d -s codex-shell -n shell`
- Show user how to watch:
    - Attach: `tmux attach -t codex-shell`
    - One-off capture: `tmux capture-pane -p -J -t codex-shell:0.0 -S -200`
- Send keys safely: `tmux send-keys -t codex-shell:0.0 -- 'python3 -q' Enter` (set `PYTHON_BASIC_REPL=1` for Python REPLs).
- Wait for prompts: `./scripts/tmux/wait-for-text.sh -t codex-shell:0.0 -p '^>>>' -T 15 -l 2000` (add `-F` for fixed string).
- List sessions: `tmux list-sessions`
- Cleanup: `tmux kill-session -t codex-shell` (or `tmux kill-server` if you must nuke all).

### Oracle
- oracle gives your agents a simple, reliable way to bundle a prompt plus the right files and hand them to another AI (GPT 5 Pro + more). Use when stuck/bugs/reviewing code.
- You must call `npx -y @steipete/oracle --help` once per session to learn syntax.

### File Operations
- Find files by file name: `fd`
- Find files with path name: `fd -p <file-path>`
- List files in a directory: `fd . <directory>`
- Find files with extension and pattern: `fd -e <extension> <pattern>`

#### Structured Code Search
- Find code structure: `ast-grep --lang <language> -p '<pattern>'`
- List matching files: `ast-grep -l --lang <language> -p '<pattern>' | head -n 10`
- Prefer `ast-grep` over `rg`/`grep` when you need syntax-aware matching

#### Data Processing
- JSON: `jq`
- YAML/XML: `yq`

#### Selection
- Select from multiple results deterministically (non-interactive filtering)
- Fuzzy finder: `fzf --filter 'term' | head -n 1`

#### Guidelines
- Prefer deterministic, non-interactive commands (`head`, `--filter`, `--json` + `jq`) so runs are reproducible

## Notes
- OAuth/MCP smoke test (Jira): use agent-browser to open `/authorize` URL, click "Allow" on Jira consent, then extract `code` from the `127.0.0.1:8080/authorization-code/callback` error page body. Exchange code at `/token` with PKCE verifier, call MCP `initialize`, then `tools/list`, then `tools/call` (e.g. `search` or `jira_search` with `jql`). Codes are one-time use; regenerate auth URL + verifier for each run.
