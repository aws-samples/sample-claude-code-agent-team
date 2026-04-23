# Spec-Driven Workflow

## When to Create a Spec

Create a spec before any non-trivial work — if it touches multiple files, involves architectural choices, or will be delegated to an agent team.

## Directory Structure

```
.claude/specs/<slug>/
  spec.md          # Design decisions, requirements, constraints
  design.md        # Architecture, repo structure, infrastructure design (optional)
  tasks.md         # Parallelized task list with agent assignments
  review.md        # review-agent findings per cycle (PASS/FAIL)
  sa-review.md     # sa-agent Well-Architected findings (optional)
  decisions.md     # Mid-flight decision log
  requirements.md  # From /brainstorm (optional)
  prd/             # Product requirements docs (optional)
```

Use short kebab-case slugs (e.g., `auth-api`, `vpc-redesign`).

## Task Format (`tasks.md`)

Tasks organized into parallel groups. All tasks in a group execute simultaneously; groups execute sequentially.

```markdown
## Group 1: <description>
Spec ref: `spec.md#<section>` — <what this implements>.
- [ ] [coding] <verb> <what> | `path/to/files` | <acceptance criteria>. Run: `<command>`
- [ ] [devops] <verb> <what> | `path/to/files` | <acceptance criteria>. Run: `<command>`
```

### Task Rules

- Each task is self-contained — completable without knowledge of sibling tasks
- Prefixed `[coding]`, `[devops]`, or `[sa]` for agent assignment
- Explicit file paths (no two tasks in same group write to same file)
- Interface contracts inline if producing/consuming shared interfaces (exact signatures)
- Verification command included
- Small enough for one teammate in a single session

### Task Coordination

Tasks tracked in two synced places:
1. `tasks.md` — full context, completion notes, blocker details
2. Shared task list — `TaskCreate`/`TaskUpdate`/`TaskList` for real-time coordination

### Parallelization Guidelines

Maximize parallelism: no shared file writes -> same group. Infrastructure before app code. Shared interfaces before consumers. SA review runs parallel with implementation (reviews design, not code).

## Development Loop

Plan -> Build (per group) -> Review -> Fix (if FAIL) -> Cleanup. See `fullstack-agent.md` for the detailed phase steps.

**Security scan remediation priority**: (1) Critical findings — immediate fix required. Run scans: `bandit -r src/ -f json -o .claude/specs/<slug>/bandit-results.json`, `semgrep --config auto --json -o .claude/specs/<slug>/semgrep-results.json`, `safety check --json > .claude/specs/<slug>/safety-results.json`, `checkov -d infra/ -o json > .claude/specs/<slug>/checkov-results.json`. (2) High findings — fix or document risk acceptance with compensating controls before merge, (3) Medium findings — fix within sprint or document acceptance.

**Acceptance criteria MUST include verification in priority order**: (1) Encryption at rest verified via `aws <service> describe-<resource> | jq '.EncryptionConfiguration'` (expect: AWS KMS key ARN present) — blocks deployment, (2) Encryption in transit verified via `aws <service> get-<resource>-policy` (expect: `aws:SecureTransport` condition present) — blocks deployment, (3) Access logging enabled via `aws <service> get-<resource>-logging` (expect: logging target configured) — required for review PASS, (4) Data classification tags via `aws <service> list-tags-of-resource` (expect: `data-classification` tag present) — required for review PASS.

**Serverless-specific acceptance criteria**: For Lambda tasks, verify event schema conformance via `get_lambda_event_schemas` from `aws-serverless` plugin. For SAM deployments, verification MUST include `sam_build` + `sam_local_invoke` (local test) before `sam_deploy`. For API Gateway, verify authorization is configured on all routes. For Aurora DSQL tasks, verify schema via `get_schema` and test queries via `readonly_query` from `databases-on-aws` plugin. For Amplify tasks, verify sandbox deployment succeeds before production.

**Completion criteria**: Zero criticals + zero warnings + all tests passing + all tasks `[x]`. Suggestions don't block.

**Safeguards**: Max 3 review cycles per group, then escalate. Log decisions in `decisions.md`. Same blocker twice -> escalate to user.

## Spec and Document Formats

If `.claude/specs/templates/` exists, use the templates there as starting points for `spec.md`, `design.md`, `review.md`, `sa-review.md`, `decisions.md`, and `prd.md` — they are examples, not rigid constraints. If the directory is absent, follow the section structures described in this file and in the agent definitions. Any `design.md` MUST include a Security Considerations section regardless of template availability.
