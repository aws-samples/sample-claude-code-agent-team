# Optimize Claude Code Configuration

Audits and optimizes the entire `~/.claude` configuration — settings, agents, rules, skills, plugins, and MCP servers — for the current Claude model and latest Claude Code features.

## Input

Focus area (optional): $ARGUMENTS

If a focus area is provided (e.g., "settings", "agents", "rules", "plugins", "mcp"), only audit and optimize that area. Otherwise, run the full audit.

## Process

### Phase 1: Audit Current State

1. **Inventory all configuration files** — read every file under `~/.claude/` that matters. Issue all reads in a single parallel batch (Opus 4.8 handles wide tool fan-out efficiently and has a 1M-token context window; sequential reads still waste turns):
   - `~/CLAUDE.md`
   - `~/.claude/settings.json` and `~/.claude/settings.local.json`
   - `~/.claude/agents/*.md` (all agent definitions)
   - `~/.claude/rules/*.md` (all rules files)
   - `~/.claude/skills/*/SKILL.md` (all custom skills)
   - `~/.claude/commands/*.md` (all custom commands)
   - `~/.claude/agents/.mcp.json` (agent MCP config)
   - `~/.claude/plugins/installed_plugins.json` and `~/.claude/plugins/blocklist.json`
   - MCP server config from `~/.claude.json` (extract `mcpServers` and project-level `mcpServers`)

2. **Record the current state** — note file sizes, line counts, and key settings for before/after comparison.

### Phase 2: Research Current Best Practices

