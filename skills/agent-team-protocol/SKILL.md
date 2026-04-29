# Agent Team Protocol

Shared protocol for all agent team teammates. The team lead (fullstack-agent) coordinates; all others are teammates.

## Teammate Lifecycle

1. Receive delegation via `SendMessage` from the team lead with spec path and task assignments
2. Read `spec.md` and `design.md` before any work
3. Claim tasks via `TaskUpdate` (-> `in_progress`), check context in `tasks.md`. Respect task dependencies — blocked tasks auto-unblock when dependencies complete
4. Implement exactly what each task describes
5. Self-verify (see below), then mark complete via `TaskUpdate` (-> `completed`)
6. Update `tasks.md` with `[x]` and a `> Done.` completion note
7. Notify team lead via `SendMessage`; after finishing, self-claim unclaimed tasks for your role

## Communication Rules

- **Direct to teammates**: Interface clarifications, dependency questions, sharing outputs they need
- **To the lead**: Blockers needing decisions, completion reports, scope/spec questions
- Tools: `SendMessage` (to any teammate), `TaskUpdate` (claim/complete), `TaskList`/`TaskGet` (status)

## Completion Reporting

Update both places and notify:
1. `TaskUpdate` -> `completed`
2. `tasks.md`: `- [x] [role] description` with `> Done. <summary>` note
3. `SendMessage` to team lead (and relevant teammates if they depend on your output)

## Blocker Reporting

Mark `[!]` in `tasks.md` with specific blocker details. `SendMessage` to team lead. If the same blocker persists after two attempts, the lead escalates to the user.

## Verification Gate (All Teammates)

Before marking ANY task complete:
1. Run the verification command specified in the task
2. Confirm interface/output contracts match the task spec exactly
3. Confirm you only modified files listed in your task assignment

If verification fails and you can't fix it within scope, mark `[!]` with the specific failure.

## Handling Ambiguity

- **Missing details**: Check `spec.md` and `design.md` first. If not there, `SendMessage` to lead or relevant teammate
- **Multiple valid approaches**: Pick the simplest that satisfies acceptance criteria
- **Out-of-scope issues**: Note in completion report, don't fix
- **Conflicting requirements**: Mark `[!]`, never silently pick one interpretation
- **Dependency on another teammate**: `SendMessage` to them directly, then `[!]` if not ready

## Shutdown

When the lead sends a shutdown request, finish current work, ensure tasks are properly marked in both the shared task list and `tasks.md`, then approve.
