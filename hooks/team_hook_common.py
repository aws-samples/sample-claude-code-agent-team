"""Shared helpers for the agent-team enforcement hooks.

Imported by task_created_format_check.py, task_completed_verify_gate.py and
teammate_idle_workcheck.py. Responsibilities:
  - parse the stdin JSON payload the harness delivers to a hook,
  - append an audit record to ~/.claude/logs/team-hooks.jsonl for every decision,
  - implement the documented exit-code contract: 0 = proceed, 2 = block + the
    stderr text is fed back as the reason.

Design rule for ALL hooks: FAIL OPEN. Any unexpected condition must resolve to
allow() — a hook bug must never be able to roll back a task, prevent a valid
completion, or trap a teammate. Enforcement is a guardrail, not a tripwire.
"""
import json
import os
import sys
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
LOG_DIR = os.path.join(HOME, ".claude", "logs")
LOG_PATH = os.path.join(LOG_DIR, "team-hooks.jsonl")
TASKS_DIR = os.path.join(HOME, ".claude", "tasks")     # ~/.claude/tasks/<team>/<id>.json
VERIFIED_DIR = os.path.join(LOG_DIR, "verified")        # completion sentinels
NUDGE_DIR = os.path.join(LOG_DIR, "idle-nudges")        # idle loop-guard state


def read_payload():
    """Read and parse the hook stdin payload. Returns {} on empty/invalid."""
    raw = sys.stdin.read()
    try:
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def audit(event, payload, decision, reason=None, extra=None):
    rec = {"captured_at": _now(), "event": event, "decision": decision}
    if reason:
        rec["reason"] = reason
    if extra:
        rec.update(extra)
    rec["payload"] = payload
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG_PATH, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
    except Exception:
        pass  # logging must never break a hook


def allow(event=None, payload=None, reason=None, extra=None):
    """Permit the action (exit 0). Audits if an event is given."""
    if event is not None:
        audit(event, payload, "allow", reason, extra)
    sys.exit(0)


def block(event, payload, reason, extra=None):
    """Block the action (exit 2). stderr is fed back as the reason."""
    audit(event, payload, "block", reason, extra)
    print(reason, file=sys.stderr)
    sys.exit(2)


def role_of_teammate(name):
    """Map a teammate name (e.g. 'coding-agent') to its task role tag, or None."""
    if not name:
        return None
    n = name.lower()
    # Order matters only for disjoint prefixes; our roles don't overlap.
    for role in ("coding", "devops", "sfdc", "sa", "review"):
        if n == role or n.startswith(role + "-") or n.startswith(role):
            return role
    return None


def load_team_tasks(team_name):
    """Load every <id>.json in ~/.claude/tasks/<team_name>/ as {id: task_dict}."""
    tasks = {}
    if not team_name:
        return tasks
    d = os.path.join(TASKS_DIR, team_name)
    try:
        names = os.listdir(d)
    except Exception:
        return tasks
    for fn in names:
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(d, fn)) as fh:
                t = json.load(fh)
            tasks[str(t.get("id", fn[:-5]))] = t
        except Exception:
            continue
    return tasks
