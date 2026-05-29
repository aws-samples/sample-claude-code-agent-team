#!/usr/bin/env python3
"""TaskCreated hook — enforce task authoring format. Exit 2 rolls back creation.

Authoring rule (agent-team-protocol / spec-workflow): a task must carry a role
tag `[coding|devops|sa|sfdc]`, pipe-delimited `| <files> | <acceptance>`, and a
`Run: <command>`. The check runs on subject + description combined.

Bypass: include the token [skip-format-check] anywhere in the subject or
description for legitimate non-build / coordination tasks.

FAIL OPEN: any internal error allows the creation.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from team_hook_common import read_payload, allow, block, audit  # noqa: E402

EVENT = "TaskCreated"
ROLE_TAG = re.compile(r"\[(coding|devops|sa|sfdc)\]", re.I)
RUN_CMD = re.compile(r"\bRun:\s*\S")


def main():
    p = read_payload()
    # Empty/unparseable payload (no task_id): can't assess — fail open, never roll back.
    if not p.get("task_id"):
        allow(EVENT, p, reason="incomplete payload (no task_id) — fail-open")

    text = "{}\n{}".format(p.get("task_subject", ""), p.get("task_description", "")).strip()

    if "[skip-format-check]" in text.lower():
        allow(EVENT, p, reason="bypass token present")

    missing = []
    if not ROLE_TAG.search(text):
        missing.append("`[role]` tag — one of [coding] [devops] [sa] [sfdc]")
    if text.count("|") < 2:
        missing.append("`| <file paths> | <acceptance>` — both pipe-delimited sections")
    if not RUN_CMD.search(text):
        missing.append("`Run: <command>` — the verification command")

    if missing:
        reason = (
            "Task #{} rejected by format check. Missing: {}.\n"
            "Required shape: `[role] <verb> <what> | <files> | <acceptance>. Run: <command>`\n"
            "Fix and recreate, or add [skip-format-check] for a non-build task."
        ).format(p.get("task_id", "?"), "; ".join(missing))
        block(EVENT, p, reason)

    allow(EVENT, p, reason="format ok")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # FAIL OPEN
        audit(EVENT, {}, "allow", reason="hook error (fail-open): {}".format(e))
        sys.exit(0)
