# Claude Code Multi-Agent Development Sample

A sample configuration for multi-agent development workflows using [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview). It shows how to set up a team of specialized AI agents that collaborate through a spec-driven process: a Full Stack lead orchestrates three specialists — Coding (application development), DevOps (infrastructure/deployment), and Review (code quality/security) — backed by Skills, Rules, and MCP servers for the tooling and knowledge needed to ship a full-stack application to AWS.

> **Disclaimer**: This repository is provided as an example only and is **NOT approved for production use**. The agent configurations, rules, and workflows are starting points — not production-ready defaults. You should review, adjust, and tailor them to fit your own project requirements, team conventions, and security posture. Adoption of this sample requires organizational legal review — you must complete the [LLM Legal Approval](#llm-legal-approval) and [MCP Server Legal Approval](#mcp-server-legal-approval) tables before use.

## Overview

![Architecture Diagram](docs/architecture-diagram.png)

This repo provides a sample `.claude` configuration with four core agents that work together:

| Agent | Role | Model | Effort |
|-------|------|-------|--------|
| **fullstack-agent** | Team lead — researches, designs specs, creates plans, delegates work | opus | xhigh |
| **coding-agent** | Implements features and writes tests from specs | sonnet | max |
| **devops-agent** | Infrastructure, CI/CD, containers, and documentation | sonnet | high |
| **review-agent** | Reviews implementations for correctness, security, and quality | opus | max |

Additional on-demand agents:

| Agent | Role | Model | Effort |
|-------|------|-------|--------|
| **sa-agent** | AWS Solutions Architect — Well-Architected reviews, cost/security | sonnet | max |

## How It Works

```
fullstack-agent (plan + research)
   → coding-agent ×N + devops-agent ×N (build in parallel, self-claiming from a shared queue)
   → review-agent ×N (verify in parallel, one per scope)
   → fullstack-agent (consolidate verdicts → next group or fix)
```

1. **Plan** — `fullstack-agent` researches the problem, writes a spec (`spec.md`, `design.md`), and creates a **wide, file-disjoint** task plan (`tasks.md`) sized so a pool of same-role agents can each claim a task at once
2. **Build** — `fullstack-agent` spawns parallel worker pools (up to **6 `coding`**, **2 `devops`**, **4 `review`**) via `TeamCreate`; instances self-claim unclaimed, unblocked tasks from the shared queue and drain it concurrently
3. **Review** — the `review-agent` pool reviews in parallel, each instance owning a disjoint scope and writing its own `review-<scope>.md` (a single `review.md` is used for small, cohesive groups); the lead consolidates verdicts (any FAIL ⇒ group FAILs)
4. **Fix** — if any scope review fails, `fullstack-agent` creates fix tasks and loops back to build

Pool sizes are ceilings, not quotas — the lead sizes each pool to the parallel width of the task graph (tiny jobs spawn 1 each). Agents coordinate through shared tasks (`TaskCreate`/`TaskUpdate`/`TaskList`) and direct messaging (`SendMessage`); the lead uses `TeamCreate` to spawn teammates and `TeamDelete` to clean up when work is complete.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) installed
- [Node.js](https://nodejs.org/) (for `npx`-based MCP servers)
- [uv](https://docs.astral.sh/uv/) (for `uvx`-based MCP servers)
- Python 3.8+ on `PATH` (the `hooks/` enforcement scripts use only the standard library)
- AWS credentials configured (for AWS MCP servers that need API access)
- *(Optional)* [tmux](https://github.com/tmux/tmux) or [iTerm2](https://iterm2.com/) with Python API enabled — for split-pane display where each agent gets its own visible pane. Without these, agent teams run in in-process mode (default), which works in any terminal.

## Quick Start

1. Install [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)

2. Add the configuration files to your Claude Code config directory:

> **Warning**: If you already have a `~/.claude/` directory with your own configuration, the commands below will overwrite files with matching names. Back up first and consider merging manually (Option B).

**Option A — Fresh install** (no existing `~/.claude` config):

```bash
mkdir -p ~/.claude
cp -r agents/ rules/ skills/ hooks/ ~/.claude/
chmod +x ~/.claude/hooks/*.py
cp settings.json ~/.claude/settings.json
cp .mcp.json ~/.claude/.mcp.json

# The bundled settings.json wires hooks via $CLAUDE_PROJECT_DIR. When installing
# globally, rewrite the hook commands to $HOME/.claude/hooks/ — see
# "Hook path resolution" below.
```

**Option B — Merge into existing config**:

```bash
# Back up your current config
cp -r ~/.claude ~/.claude.bak

# Copy agents, rules, skills, hooks (-n won't overwrite existing files)
cp -rn agents/ rules/ skills/ hooks/ ~/.claude/
chmod +x ~/.claude/hooks/*.py

# Then manually merge into your existing files:
# - settings.json: merge the "env", "enabledPlugins", and "hooks" keys (rewrite
#   hook paths from $CLAUDE_PROJECT_DIR to $HOME/.claude/hooks/ — see below)
# - .mcp.json: merge the "mcpServers" entries
```

**Hook path resolution.** The bundled `settings.json` wires the three enforcement hooks with `python3 "$CLAUDE_PROJECT_DIR/hooks/..."` so this repo can ship and run them without leaving the project. When you install hooks under `~/.claude/hooks/` (the natural location for a global setup), edit the `hooks` block in your merged `settings.json` to use `$HOME/.claude/hooks/...` instead. Either form works — the hooks themselves resolve `~/.claude/logs/...` paths via `$HOME` regardless of where the scripts live.

**Option C — Per-project install** (optional; scope the setup to one project instead of all of them):

Install into a single project's `.claude/` directory rather than your global `~/.claude/` — useful to try the setup on one repo, run different agent configs per project, or version the config alongside the code. Run from the target project's root:

```bash
mkdir -p .claude
cp -r agents/ rules/ skills/ commands/ hooks/ .claude/
chmod +x .claude/hooks/*.py
cp settings.json .claude/settings.json
cp .mcp.json .claude/.mcp.json
```

No hook-path edits are needed here: the bundled `settings.json` already resolves hooks via `$CLAUDE_PROJECT_DIR`, which Claude Code points at the project root. Project settings layer on top of your global config and take precedence for that project (see [Project-Local Settings](#project-local-settings-optional) for the full precedence order). Commit `.claude/` to share the setup with your team, or `.gitignore` it to keep it personal.

3. Enable the agent teams experimental feature. The bundled `settings.json` already sets this, so Option A/C installs are covered; if you merged manually (Option B), ensure your `settings.json` carries:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

4. Install required plugins.

   Plugins live in two marketplaces, both declared by the bundled `settings.json` via `enabledPlugins` (15 entries) and `extraKnownMarketplaces`. The AWS marketplace registers automatically on next session start, but the **official Claude marketplace** must be registered explicitly — `extraKnownMarketplaces` only carries non-default sources.

   **a) Register the official Claude marketplace** (one-time, host-wide):

   ```bash
   claude plugin marketplace add anthropics/claude-plugins-official
   ```

   Then verify both are listed (`claude-plugins-official`, `agent-plugins-for-aws`):

   ```bash
   claude plugin marketplace list
   ```

   **b) Install + enable plugins.** With the bundled `settings.json` in place, restart Claude Code (`claude`). On session start, it reads `enabledPlugins`, fetches each plugin from its declared marketplace, installs it under `~/.claude/plugins/cache/`, and enables it — the first start can take ~30s while plugins download. Alternatively, browse and toggle plugins interactively with `claude /plugins`, or install one directly: `claude plugin install deploy-on-aws@agent-plugins-for-aws`.

   **c) Verify.** From inside Claude Code, run `/plugins` and confirm all 15 entries listed in `settings.json` show as **enabled**:

   | Marketplace | Plugins |
   |-------------|---------|
   | `claude-plugins-official` | `context7`, `superpowers`, `code-review`, `code-simplifier`, `commit-commands`, `feature-dev`, `frontend-design`, `github`, `gitlab`, `pr-review-toolkit`, `security-guidance` |
   | `agent-plugins-for-aws` | `deploy-on-aws`, `aws-amplify`, `aws-serverless`, `databases-on-aws` |

   **Option B (merging into existing config):** make sure your merged `settings.json` includes **both** the full `enabledPlugins` block and the `extraKnownMarketplaces.agent-plugins-for-aws` block — without the marketplace definition, Claude Code cannot resolve the four AWS plugins (`@agent-plugins-for-aws`-suffixed names) even after the official marketplace is registered. Reference snippet:

   ```json
   {
     "enabledPlugins": {
       "deploy-on-aws@agent-plugins-for-aws": true,
       "aws-amplify@agent-plugins-for-aws": true,
       "aws-serverless@agent-plugins-for-aws": true,
       "databases-on-aws@agent-plugins-for-aws": true
     },
     "extraKnownMarketplaces": {
       "agent-plugins-for-aws": {
         "source": {
           "source": "github",
           "repo": "awslabs/agent-plugins"
         }
       }
     }
   }
   ```

   **Troubleshooting**:
   - *`marketplace add` fails with a clone error*: the repos are public, but `git` must be installed and reachable (configure your proxy first if behind one).
   - *Plugins in `enabledPlugins` show as missing in `/plugins`*: their marketplace isn't registered. Re-run `claude plugin marketplace list`; add `anthropics/claude-plugins-official` if absent (the AWS marketplace re-registers automatically from `settings.json`).
   - *Plugin loaded but its skills/agents are absent*: restart your session — plugin contributions are wired at session start, not hot-reloaded.

5. Verify MCP servers. Those in `.mcp.json` auto-install on first use via `npx`/`uvx`; check their status with `claude /mcp`.

6. Start Claude Code with `claude`.

## Repository Structure

```
├── agents/                     # Agent definitions (markdown prompts with frontmatter)
│   ├── fullstack-agent.md      # Team lead — architecture, planning, coordination
│   ├── coding-agent.md         # Implements features and tests
│   ├── devops-agent.md         # Infrastructure, CI/CD, containers, docs
│   ├── review-agent.md         # Code review and quality verification
│   └── sa-agent.md             # AWS Solutions Architect — Well-Architected reviews
├── .mcp.json                   # MCP server configurations used by agents and skills
├── rules/                      # Global behavioral rules for all agents (auto-loaded every session)
│   ├── AWS-security-guidelines.md # AWS security best practices and production safeguards
│   ├── agent-team-protocol.md  # Shared teammate lifecycle and communication protocol
│   └── execution-hygiene.md    # Non-interactive execution and dependency isolation
├── skills/                     # Domain-specific knowledge files (invoked on demand)
│   ├── spec-workflow/          # Spec-driven development loop with parallel task groups
│   ├── concurrent-cached-fetch/ # Concurrent + disk-cached bulk external fetching
│   ├── documentation/          # Technical writing patterns
│   ├── git-workflow/           # Git operations and conventions
│   └── pr-review/              # Pull request review patterns
├── commands/                   # Optional slash commands (see Optional Commands section)
│   ├── brainstorm.md           # `/brainstorm` — structured new-project ideation -> requirements.md
│   └── optimize-my-claude.md   # `/optimize-my-claude` — audit and tune ~/.claude after model releases
├── hooks/                      # Python hook scripts that machine-enforce the agent-team protocol
│   ├── team_hook_common.py            # Shared payload-parsing, audit-log, and exit-contract helpers
│   ├── task_created_format_check.py   # TaskCreated → enforce role/file/acceptance/Run task shape
│   ├── task_completed_verify_gate.py  # TaskCompleted → require Run command + verification sentinel
│   └── teammate_idle_workcheck.py     # TeammateIdle → nudge if claimable work remains for the role
└── settings.json               # Claude Code settings (env vars, enabled plugins, hook wiring)
```

## Key Concepts

**Agents** define who does what. Each is a markdown file with YAML frontmatter (name, description, model, optional `effort`) and a system prompt (role, constraints, workflow). The team lead (`fullstack-agent`) spawns and coordinates teammates. The optional `effort` field tunes reasoning depth.

**Rules** are global behavioral constraints applied to all agents — like AWS security guidelines and production safeguards honored on every interaction (see [Rules](#rules)).

**Skills** are domain-specific knowledge agents invoke on demand — patterns and protocols for workflows such as spec-driven development, git workflow, and PR review (see [Skills](#skills)).

**Hooks** are Python scripts wired into `settings.json` that machine-enforce the protocol across three events (`TaskCreated`, `TaskCompleted`, `TeammateIdle`), fail-open, auditing every decision to `~/.claude/logs/team-hooks.jsonl` (see [Hooks](#hooks)).

**Specs** are created at runtime in `.claude/specs/<slug>/` and hold the design decisions, task plans, review findings, and decision logs for each piece of work. Reusable templates (`spec.md`, `design.md`, `review.md`, `sa-review.md`, `decisions.md`, `prd.md`) live in `docs/specs/templates/` — agents copy them into a new spec as starting points.

## Rules

| Rule | Purpose |
|------|---------|
| `AWS-security-guidelines.md` | Enforces AWS security best practices including least-privilege access, production safeguards, and credential handling |
| `agent-team-protocol.md` | Shared teammate lifecycle — claiming tasks, communication patterns, verification gates (machine-enforced via `hooks/`; see [Hooks](#hooks)), and blocker reporting. Loaded as a rule (not a skill) so every spawned teammate inherits it without invoking `Skill` |
| `execution-hygiene.md` | Non-interactive execution (`-y`/`--yes`/`--no-input`, disabled pagers, no TTY assumptions) and per-language dependency isolation (venvs, `node_modules`, cargo, go mod) with version pinning and lock files. Loaded as a rule so every session — team or solo — inherits it |

## Skills

| Skill | Purpose |
|-------|---------|
| `spec-workflow` | Defines the full plan → build → review loop with parallel task groups and the `.claude/specs/<slug>/` directory structure. Structural conventions (directory layout, task format) are also inlined into each agent file so they are always visible; this skill carries the deeper workflow narrative on demand |
| `concurrent-cached-fetch` | Patterns for code that fans out over many independent external calls — bounded concurrency plus a content-keyed, no-expiry disk cache, with ready-to-adapt implementations in Python, JS/TS, Go, and Java. `fullstack-agent` plans for it, `coding-agent` loads it before any bulk-fetch loop, and `review-agent` flags sequential/uncached bulk I/O |
| `documentation` | Technical writing patterns for runbooks, architecture docs, and AWS service doc linking. Invoked by `coding-agent`/`devops-agent` at task close-out, and by `fullstack-agent` to refresh docs before cleanup |
| `git-workflow` | Conventional commit style, branch naming, and integration with the `commit-commands` plugin for commit/push/PR flows |
| `pr-review` | Pull request review patterns and delegation to the `pr-review-toolkit` plugin for specialized analyses |

## Hooks

Three Python scripts in `hooks/` machine-enforce the agent-team protocol. They are wired in `settings.json` and resolved at runtime via `$CLAUDE_PROJECT_DIR` (this repo) or `$HOME` (when installed globally — see "Hook path resolution" in [Quick Start](#quick-start)). Every decision is audited to `~/.claude/logs/team-hooks.jsonl`, and all hooks are **fail-open**: any unexpected condition allows the action, so a hook bug can never block a teammate.

| Event | Script | Enforcement |
|-------|--------|-------------|
| `TaskCreated` | `task_created_format_check.py` | Rolls back creation unless the task carries a `[role]` tag, both `\| files \| acceptance` pipe sections, and a `Run: <command>` |
| `TaskCompleted` | `task_completed_verify_gate.py` | Blocks completion unless the task has a `Run:` command **and** the owning teammate wrote a verification sentinel after that command passed |
| `TeammateIdle` | `teammate_idle_workcheck.py` | Nudges a teammate that is going idle while unclaimed, unblocked tasks tagged with its role still exist (capped at 2 nudges per claimable set, loop-safe) |

### Task shape

Tasks authored by the team lead must follow:

```
[coding|devops|sa] <verb> <what> | <file paths> | <acceptance>. Run: <command>
```

Example: `[coding] add JWT verifier | src/auth/jwt.ts | unit tests pass. Run: npm test -- src/auth`

### Verification sentinel

Before a teammate calls `TaskUpdate(status=completed)`, it must run the task's `Run:` command and then write a sentinel attesting that the run passed:

```bash
mkdir -p ~/.claude/logs/verified/<team_name>
echo "<the Run command> PASSED" > ~/.claude/logs/verified/<team_name>/task-<task_id>.verified
```

The hook deletes the sentinel on a successful completion so it cannot be reused. The hook can't read the teammate's transcript — the sentinel is the teammate's attestation that verification actually happened.

### Bypass tokens

Add either token anywhere in the task subject or description for legitimate exceptions:

| Token | Use when |
|-------|----------|
| `[skip-format-check]` | The task is coordination/research/non-build work and doesn't need the `[role] \| files \| acceptance \| Run:` shape |
| `[skip-verify]` | The task is pure analysis or documentation with no runnable verification command (typical for some `[sa]` / docs-only tasks). Prefer giving the task a real `Run:` (lint, validate, `--dry-run`, query check) over a skip token where one exists |

### Verifying hooks are wired

After install, smoke-test from the repo root:

```bash
# Should exit 2 (block) with "Missing: [role] tag..." on stderr
echo '{"task_id":"test","task_subject":"do something","task_description":""}' \
  | python3 hooks/task_created_format_check.py

# Should exit 0 (allow)
echo '{"task_id":"test","task_subject":"[coding] foo | f.py | tests pass. Run: pytest"}' \
  | python3 hooks/task_created_format_check.py

# Should exit 0 (fail-open)
echo '{}' | python3 hooks/task_completed_verify_gate.py
```

If `claude /doctor` reports the hook commands and Claude Code logs each `TaskCreated` / `TaskCompleted` / `TeammateIdle` decision to `~/.claude/logs/team-hooks.jsonl`, enforcement is live.

The full convention, including loop-guard semantics for `TeammateIdle` and the audit-log schema, lives in `rules/agent-team-protocol.md` → "Enforced Hooks".

## Optional Commands

The `commands/` directory holds optional slash commands that plug into this workflow. They aren't required for the core plan → build → review loop, but cover two common needs around it: starting new work and keeping the configuration current. Install them alongside the other config, then invoke from any session:

```bash
cp -r commands/ ~/.claude/commands/
```

| Command | When to Use | Purpose |
|---------|-------------|---------|
| `/brainstorm` | Starting a new project from a rough idea | Walks through up to 10 clarifying questions (users, scale, integrations, NFRs, budget, deployment, edge cases, MVP scope) and writes `.claude/specs/<slug>/requirements.md` — the starting point the `spec-workflow` skill turns into `spec.md`, `design.md`, and `tasks.md` |
| `/optimize-my-claude` | Following a new Claude model release | Audits the full `~/.claude` configuration against current best practices for the active model — flagging deprecated env vars, stale model IDs, cost leaks, redundant content, and missing features. Presents findings by impact, waits for approval, then applies only the approved changes. Pass an optional focus area (e.g., `/optimize-my-claude settings`) to scope it |

Both commands are interactive — they ask for confirmation before writing files or making configuration changes.

## Plugins

This configuration enables the following Claude Code plugins via `settings.json`:

| Plugin | Purpose |
|--------|---------|
| context7 | Live documentation lookup for libraries and frameworks |
| superpowers | Enhanced development workflows (TDD, debugging, planning) |
| feature-dev | Guided feature development with architecture focus |
| code-review | Code review workflows |
| pr-review-toolkit | Comprehensive PR review with specialized agents |
| commit-commands | Git commit, push, and PR creation |
| github | GitHub issue/PR management |
| gitlab | GitLab issue/PR management |
| code-simplifier | Code clarity and maintainability refinement |
| frontend-design | Production-grade frontend interface design |
| security-guidance | Security best practices — container hardening, secrets handling, and least-privilege guidance |
| deploy-on-aws | AWS deployment — codebase analysis, service recommendation, cost estimation, IaC generation. Provides `awsiac` (CloudFormation/CDK validation), `awspricing` (cost reports), and an architecture-diagram skill |
| aws-amplify | AWS Amplify Gen 2 — full-stack app deployment, auth, data models, storage, GraphQL APIs, sandbox/production environments |
| aws-serverless | AWS serverless — Lambda design/build/deploy/test, SAM CLI, API Gateway (REST/HTTP/WebSocket), Event Source Mapping, durable functions |
| databases-on-aws | Aurora DSQL — queries, schema inspection, migrations, and best-practice recommendations |

## MCP Servers

MCP servers are configured in [`.mcp.json`](.mcp.json) and auto-installed on first use via `npx` or `uvx`. No manual installation is required.

| Server | Source | Purpose |
|--------|--------|---------|
| [awslabs.document-loader-mcp-server](https://github.com/awslabs/mcp) | AWS Labs | Load external documents (PDFs, web pages) |

## Speed & Orchestration Modes

Two on-demand Claude Code modes pair well with this agent-team setup. Both are optional and used per-task — not configured in this repo.

- **`/fast`** — toggles faster Opus output without switching to a smaller model. Useful for interactive work (live debugging, tight edit-test loops) where latency matters more than token economy. Toggle it at session start rather than mid-conversation. It doesn't change an agent's model — that stays in each agent's `model` frontmatter.
- **Workflows / `ultracode`** — multi-agent orchestration that fans a task out across many subagents (parallel audits, large migrations, broad multi-file sweeps, adversarial review). Opt in by including the word **workflow** in a request, monitor progress with `/workflows`, or turn on **ultracode** for a standing workflow-per-task default. A heavier, broader-coverage complement to the lead → teammates → review loop; reach for it when a task genuinely needs the breadth, and stay with the standard team loop otherwise.

## Project-Local Settings (Optional)

`.claude/settings.local.json` is your **personal, per-project** settings file — Claude Code auto-gitignores it (also listed in [`.gitignore`](.gitignore)), so it never gets committed. It's the home for anything you don't want to share or hard-code into the shared config: a **permission allow-list** so Claude Code stops prompting for tools you trust, project MCP opt-ins, and machine- or account-specific `env`/`model` overrides.

Claude Code combines settings across scopes in this priority order:

1. **Managed** (enterprise/MDM) — highest, cannot be overridden
2. **Command-line flags** — temporary session overrides
3. **Local** — `.claude/settings.local.json` (personal, per-project)
4. **Project** — `.claude/settings.json` (shared, committed to git)
5. **User** — `~/.claude/settings.json` (your global defaults) — lowest

For single-valued keys (e.g. `model`), the higher scope wins, so a project's `.claude/settings.local.json` overrides your global settings for that project only. Permission allow-lists are **additive** — entries from every scope combine, so a project-local list extends your global one rather than replacing it.

**Create it** — most commonly to pre-approve the tools and commands you trust, the same `permissions` block you keep in your global `~/.claude/settings.local.json`:

```bash
mkdir -p .claude
cat > .claude/settings.local.json <<'JSON'
{
  "permissions": {
    "allow": [
      "Read",
      "Edit",
      "Grep",
      "Glob",
      "Bash(git status)",
      "Bash(npm test:*)",
      "WebFetch(domain:docs.aws.amazon.com)"
    ]
  },
  "enabledMcpjsonServers": ["awslabs.document-loader-mcp-server"]
}
JSON
```

Notes:
- **Scope to least privilege.** Each entry is a tool Claude Code may then run without asking. A bare name like `"Bash"` or `"Edit"` approves *every* use; prefer scoped forms — `"Bash(npm test:*)"`, `"WebFetch(domain:...)"` — for anything with side effects, and grant only what you're comfortable auto-approving.
- Same shape as the repo's own [`.claude/settings.local.json`](.claude/settings.local.json), which ships with an empty `allow` list and uses `enabledMcpjsonServers` to opt into the project's MCP server.
- The file can also carry personal `env` or `model` overrides — e.g. `"model": "opus"`, or on Amazon Bedrock the inference-profile IDs (`"model": "us.anthropic.claude-opus-4-8"` plus `ANTHROPIC_DEFAULT_*_MODEL` entries in `env`). It need **not** restate `hooks`, `enabledPlugins`, or marketplaces from the shared config.

## Customization

- **Add agents**: Create a new `<name>.md` in `agents/` with frontmatter (`name`, `description`, `model`, optional `effort`), then reference it in the fullstack-agent's team composition
- **Add rules**: Drop a markdown file in `rules/` — all agents will follow it
- **Add skills**: Create a `<name>/SKILL.md` in `skills/` — agents reference these for domain knowledge
- **Change models**: Edit the `model` field in each agent's YAML frontmatter. Available models: `opus`, `sonnet`, `haiku`
- **Add MCP servers**: Add entries to `.mcp.json` — servers are auto-installed via `npx`/`uvx` on first use

## LLM Legal Approval

| Field | Value |
|-------|-------|
| Service | Claude (Anthropic) |
| Approval Status | [To be completed by adopter] |
| Approval Date | [Date] |
| Approval Authority | [Legal/Procurement team] |
| License Terms | [Link to agreement] |
| Usage Restrictions | [Any limitations] |

> **Note**: Adopters must complete this section with their organization's legal approval status before using Claude Code in any project. Consult your legal and procurement teams for guidance on AI/LLM usage policies.

## MCP Server Legal Approval

Adopters must complete this table before using the MCP servers configured in [`.mcp.json`](.mcp.json).

| Server | Provider | Approval Status | Right to Use | Distribution Rights | Security Review |
|--------|----------|-----------------|--------------|---------------------|-----------------|
| awslabs.document-loader-mcp-server | AWS Labs | Approved (AWS ToS) | Yes | Yes | AWS-managed |
> **Note**: Third-party MCP servers require independent legal and security review by your organization before use. AWS-provided servers fall under AWS Terms of Service.

## Dataset Compliance

No dataset is provided or required. This repository contains only configuration files (agent definitions, rules, skills, and MCP server configurations) — no training data, evaluation data, or other datasets are included.

## Security

See [SECURITY.md](SECURITY.md) for the full security overview including threat model, AI security controls, and risk assessment.

For security issue notifications, see [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications).

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.
