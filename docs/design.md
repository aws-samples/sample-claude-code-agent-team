# Multi-Agent System Architecture

This document describes the architecture of the Claude Code multi-agent development system and the security considerations that informed its design.

## System Overview

The system consists of a team lead agent (`fullstack-agent`) that coordinates specialized teammates through a spec-driven build-review loop. Agents communicate via shared tasks and direct messaging within a single Claude Code session.

```
User -> fullstack-agent (plan) -> [coding-agent, devops-agent] (build in parallel) -> review-agent (verify) -> fullstack-agent (next group or fix)
```

## Agent Roles

| Agent | Responsibility | Model | Writes To |
|-------|---------------|-------|-----------|
| fullstack-agent | Architecture, planning, coordination | opus | spec.md, design.md, tasks.md, decisions.md |
| coding-agent | Application code and tests | opus | Source code, test files |
| devops-agent | Infrastructure, CI/CD, containers, docs | sonnet | IaC files, CI configs, READMEs |
| review-agent | Code review and quality verification | opus | review.md only |
| sa-agent | Well-Architected reviews (on-demand) | sonnet | sa-review.md |

## Coordination Model

Agents coordinate through two mechanisms:
1. **Shared task list** (`TaskCreate`/`TaskUpdate`/`TaskList`) — real-time status tracking
2. **Direct messaging** (`SendMessage`) — interface clarifications, blocker notifications, review handoffs

The team lead owns the workflow lifecycle: spawning teammates (`TeamCreate`), delegating work, monitoring progress, and cleaning up (`TeamDelete`).

## Security Considerations

For the full threat model and risk assessment, see [SECURITY.md](../SECURITY.md).

### 1. Agent Isolation and File Access Boundaries

Agents share the same file system within a Claude Code session. Isolation is enforced through convention, not hard boundaries:

- **Task-scoped file assignments**: Each task explicitly lists the files an agent may modify. No two tasks in the same group write to the same file.
- **Verification gate**: Agents must confirm they only modified assigned files before marking tasks complete.
- **Review-agent audit**: The review agent independently verifies that changes match task scope during each review cycle.
- **Worktree isolation**: When file overlap is unavoidable, agents run in separate git worktrees (`isolation: "worktree"`).

**Risk**: Task configuration error may result in unauthorized file system access beyond assigned scope. Mitigation depends on accurate task definitions and review-agent enforcement.

### 2. Credential Management and AWS Access Patterns

Agents may interact with AWS services via MCP servers or CLI commands. Credential security follows these principles:

- **Least-privilege by default**: Production safety rules (`rules/amazon-builder-production-safety.md`) mandate ReadOnly credentials for read operations.
- **Assume production**: Agents treat all resources as production unless explicitly proven otherwise.
- **User confirmation gates**: Destructive operations (delete, terminate, modify) require explicit user approval through Claude Code's permission system.
- **Identity verification**: AWS Security Token Service (AWS STS) identity check via `aws sts get-caller-identity` is required before any AWS operation to confirm credential scope.
- **AWS security guidelines**: Service-specific security requirements are defined in `rules/AWS-security-guidelines.md` and verified during review, with findings requiring user action to remediate. Coverage includes Lambda, DynamoDB, RDS, EBS, S3, API Gateway, Aurora DSQL, and Amplify Gen 2.

**Risk**: Agents may perform unauthorized privilege escalation or access resources outside authorized scope through exploitation of overly permissive credentials. Users must configure appropriate IAM policies and review all AWS operations.

### 3. Inter-Agent Communication Security and Trust Model

Agents communicate through Claude Code's built-in messaging and task systems. The trust model is:

- **Flat trust within the team**: All agents in a team are equally trusted within their assigned scope. There is no privilege escalation between agents.
- **Lead-controlled workflow**: Only the team lead spawns teammates, creates tasks, and manages the review loop. Teammates cannot spawn other agents or modify the workflow.
- **No inherited context**: Teammates do not inherit the lead's conversation history. They receive only the spec path, task assignments, and explicit context via `SendMessage`.
- **Review as verification**: The review agent provides an independent check on all implementation work. It cannot be bypassed — the workflow requires an explicit PASS verdict before proceeding.
- **Blocker escalation**: Persistent disagreements (same blocker twice, 3 failed review cycles) escalate to the user rather than being resolved autonomously.

**Risk**: Agent compromise or logic fault may result in transmission of manipulated messages to other agents. Mitigation relies on the review agent's independent verification and user oversight of the session.
