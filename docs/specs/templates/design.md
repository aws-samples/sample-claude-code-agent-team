# Design: <Title>

> Architecture, repository structure, and infrastructure design for `<slug>`. The **Security Considerations** section below is MANDATORY (per `spec-workflow` skill) regardless of template use.

## Architecture Overview

High-level description + a diagram (link or ASCII). Components and how requests/data flow between them.

## Repository / Module Structure

```
<tree of dirs and key files this work will create or touch>
```

## Components

### <Component Name>
- **Responsibility:** <what it owns>
- **Interface:** <public API / events / inputs & outputs>
- **Dependencies:** <upstream/downstream>

## Data Model

Entities, schemas, storage choices, retention. Note data classification for anything sensitive.

## Infrastructure Design

AWS services, IaC approach (CDK/Terraform/SAM/CFN), environments, deploy/rollback strategy. Outputs (ARNs, endpoints, table names) other components or app code consume.

## Security Considerations (MANDATORY)

> Reconcile against `rules/AWS-security-guidelines.md`. Do not omit this section.

- **Authentication & Authorization:** identity model, least-privilege IAM, scoping
- **Encryption at rest:** KMS keys per resource (blocks deployment if absent)
- **Encryption in transit:** TLS / `aws:SecureTransport` enforcement (blocks deployment if absent)
- **Secrets management:** Secrets Manager / Parameter Store — never inline
- **Network:** VPC, security groups, public exposure, endpoints
- **Logging & audit:** access logging enabled, CloudTrail, retention
- **Data classification & tagging:** `data-classification` tag on sensitive resources
- **Threat model notes:** key abuse cases and mitigations (link `.threatmodel/` if present)

## Trade-offs & Alternatives

What was considered and rejected, with reasoning.

## Open Design Questions

- [ ] <question>
