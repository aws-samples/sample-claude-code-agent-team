# Security

This document provides a security overview of the Claude Code Multi-Agent Development Sample, including a threat model, AI security controls, and risk assessment.

> **Note**: This repository is a sample configuration — not a production application. The security analysis below documents risks inherent in multi-agent AI workflows and the mitigations built into this configuration.

## Threat Model

### 1. Agent Isolation and Trust Boundaries

**Threat:** Agents execute in the same Claude Code session with shared file system access. An agent operating outside defined scope due to configuration error or logic fault may perform unauthorized file system modifications beyond its assigned scope.

**Mitigations** (require user configuration and ongoing verification):
- Agent team protocol (`skills/agent-team-protocol/`) restricts each agent to files listed in its task assignment — users must define and maintain these restrictions
- Verification gate requires agents to confirm they only modified assigned files before marking tasks complete — users must enforce this gate in their workflow
- `review-agent` independently verifies changes match task scope — users must include review-agent in their team composition
- Claude Code's permission system prompts the user before executing potentially dangerous operations — users must review and respond to these prompts

### 2. Credential Scope and AWS Access

**Threat:** Agents interacting with AWS services may perform unauthorized privilege escalation through IAM policy exploitation, access resources outside authorized scope, or execute unauthorized modifications to production infrastructure.

**Mitigations** (require user configuration and ongoing verification):
- AWS security guidelines (`rules/AWS-security-guidelines.md`) mandate ReadOnly/least-privilege credentials for read operations — users must configure appropriate AWS profiles and IAM policies
- Agents must assume resources are production unless proven otherwise — users must verify agents follow this convention
- Destructive operations (delete, terminate, modify) require explicit user confirmation — users must not grant blanket approval
- AWS Security Token Service (AWS STS) identity verification via `aws sts get-caller-identity` is required before any AWS operation — users must ensure credentials are correctly scoped
- Safety controls (termination protection, deletion protection, MFA delete) must never be disabled without user confirmation — users must review all safety control changes

### 3. File System Access

**Threat:** Agents have read/write access to the local file system and may perform unauthorized file system modifications to system configuration files, overwrite uncommitted work, or access sensitive data outside authorized scope.

**Mitigations** (require user configuration and ongoing verification):
- Claude Code's built-in permission system gates file operations — users must review permission prompts and not grant overly broad access
- Spec-driven workflow constrains agents to spec-defined file paths — users must define accurate file paths in specs
- Agent team protocol requires agents to stay within task scope — users must verify compliance during review
- The `non-interactive` skill requires agents to run commands without bypassing confirmation prompts — users must keep the skill available in their configuration

### 4. MCP Server Trust

**Threat:** MCP servers are external services that agents communicate with. MCP server compromise may result in data manipulation, prompt injection attacks, or unauthorized data exfiltration.

**Mitigations** (require user configuration and ongoing verification):
- All configured MCP servers are either official AWS services or well-known public services — users must vet any additional MCP servers before adding them
- MCP servers are used for documentation lookup and diagram generation — not for executing privileged operations — users must verify new servers do not require privileged access
- Claude Code flags suspected prompt injection in tool results — users must review flagged results and act accordingly
- Users can review and approve/deny MCP server tool calls via the permission system — users must actively monitor and respond to these prompts

### 5. Plugin Security

**Threat:** Plugins execute code within the Claude Code session and may access data outside authorized scope boundaries.

**Mitigations** (require user configuration and ongoing verification):
- All configured plugins come from vetted marketplaces — the official Claude Code marketplace (`claude-plugins-official`) and the AWS Labs marketplace (`agent-plugins-for-aws`, declared in `extraKnownMarketplaces`). Users must review plugin permissions before enabling and vet any additional marketplaces before adding them
- Plugins operate within Claude Code's permission framework — users must maintain appropriate permission settings
- The `pr-review-toolkit` and `code-review` plugins provide specialized security and quality review — users must include these plugins in their configuration and act on their findings

## AI Security Controls

### Input Validation

