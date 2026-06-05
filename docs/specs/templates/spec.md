# Spec: <Title>

> Slug: `<kebab-case-slug>` · Status: Draft | Approved | In Progress | Done · Last updated: YYYY-MM-DD

## Problem / Goal

What we're solving and why. The user-facing or business outcome. One paragraph.

## Requirements

### Functional
- <requirement> — <acceptance signal>

### Non-Functional
- Performance / latency / throughput targets
- Security & compliance constraints (see `rules/AWS-security-guidelines.md`)
- Cost ceiling (if any)
- Operability (logging, metrics, alarms)

## Constraints & Assumptions

- Hard constraints (existing systems, contracts, deadlines, tech mandates)
- Assumptions we're making (flag any that need validation)

## Design Decisions

| Decision | Choice | Alternatives Considered | Rationale |
|---|---|---|---|
| <topic> | <what we chose> | <what we rejected> | <why> |

## Interfaces & Contracts

Shared types, API signatures, resource names/ARNs, event schemas that tasks produce or consume. Pin exact signatures so dependent tasks run in parallel without blocking.

## Edge Cases & Risks

- <edge case> → expected behavior
- <risk> → mitigation / reversibility

## Out of Scope

What this spec deliberately does NOT cover.

## Open Questions

- [ ] <question needing an answer before/while building>
