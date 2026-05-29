#!/usr/bin/env python3
"""TeammateIdle hook — nudge a teammate to claim claimable work before idling.

Exit 2 keeps the teammate working and delivers the nudge via stderr. The hook
reads the team task store at ~/.claude/tasks/<team_name>/ and looks for tasks
that are ALL of:
  - status 'pending',
  - unclaimed (no owner),
  - unblocked (every id in blockedBy is completed/absent), and
  - tagged with this teammate's role (e.g. coding-agent -> [coding]).

LOOP GUARD (critical): a naive nudge would trap a teammate forever. State at
~/.claude/logs/idle-nudges/<team>__<teammate>.json tracks how many times we've
nudged for the *same* claimable set. After MAX_NUDGES the teammate is allowed to
idle. When the claimable set changes the counter resets; when it empties the
state file is cleared.

FAIL OPEN: any internal error allows idle.
"""
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from team_hook_common import (  # noqa: E402
    read_payload, allow, block, audit, load_team_tasks, role_of_teammate, NUDGE_DIR,
)

EVENT = "TeammateIdle"
MAX_NUDGES = 2


def _state_path(team, teammate):
    safe = "{}__{}".format(team, teammate).replace("/", "_")
    return os.path.join(NUDGE_DIR, safe + ".json")


def main():
    p = read_payload()
    team = p.get("team_name")
    teammate = p.get("teammate_name")
    role = role_of_teammate(teammate)
    state_path = _state_path(team, teammate)

    if not team or not role:
        allow(EVENT, p, reason="no team or unmapped role — not nudging")

    tasks = load_team_tasks(team)
    done = {tid for tid, t in tasks.items() if t.get("status") == "completed"}
    role_tag = re.compile(r"\[%s\]" % role, re.I)

    claimable = []
    for tid, t in tasks.items():
        if t.get("status") != "pending":
            continue
        if t.get("owner"):
            continue
        if any(b not in done for b in t.get("blockedBy", []) or []):
            continue
        if not role_tag.search("{} {}".format(t.get("subject", ""), t.get("description", ""))):
            continue
        claimable.append(tid)
    claimable.sort(key=lambda x: (len(x), x))

    if not claimable:
        # Nothing to do — let it idle and clear any stale nudge state.
        try:
            os.remove(state_path)
        except Exception:
            pass
        allow(EVENT, p, reason="no claimable tasks for role [{}]".format(role))

    sig = hashlib.sha1((",".join(claimable)).encode()).hexdigest()[:12]
    state = {}
    try:
        with open(state_path) as fh:
            state = json.load(fh)
    except Exception:
        state = {}
    count = state.get("count", 0) if state.get("sig") == sig else 0

    if count >= MAX_NUDGES:
        allow(EVENT, p, reason="nudge cap reached for set {} — allowing idle".format(sig))

    try:
        os.makedirs(NUDGE_DIR, exist_ok=True)
        with open(state_path, "w") as fh:
            json.dump({"sig": sig, "count": count + 1}, fh)
    except Exception:
        pass

    reason = (
        "Before idling: {} unclaimed, unblocked [{}] task(s) are available — "
        "#{}. Claim one with TaskUpdate(owner='{}', status='in_progress') and work it, "
        "or send the lead a one-line note that you're genuinely done. (nudge {}/{})"
    ).format(len(claimable), role, ", #".join(claimable), teammate, count + 1, MAX_NUDGES)
    block(EVENT, p, reason)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # FAIL OPEN
        audit(EVENT, {}, "allow", reason="hook error (fail-open): {}".format(e))
        sys.exit(0)