- Claude Code's built-in safety system validates user prompts and agent communications
- The system flags suspected prompt injection attempts in tool results and MCP responses
- Agent instructions include explicit constraints on scope and behavior (each agent's markdown definition)

### Output Filtering

- Claude Code applies content safety measures to all generated output
- `review-agent` independently verifies implementation correctness and security
- The spec-driven workflow requires explicit PASS from `review-agent` before work is accepted

### Rate Limiting and Abuse Prevention

- Claude Code sessions are governed by Anthropic's API rate limits and usage policies
- Agent team protocol limits review cycles to 3 per group before escalating to the user
- Same-blocker-twice rule forces escalation rather than infinite retry loops

### Monitoring and Logging

- All agent interactions occur within the Claude Code session and are visible to the user
- Task coordination (`TaskCreate`/`TaskUpdate`/`TaskList`) provides an audit trail of agent actions
- `decisions.md` logs mid-flight architectural decisions
- `review.md` documents review findings per cycle

### Incident Response

1. **Suspicious agent behavior**: User can deny any tool call via Claude Code's permission system
2. **Unexpected AWS changes**: Production safety rules require confirmation for destructive operations; use `aws cloudformation describe-stack-events` to audit
3. **Compromised MCP server**: Remove the server entry from `.mcp.json` and restart the session
4. **Review failure loop**: After 3 cycles, the system escalates to the user for manual intervention

## Bias and Fairness

This section addresses bias and fairness considerations for the multi-agent system. Because this repository is a **sample configuration** — not a production application that processes user data or makes consequential decisions — many traditional bias concerns do not directly apply. The agents generate infrastructure code and review it; they do not make decisions about people.

### Code Generation and Architectural Decisions

The agents rely on Claude models, which may reflect biases present in their training data. In practice, this could surface as:
- Defaulting to specific AWS services, patterns, or regions without considering alternatives
- Over-engineering or under-engineering based on patterns seen in training data

**Mitigation:** The spec-driven workflow requires explicit architectural decisions documented in `design.md` and `decisions.md`. The `sa-agent` provides Well-Architected reviews that challenge assumptions. All decisions are visible to the user for override.

### Task Delegation and Review Processes

Task delegation is deterministic — tasks are assigned by role prefix (`[coding]`, `[devops]`, `[sa]`) defined in `tasks.md` by the team lead. The `review-agent` applies the same review criteria to all code regardless of which agent produced it. There is no adaptive or learned behavior that could develop bias over time.

### Monitoring for Biased Outputs

- All agent outputs are visible in the Claude Code session
- `review-agent` independently evaluates all implementations against the same criteria
- `decisions.md` provides an audit trail of architectural choices for human review
- The max-3-review-cycles rule with user escalation ensures a human reviews persistent disagreements

### Human Oversight Mechanisms

- Claude Code's permission system requires user approval for potentially impactful operations
- The spec-driven workflow has explicit human review points (spec approval, diff review, deployment approval)
- Production safety rules gate all destructive AWS operations behind user confirmation
- Users can deny any tool call and override any agent decision

### Known Model Limitations

The Claude models used by these agents have known limitations regarding bias:
- Training data biases may influence code style, library choices, and architectural preferences
- Models may not equally represent all programming paradigms, languages, or cloud providers
- Generated code patterns may reflect biases toward certain community conventions over others
- Models have a knowledge cutoff and may not reflect the latest best practices

Users should treat agent outputs as recommendations subject to human judgment, not as authoritative decisions.

## Claude Code Responsibility Model

> **Important**: The security controls described in this document are required controls that users must actively implement, configure, and maintain. Failure to implement these controls may result in unauthorized access, data exposure, or unintended infrastructure modifications.

### Anthropic/Claude Code Platform Responsibilities

Anthropic is responsible for the following platform-level security controls:

- Claude Code platform security and infrastructure
- API authentication and authorization
- Model safety controls and content filtering
- Rate limiting and abuse prevention
- Prompt injection detection in tool results

### User Responsibilities

Users MUST implement and maintain the following security controls. Failure to implement these controls may result in unauthorized access, data exposure, or unintended infrastructure modifications:

- Secure agent configuration and rule definitions — users must define and maintain agent scope restrictions
- AWS credential management and least-privilege IAM policies — users must configure appropriate IAM roles and rotate credentials
- MCP server security review and approval — users must vet all MCP servers before adding them to `.mcp.json`
- File system access controls and sensitive data protection — users must review and respond to Claude Code permission prompts
- Production safety rule enforcement — users must not grant blanket approval for destructive operations
- Ongoing verification that security controls remain correctly configured — users must periodically audit agent configurations and access policies

## AWS Shared Responsibility Model

When agents interact with AWS services via MCP servers or CLI commands, the standard [AWS Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/) applies.

**Core Principle:** AWS is responsible for **security OF the cloud** (physical infrastructure, compute, storage, networking, and managed service infrastructure). Users are responsible for **security IN the cloud** (customer data, IAM policies, OS patching, network configuration, and encryption).

### Security OF the Cloud (AWS Responsibility)

- Physical security of data centers and global infrastructure
- Managed service infrastructure (compute, storage, networking, databases)
- Hypervisor and host OS security for managed services
- Service availability and durability guarantees

### Security IN the Cloud (User Responsibility)

- **Identity and access management**: Least-privilege IAM policies, credential rotation, MFA enforcement
- **Data protection**: Encryption key management, data classification, retention policies
- **OS and application patching**: EC2 instance OS updates, security groups, instance metadata controls
- **Network configuration**: VPC design, subnet isolation, security group rules, NACLs
- **Service-specific configuration**: S3 encryption and public access blocks, database authentication and audit logging
- **Monitoring and compliance**: AWS CloudTrail, AWS Config rules, Amazon GuardDuty, AWS Security Hub

## Implementation Guide

Implement security controls in phased priority order. See `agents/devops-agent.md` Data Security section for the detailed S3 implementation pattern.

### Phase 1: Credential Scope (Threat Model §2)

Configure least-privilege IAM for agent operations:
```bash
aws iam create-policy --policy-name claude-code-readonly --policy-document file://readonly-policy.json
aws iam attach-user-policy --user-name claude-code-user --policy-arn arn:aws:iam::<account>:policy/claude-code-readonly
```
Verify: `aws iam simulate-principal-policy --policy-source-arn arn:aws:iam::<account>:user/claude-code-user --action-names s3:DeleteBucket ec2:TerminateInstances --resource-arns "*"` (expect: Deny for all write/delete operations)

### Phase 2: File System Access (Threat Model §3)

Configure Claude Code permission settings to restrict file operations:
- Review and set permission mode to limit automatic file access: `claude config set --project permissions.mode restricted`
- Define allowed paths in agent task assignments via `tasks.md` file path column
- Verify: `git diff --name-only` lists only files assigned in the agent's task scope (expect: 100% match with task assignments)
- Audit: review-agent checks modified files against task scope each review cycle

### Phase 3: MCP Server Trust (Threat Model §4)

Vet all MCP servers before adding to `.mcp.json`:
- Review server source code or documentation for data handling practices
- Verify servers do not require privileged AWS credentials: `cat .mcp.json | jq '.mcpServers[] | .command, .args'` (expect: no credential flags or secret references)
- Remove any unreviewed third-party servers: `cat .mcp.json | jq '.mcpServers | keys'` (expect: only approved servers from the MCP Server Legal Approval table)
- Validate server integrity: `npx @anthropic/mcp-validator <server-name>` (expect: PASS for all security checks)

### Acceptance Criteria

Each phase must be verified before proceeding to the next:
- Phase 1: `aws sts get-caller-identity` returns a least-privilege role; `aws iam simulate-principal-policy` returns Deny for unused actions
- Phase 2: `review-agent` confirms all file modifications are within task scope
- Phase 3: All MCP servers in `.mcp.json` have completed security review

## Risk Assessment

### Security Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Agent modifies files outside task scope | Low | Medium | Agent protocol file restrictions + review-agent verification |
| AWS credential misuse by agent | Low | High | Production safety rules + ReadOnly defaults + user confirmation gates |
| Hardcoded secrets in generated code | Medium | High | review-agent security checks + pr-review-toolkit plugin |
| MCP server returns manipulated data | Low | Medium | Prompt injection detection + user-visible tool results |
| Plugin accesses unintended data | Low | Low | Claude Code permission framework + marketplace-only plugins |

### Compliance Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Sensitive data in agent-generated code | Medium | High | review-agent checks + pr-review-toolkit plugin + AWS-security-guidelines rule |
| AWS service usage without proper authorization | Low | Medium | Production safety rules + credential verification before operations |
| Data handling by AI agents | Medium | Medium | All processing occurs locally in the user's Claude Code session |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Agent coordination failure | Medium | Low | Task tracking system + SendMessage protocol + blocker escalation |
| Uncontrolled AWS resource creation | Low | High | CDK diff review + user confirmation + cost-center tagging |
| Review cycle infinite loop | Low | Low | Max 3 review cycles then escalate |
| Agent generates incorrect IaC | Medium | Medium | cdk synth + cdk diff + review-agent + sa-agent Well-Architected review |
