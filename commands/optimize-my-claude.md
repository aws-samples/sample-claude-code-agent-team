# Optimize Claude Code Configuration

Audits and optimizes the entire `~/.claude` configuration — settings, agents, rules, skills, plugins, and MCP servers — for the current Claude model and latest Claude Code features.

## Input

Focus area (optional): $ARGUMENTS

If a focus area is provided (e.g., "settings", "agents", "rules", "plugins", "mcp"), only audit and optimize that area. Otherwise, run the full audit.

## Process

### Phase 1: Audit Current State

1. **Inventory all configuration files** — read every file under `~/.claude/` that matters. Issue all reads in a single parallel batch (Opus 4.7 handles wide tool fan-out efficiently; sequential reads waste context budget):
   - `~/CLAUDE.md`
   - `~/.claude/settings.json` and `~/.claude/settings.local.json`
   - `~/.claude/agents/*.md` (all agent definitions)
   - `~/.claude/rules/*.md` (all rules files)
   - `~/.claude/skills/*/SKILL.md` (all custom skills)
   - `~/.claude/commands/*.md` (all custom commands)
   - `~/.claude/agents/.mcp.json` (agent MCP config)
   - `~/.claude/plugins/installed_plugins.json` and `~/.claude/plugins/blocklist.json`
   - `~/.claude/specs/templates/*.md` (spec templates)
   - MCP server config from `~/.claude.json` (extract `mcpServers` and project-level `mcpServers`)

2. **Record the current state** — note file sizes, line counts, and key settings for before/after comparison.

### Phase 2: Research Current Best Practices

3. **Research latest Claude Code features** — use the `claude-code-guide` agent to research. Anchor the research on the **active model — Opus 4.7 (`claude-opus-4-7`)** — and flag any recommendations that assume an older model (e.g., Opus 4.6's `/fast` mode is not available on 4.7). Cover:
   - Opus 4.7 capabilities, pricing, and recommended settings (caching, effort, thinking budget, parallel tool calls)
   - New or changed environment variables
   - New hook events, skill features, or agent team capabilities
   - Deprecated settings or features (including model IDs retired between 4.6 and 4.7)
   - Token optimization best practices specific to Opus-tier models (caching discipline matters more at Opus pricing)
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
- Prompt caching enabled (no `DISABLE_PROMPT_CACHING=1` unless justified) — caching ROI is highest at Opus 4.7 pricing
- Effort level strategy (prefer medium default with on-demand escalation; Opus 4.7 already reasons well at medium, so global high-effort is almost always wasteful)
- Subagent model strategy (per-agent frontmatter vs global override). With Opus 4.7 as the main-loop model, cost discipline depends on routing focused/narrow work to Sonnet 4.6 or Haiku 4.5 subagents rather than inheriting Opus. Flag any teammate still pinned to `opus` whose task doesn't actually need it.
- Security hardening vars (`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`)
- MCP tool search threshold (`ENABLE_TOOL_SEARCH` / `MAX_MCP_OUTPUT_TOKENS`) — with the current server footprint (AWS suite + deepwiki + playwright + sentral), tool-search deferral is effectively mandatory to keep the system prompt compact
- Model IDs match current Bedrock inference profiles — `claude-opus-4-7` for the main loop; verify no `claude-opus-4-6`, `claude-opus-4-5`, or earlier IDs linger in settings, agent frontmatter, or CLAUDE.md
- `/fast` references: `/fast` only works on Opus 4.6. If CLAUDE.md or docs mention it as a fallback for the current session, flag it — it's a no-op on 4.7

### Agents
- Model assignments appropriate for the Opus-4.7 era:
  - `opus` (4.7) — team lead, cross-file reasoning, review-agent, code-architect roles
  - `sonnet` (4.6) — `[coding]` and `[devops]` teammates with well-scoped tasks, Explore agent
  - `haiku` (4.5) — narrow lookups, mechanical transforms, status-line helpers, quick classifiers
  - Any `opus` pin on a teammate that does focused single-file work is likely a cost leak — call it out
- No duplicated content that belongs in `agent-team-protocol.md`
- Frontmatter uses current features (model, isolation, memory, `team_name`)
- Cross-references to rules and specs are valid
- Teammates that dispatch many parallel tool calls benefit from Opus 4.7's wide tool-fanout; keep their prompts from over-sequencing work

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
- Deferred tool search threshold appropriate for server count — with the sentral + AWS suite + playwright + deepwiki footprint, the eager-load tool set should be kept small and everything else routed through `ToolSearch`
- `MAX_MCP_OUTPUT_TOKENS` tuned so a single tool call cannot swamp the Opus 4.7 context window

### Permissions (settings.local.json)
- No stale one-off permission entries
- Permissions are minimal and intentional