3. **Research latest Claude Code features** — use the `claude-code-guide` agent to research. Anchor the research on the **active model — Opus 4.8 (`claude-opus-4-8`)**, whose 1M-token context window is now standard. Flag any recommendation that assumes an older model (e.g., Opus 4.7's tighter token-budget framing, or manual extended-thinking `budget_tokens`, which Opus 4.8 rejects in favor of adaptive thinking).

   **Token-accounting is source-agnostic:** wherever this command reasons about "cost," the real constraint is **token-budget headroom**, independent of how those tokens are consumed — billed per-token via Amazon Bedrock / Google Vertex / the Anthropic API, or counted against an Anthropic subscription plan's rate limits. Published per-token prices ($/MTok) are useful only as *relative weights* between models (Opus > Sonnet > Haiku). Determine the active backend before reasoning about cost: check `settings.json` for `CLAUDE_CODE_USE_BEDROCK` / `CLAUDE_CODE_USE_VERTEX`, the model-ID style (`us.anthropic.claude-*` ⇒ Bedrock inference profile; `claude-*@<date>` ⇒ Vertex; bare `claude-*` ⇒ Anthropic API / plan), and caching env vars (`ENABLE_PROMPT_CACHING_1H_BEDROCK` ⇒ Bedrock). Cover:
   - Opus 4.8 capabilities and recommended settings (caching, effort, adaptive thinking, parallel tool calls, 1M-context headroom)
   - New or changed environment variables
   - New hook events, skill features, or agent team capabilities
   - Deprecated settings or features (including model IDs that became legacy by 4.8: `claude-opus-4-7`, `claude-opus-4-6`, `claude-opus-4-5`)
   - Token optimization best practices specific to Opus-tier models (caching discipline conserves token-budget headroom on every backend, even with 1M context)
   - New plugins or MCP servers worth adopting

4. **Compare current config against best practices** — identify:
   - Deprecated env vars still in use
   - Suboptimal defaults (effort level, model assignments, caching)
   - Redundant content across files (rules duplicating CLAUDE.md, agents duplicating protocol)
   - Stale permissions in `settings.local.json`
   - Missing new features that would benefit the user's workflow
   - Context bloat (oversized rules, too many unconditional rules, MCP tool overhead)

### Phase 3: Plan Changes

5. **Present findings to user** — organize into categories:

   ```
   ## Findings

   ### High Impact (cost/performance)
   - <finding> — <recommendation>

   ### Medium Impact (features/quality)
   - <finding> — <recommendation>

   ### Low Impact (cleanup)
   - <finding> — <recommendation>

   ### No Changes Needed
   - <area> — already optimal because <reason>
   ```

6. **Get user approval** — ask the user which findings to act on before making changes. Do NOT make changes without confirmation.

### Phase 4: Implement

7. **Apply approved changes** — for each approved change:
   - Read the file first
   - Make the minimal edit needed
   - Verify the edit is correct

8. **Validate cross-references** — after all edits:
   - Verify every path referenced in CLAUDE.md exists
   - Verify agent model frontmatter matches CLAUDE.md agent roster
   - Verify rules files referenced by agents and skills exist
   - Verify no broken cross-references between files

### Phase 5: Report

9. **Summarize changes** — present a before/after table:

   ```
   ## Changes Applied

   | File | Change | Reason |
   |------|--------|--------|
   | ... | ... | ... |

   ## Features to Consider Later
   - <feature> — <when it would be useful>
   ```

10. **Update memory** — save a memory entry recording what was changed and why, so future runs of this command can track drift over time.

## Key Checks by Area

### settings.json
- Deprecated env vars (`ANTHROPIC_SMALL_FAST_MODEL`, etc.)
- Prompt caching enabled (no `DISABLE_PROMPT_CACHING=1` unless justified) — caching ROI is highest at Opus pricing/usage weight; on Bedrock confirm `ENABLE_PROMPT_CACHING_1H_BEDROCK` is set. Cache hits reuse prior context at a fraction of a fresh read's token weight, stretching token-budget headroom regardless of backend
- Effort level strategy. Opus 4.8 honors the effort knob more strictly than older models; the ladder is `low` < `medium` < `high` < `xhigh` (`xhigh` is Opus 4.8/4.7 only). Per-agent `effort:` frontmatter is the right lever — set `high` on Opus reasoning roles (team lead, review), `medium` on Sonnet/Haiku helper agents, and leave focused implementers at default. Reconcile against the user's "medium default, avoid global high-effort" philosophy in `CLAUDE.md`: that guidance is about the *global* default, not per-agent tiers — keep the global default modest and escalate per-role
- Subagent model strategy (per-agent frontmatter vs global override). With Opus 4.8 as the main-loop model, token-budget discipline depends on routing focused/narrow work to Sonnet 4.6 or Haiku 4.5 subagents rather than inheriting Opus 4.8 — the win (lower token weight + latency) holds on every backend. Flag any teammate still pinned to `opus` whose task doesn't actually need it.
- Security hardening vars (`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`)
- MCP tool search threshold (`ENABLE_TOOL_SEARCH` / `MAX_MCP_OUTPUT_TOKENS`) — with the current server footprint (deploy-on-aws / aws-serverless / databases-on-aws / aws-amplify plugin MCPs + standalone `awslabs.document-loader-mcp-server`), tool-search deferral is effectively mandatory to keep the system prompt compact
- Model IDs are current for the active backend — main loop on Opus 4.8 (Bedrock inference profile `us.anthropic.claude-opus-4-8`; Vertex `claude-opus-4-8@<date>`; Anthropic API `claude-opus-4-8`). Agent frontmatter uses the `opus` / `sonnet` / `haiku` aliases, resolving to Opus 4.8, Sonnet 4.6, and Haiku 4.5. Verify no `claude-opus-4-7`, `claude-opus-4-6`, `claude-opus-4-5`, or earlier IDs linger as the main loop in settings, agent frontmatter, or CLAUDE.md — these are now legacy
- **Inference backend matches the account.** Confirm `CLAUDE_CODE_USE_BEDROCK` / `CLAUDE_CODE_USE_VERTEX` (or their absence) is consistent with the model-ID style in use — a mismatch silently routes to the wrong or unavailable backend. Flag any inconsistency
- `/fast` mode availability: works on Opus 4.8, 4.7, and 4.6 — it speeds up Opus output without downgrading to a smaller model (confirmed in the active CLI system prompt). Flag any docs claiming `/fast` is limited to older Opus versions and correct them.

### Agents
- Model assignments appropriate for the Opus-4.8 era:
  - `opus` (4.8) — team lead, cross-file reasoning, review-agent, code-architect roles; benefits most from the 1M context on large-repo work. Pair with `effort: high`
  - `sonnet` (4.6) — `[coding]` and `[devops]` teammates with well-scoped tasks, Explore agent; `effort: medium` for the speed/quality balance
  - `haiku` (4.5) — narrow lookups, mechanical transforms, status-line helpers, quick classifiers
  - Any `opus` pin on a teammate that does focused single-file work is likely a token-budget leak (Opus carries far more token weight than Sonnet/Haiku for the same work, on every backend) — call it out
- Frontmatter sets `effort:` deliberately — `high` on Opus reasoning roles, `medium` on Sonnet/Haiku helpers, omitted (default) on focused implementers. Flag Opus agents with no effort tier
- No duplicated content that belongs in `agent-team-protocol.md`
- Frontmatter uses current features (model, effort, isolation, memory, `team_name`)
- Cross-references to rules and specs are valid
- Teammates that dispatch many parallel tool calls benefit from Opus 4.8's wide tool fan-out and large context; keep their prompts from over-sequencing work

### Rules
- No content duplicated between rules files and CLAUDE.md
- No content duplicated between rules files and agent definitions
- Large rules consider whether content could move to on-demand skills
- Rules that only apply to specific file types use `paths` frontmatter

### Skills
- Skills use SKILL.md format (not legacy commands format)
- Skills reference current MCP servers and plugins
- Agent integration sections reference current agent roster

### Plugins
- No deprecated plugins enabled
- LSP/code intelligence plugins installed for primary languages
- Plugin count reasonable (each adds context overhead)

### MCP Servers
- No deprecated servers (e.g., `awslabs.aws-diagram-mcp-server` has been superseded by the deploy-on-aws diagram skill)
- Server config uses latest package versions (`@latest`)
- `FASTMCP_LOG_LEVEL=ERROR` set to reduce noise
- Deferred tool search threshold appropriate for server count — with the AWS plugin suite + standalone `awslabs.document-loader-mcp-server` footprint, the eager-load tool set should be kept small and everything else routed through `ToolSearch`
- `MAX_MCP_OUTPUT_TOKENS` tuned so a single tool call cannot swamp the context window — Opus 4.8's 1M context is larger, but an oversized tool result still wastes tokens and pollutes the cache

### Permissions (settings.local.json)
- No stale one-off permission entries
- Permissions are minimal and intentional
