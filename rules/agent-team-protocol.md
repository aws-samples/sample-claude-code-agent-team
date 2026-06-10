# Agent Team Protocol

Shared protocol for all agent team teammates. The team lead (`fullstack-agent`) coordinates; all other agents are teammates. This file is loaded as a global rule for every session — every teammate inherits it as priming, no `Skill` invocation required.

## Teammate Lifecycle

1. Receive delegation via `SendMessage` from the team lead with spec path and task assignments
2. Read `spec.md` and `design.md` before any work
3. Claim tasks via `TaskUpdate` (-> `in_progress`); check context in `tasks.md`. Blocked tasks auto-unblock when dependencies complete
4. Implement exactly what each task describes
5. Self-verify (see Verification Gate below), then mark complete via `TaskUpdate` (-> `completed`)
6. Update `tasks.md` with `[x]` and a `> Done.` completion note
7. Notify team lead via `SendMessage`; after finishing, self-claim unclaimed tasks for your role

## Communication Rules

- **Direct to teammates**: Interface clarifications, dependency questions, sharing outputs they need
- **To the lead**: Blockers needing decisions, completion reports, scope/spec questions
- Tools: `SendMessage` (any teammate), `TaskUpdate` (claim/complete), `TaskList` / `TaskGet` (status)

## Completion Reporting

Update both places and notify:
1. `TaskUpdate` -> `completed`
2. `tasks.md`: `- [x] [role] description` with `> Done. <summary>` note
3. `SendMessage` to team lead (and any teammates that depend on your output)

## Blocker Reporting

Mark `[!]` in `tasks.md` with specific blocker details. `SendMessage` to team lead. If the same blocker persists after two attempts, the lead escalates to the user.

## Verification Gate (All Teammates)

Before marking ANY task complete:
1. Run the verification command specified in the task (the `Run:` command)
2. Confirm interface/output contracts match the task spec exactly
3. Confirm you only modified files listed in your task assignment
4. **Write the verification sentinel** (machine-enforced — see below), then `TaskUpdate -> completed`

If verification fails and you can't fix it within scope, mark `[!]` with the specific failure.

## Enforced Hooks (Automated Guardrails)

Three settings.json hooks enforce this protocol automatically when an agent team is active. They are **fail-open** (a hook error never blocks you) and log every decision to `~/.claude/logs/team-hooks.jsonl`. Scripts live at `hooks/` in this project (resolved via `$CLAUDE_PROJECT_DIR`).

### 1. Task format check (`TaskCreated`)
A task is **rolled back at creation** unless its subject/description contains: a `[coding|devops|sa]` role tag, pipe-delimited `| <files> | <acceptance>`, and a `Run: <command>`. This is the lead's concern (the lead authors tasks), but all agents should know the shape:
`[role] <verb> <what> | <file paths> | <acceptance>. Run: <command>`
- **Bypass** (non-build / coordination / research tasks): include `[skip-format-check]` anywhere in the subject or description.

### 2. Verification gate (`TaskCompleted`) — ACTION REQUIRED BY TEAMMATES
A task **cannot be marked complete** unless (a) it carries a `Run:` command, and (b) you have written a **verification sentinel** after that command passed. The hook cannot see your transcript, so the sentinel is your attestation that you actually ran verification. After your `Run:` command passes, and immediately before `TaskUpdate -> completed`:

```bash
mkdir -p ~/.claude/logs/verified/<team_name>
echo "<the Run command> PASSED" > ~/.claude/logs/verified/<team_name>/task-<task_id>.verified
```

Use your real team name and the task's numeric id. The sentinel is consumed (deleted) on a successful completion, so it cannot be reused. If you skip this, your completion is blocked with instructions.
- **Bypass** (tasks that genuinely need no verification, e.g. docs-only): include `[skip-verify]` in the task subject/description.

### 3. Idle work-check (`TeammateIdle`)
Before you go idle, the hook checks the task store for **unclaimed, unblocked tasks tagged with your role**. If any exist, you are kept working and nudged to either claim one (`TaskUpdate(owner=<you>, status=in_progress)`) or confirm to the lead you're genuinely done. After 2 nudges for the same task set it lets you idle (loop-safe). This enforces the lifecycle step "self-claim unclaimed tasks for your role."

## Handling Ambiguity

- **Missing details**: Check `spec.md` and `design.md` first. If not there, `SendMessage` to lead or relevant teammate
- **Multiple valid approaches**: Pick the simplest that satisfies acceptance criteria
- **Out-of-scope issues**: Note in completion report; don't fix
- **Conflicting requirements**: Mark `[!]`, never silently pick one interpretation
- **Dependency on another teammate**: `SendMessage` to them directly, then `[!]` if not ready

## Shutdown (Ordered Handshake)

**Teammate side.** When the lead sends `{type: "shutdown_request"}`, finish current work, ensure tasks are properly marked in both the shared task list and `tasks.md`, then reply `{type: "shutdown_response", request_id: <echoed>, approve: true}`. Approving terminates your process — do it only once your work is durably recorded.

**Lead side.** `TeamDelete` **fails while the team has any active member**; a member stays active until it has approved a shutdown. So tear down in order: (1) read `~/.claude/teams/<team>/config.json` `members[]` for the authoritative active list — don't rely on memory; (2) `SendMessage` a `shutdown_request` to **every** member; (3) **wait** for every `shutdown_response`/`approve: true` (each approval frees one member); (4) only then `TeamDelete`. Calling `TeamDelete` before the member list drains wastes a turn on a predictable error. If a member won't respond after a second request, escalate rather than forcing the delete. After delete, sweep any leftover `~/.claude/logs/verified/<team>/` sentinels (`TeamDelete` doesn't).
