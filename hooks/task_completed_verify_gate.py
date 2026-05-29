#!/usr/bin/env python3
"""TaskCompleted hook — presence + sentinel verification gate.

Exit 2 prevents the task from being marked complete unless BOTH hold:
  1. PRESENCE — the task carries a `Run: <command>` (a defined verification step), and
  2. SENTINEL — the completing teammate left a verification marker at
       ~/.claude/logs/verified/<team_name>/task-<task_id>.verified
     written AFTER its Run command passed.

Why a sentinel: the hook payload's transcript_path is the lead's session, not the
teammate's, so the hook cannot observe the teammate actually running tests. The
sentinel is the teammate's attestation. On a successful pass it is consumed
(deleted) so it cannot be reused for a later re-completion.

Teammate convention (documented in agent-team-protocol):
    mkdir -p ~/.claude/logs/verified/<team>
    echo "<Run cmd> PASSED" > ~/.claude/logs/verified/<team>/task-<id>.verified
    # then TaskUpdate(status=completed)

Bypass: token [skip-verify] in subject/description (e.g. docs-only tasks).
FAIL OPEN: any internal error allows the completion.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from team_hook_common import read_payload, allow, block, audit, VERIFIED_DIR  # noqa: E402

EVENT = "TaskCompleted"
RUN_CMD = re.compile(r"\bRun:\s*\S")


def sentinel_path(team, task_id):
    return os.path.join(VERIFIED_DIR, team or "_noteam", "task-{}.verified".format(task_id))


def main():
    p = read_payload()
    # Empty/unparseable payload (no task_id): can't assess — fail open, never block.
    if not p.get("task_id"):
        allow(EVENT, p, reason="incomplete payload (no task_id) — fail-open")

    text = "{}\n{}".format(p.get("task_subject", ""), p.get("task_description", ""))
    task_id = p.get("task_id", "?")
    team = p.get("team_name")

    if "[skip-verify]" in text.lower():
        allow(EVENT, p, reason="bypass token present")

    sp = sentinel_path(team, task_id)
    missing = []
    if not RUN_CMD.search(text):
        missing.append("task has no `Run:` verification command")
    if not os.path.exists(sp):
        missing.append(
            "verification sentinel not found at {0} — run the task's `Run:` command, then "
            "`mkdir -p {1} && echo PASSED > {0}` before completing".format(
                sp, os.path.dirname(sp)
            )
        )

    if missing:
        reason = (
            "Completion of task #{} blocked by the verification gate: {}.\n"
            "If this task genuinely needs no verification, add [skip-verify] to it."
        ).format(task_id, "; ".join(missing))
        block(EVENT, p, reason)

    # Passed: consume the sentinel so it can't be reused.
    try:
        os.remove(sp)
    except Exception:
        pass
    allow(EVENT, p, reason="verified (presence + sentinel)")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # FAIL OPEN
        audit(EVENT, {}, "allow", reason="hook error (fail-open): {}".format(e))
        sys.exit(0)
