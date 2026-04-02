# Documentation

Use these patterns when writing documentation, creating runbooks, or documenting system architecture.

## MCP Servers & Plugins

| Resource | When to Use |
|---|---|
| `deploy-on-aws` diagram skill | Generate architecture diagrams for system documentation and runbooks |
| `awslabs.aws-documentation-mcp-server` | Reference AWS service docs when writing architecture docs or runbooks — link to official docs rather than paraphrasing |
| `awslabs.document-loader-mcp-server` | Load external reference documents (PDFs, web pages) as source material for documentation |
| `context7` MCP | Look up library/framework docs to verify technical accuracy in README examples |
| `pr-review-toolkit:comment-analyzer` plugin | After writing any documentation — verifies accuracy, staleness risk, and maintainability |
| `github` plugin | Link to issues, PRs, and discussions from documentation. Create issues for documentation gaps |

## README Structure

```markdown
# Project Name

One-line description of what this does.

## Quick Start

\`\`\`bash
npm install
npm start
\`\`\`

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| PORT | Server port | 3000 |

## Usage

[Examples of common operations]

## Development

[How to set up dev environment, run tests]

## License

MIT
```

## API Documentation

Use OpenAPI/Swagger. Minimum per endpoint:
- HTTP method and path
- Request parameters (path, query, body)
- Response codes and schemas
- Authentication requirements
- Example request/response

## Runbook Template

```markdown
# [Service Name] Runbook

## Overview
What this service does, who owns it.

## Architecture
[Use `deploy-on-aws` diagram skill to generate architecture diagram]

## Health Checks
- Endpoint: `GET /health`
- Expected: 200 OK

## Common Issues

### Issue: High latency
**Symptoms**: Response times > 500ms
**Diagnosis**: Check DB connections, cache hit rate
**Resolution**: Scale horizontally, clear cache

## Escalation
- L1: On-call engineer
- L2: Service owner
- L3: Platform team
```

## Architecture Decision Record (ADR)

```markdown
# ADR-001: Use PostgreSQL for user data

## Status
Accepted

## Context
Need persistent storage for user accounts.

## Decision
Use PostgreSQL on RDS.

## Consequences
- Pro: ACID compliance, familiar tooling
- Con: Operational overhead vs DynamoDB
```

## Spec Artifact Documentation

When documenting within the spec-driven workflow, these artifacts have defined formats (see `.claude/rules/spec-workflow.md`):

| Artifact | Owner | Purpose |
|----------|-------|---------|
| `spec.md` | fullstack-agent | Design decisions, constraints, alternatives considered |
| `design.md` | fullstack-agent | Architecture, repo structure, infrastructure design |
| `tasks.md` | fullstack-agent (authored), all teammates (updated) | Parallelized task groups with completion notes |
| `review.md` | review-agent | Severity-rated findings with PASS/FAIL verdict |
| `sa-review.md` | sa-agent | Well-Architected findings by pillar, cost estimates |
| `decisions.md` | any agent via fullstack-agent | Mid-flight decisions to prevent re-litigation |

When writing documentation for a project that uses the spec workflow, link to relevant specs rather than duplicating their content.

## Agent Integration

- `devops-agent` owns READMEs, runbooks, and architecture docs — keeps them next to the code they describe
- `coding-agent` writes inline documentation (function/class/module docs) during implementation
- Both agents delegate to `pr-review-toolkit:comment-analyzer` after writing docs to verify accuracy
- `sa-agent` produces architecture review documentation in Well-Architected pillar format, claims and tracks tasks like other teammates
- Use `github` plugin to create issues for documentation that needs future updates (e.g., after API changes)

## Writing Tips

- Lead with the "what" and "why"
- Use concrete examples over abstract explanations
- Keep it scannable (headers, bullets, tables)
- Update docs when code changes (or automate it)
- Docs are concise and actionable — no filler
- Use the `deploy-on-aws` diagram skill for architecture diagrams — don't describe what a diagram can show
- Use `awslabs.document-loader-mcp-server` to load external specs or references rather than copy-pasting content
