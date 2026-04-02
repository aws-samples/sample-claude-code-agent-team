# PR Review

Use this when reviewing pull requests, preparing code for review, or running manual code review outside the spec-driven workflow.

## Plugins for Review

Delegate to these plugins in parallel for deeper automated analysis. Invoke all applicable plugins — they complement your own manual review.

**Always invoke:**
| Plugin | Purpose |
|---|---|
| `feature-dev:code-reviewer` | Confidence-scored bug and quality review (surfaces issues at >= 80% confidence) |
| `security-guidance` | Security best practices review — IAM, secrets, injection, OWASP Top 10 |

**Invoke when applicable:**
| Plugin | When |
|---|---|
| `pr-review-toolkit:silent-failure-hunter` | Code contains try/catch, error handling, or retry logic |
| `pr-review-toolkit:pr-test-analyzer` | Tests are added or modified |
| `pr-review-toolkit:type-design-analyzer` | New types, interfaces, or data models are introduced |
| `pr-review-toolkit:comment-analyzer` | Significant documentation or inline comments are added |
| `code-review:code-review` | Full-scope PR review with structured output |

**Synthesis:** After collecting plugin findings, deduplicate (keep the most specific version), drop false positives, and merge into your own review under the appropriate severity level.

## MCP Servers for Context

| MCP Server | When to Use |
|---|---|
| `context7` | Verify library API usage is correct — look up the library docs for functions used in the PR |
| `awslabs.cdk-mcp-server` | When reviewing CDK constructs — verify construct props and configuration patterns |
| `deploy-on-aws:awsiac` | When reviewing CloudFormation or CDK-generated templates — validate templates (`validate_cloudformation_template`), check compliance (`check_cloudformation_template_compliance`), get CDK best practices (`cdk_best_practices`) |
| `aws-serverless` plugin | When reviewing Lambda handlers — verify event schemas via `get_lambda_event_schemas`, check ESM configs via `esm_guidance`, validate IAM policies via `secure_esm_*_policy` tools |
| `databases-on-aws` plugin | When reviewing DSQL code — verify schema via `get_schema`, validate queries via `readonly_query`, check patterns via `dsql_recommend` |
| `awslabs.aws-documentation-mcp-server` | When reviewing AWS service integration code — verify API behavior, limits, error codes |
**Use MCP lookup when:** you're unsure whether an API is being used correctly, a resource property is valid, or a library function has the expected behavior. Verify before flagging.

## Review Methodology

Follow this sequence. Do not skip steps.

### Step 1: Understand Intent

Before reading code, understand what the PR is trying to do:
- Read the PR description, linked issues, or spec (if part of spec-driven workflow)
- Identify the acceptance criteria — what "done" looks like
- Note the scope — which files should be changed and which should not

### Step 2: Structural Review

Scan the changeset at a high level:
- Are the right files modified? Any unexpected additions or deletions?
- Is the change scoped correctly, or does it mix unrelated concerns?
- Are new files in the right directories following project conventions?

### Step 3: Code Analysis

Read each changed file and evaluate:

**Correctness**
- Does the code do what the PR description says?
- Are edge cases handled (null, empty, boundary values, concurrent access)?
- Is error handling complete — no swallowed exceptions, no missing error paths?
- Are there race conditions, null derefs, or off-by-one errors?

**Security**
- Secrets management (**Critical**): Verify no hardcoded secrets: `grep -r "(password|api[_-]\?key|secret|token)\s*=\s*[\"']" --include="*.{py,js,ts}"` (expect: zero matches). All secrets must use AWS Secrets Manager: `aws secretsmanager create-secret --name <name> --secret-string <value>`
- Input validation (**Critical**): Implement sanitization at trust boundaries using parameterized queries for SQL, allowlist validation for user input
- IAM least-privilege (**Critical**): Verify using `aws iam simulate-principal-policy --policy-source-arn <arn> --action-names <actions>` (expect: Deny for unused actions)
- No injection vulnerabilities: SQL, command, template, XSS, SSRF
- OWASP Top 10 for web-facing code

**Performance**
- No N+1 queries or unnecessary loops over collections
- Appropriate data structures for the access patterns
- Resource cleanup — connections, file handles, streams, timers
- No blocking calls in async contexts

**Maintainability**
- Clear naming — would a new team member understand this without context?
- No unnecessary complexity or premature abstraction
- Follows existing project conventions and patterns
- Tests added/updated for new behavior

**Infrastructure (when IaC is in scope)**
- Resources tagged consistently (service, environment, owner, cost-center)
- Secrets managed properly — AWS Secrets Manager or Parameter Store, a capability of AWS Systems Manager — do not inline
- Config parameterized — no hardcoded account IDs, regions, AZs
- Outputs exported for downstream consumers with correct names/types
- Encryption at rest configured for all stateful resources (S3, DynamoDB, RDS, EBS) using AWS Key Management Service (AWS KMS) keys — **Critical** if missing
- Encryption in transit enforced (TLS/HTTPS endpoints, database connections) — **Critical** if missing
- Key management strategy documented (key rotation, access policies) — **Warning** if missing
- Data classification tags present on resources handling sensitive data — **Warning** if missing
- Access logging enabled (CloudTrail, S3 access logs, database audit logs) — **Warning** if missing
- S3 bucket policies enforce TLS/HTTPS using `aws:SecureTransport` condition (deny when false) — **Critical** if missing
- Block Public Access (BPA) enabled on all S3 buckets — **Critical** if missing (unless public access is explicitly documented and justified)
- Versioning enabled for S3 buckets containing critical data — **Warning** if missing
- MFA Delete configured for S3 buckets with sensitive data — **Warning** if missing
- BYOK (customer-managed KMS keys) usage documented and flagged for security review — **Warning** if not documented
- For infrastructure tasks creating stateful resources, acceptance criteria MUST include: (1) Encryption at rest verified via `aws <service> describe-*` commands, (2) Encryption in transit verified (TLS 1.2+), (3) Access logging enabled and verified, (4) Data classification tags present. Example: `Create S3 bucket | infra/bucket.tf | Bucket created with KMS encryption, versioning enabled, access logging to audit bucket, data-classification tag applied. Run: aws s3api get-bucket-encryption --bucket <name> && aws s3api get-bucket-logging --bucket <name>`

### Step 4: Cross-File Consistency

When the PR spans multiple files:
- Do interfaces match between producers and consumers?
- Are naming conventions consistent across files?
- Are there conflicting assumptions between different parts of the change?

## Severity Calibration

Use these severity levels consistently:

| Severity | Criteria | Blocks merge? |
|----------|----------|---------------|
| **Critical** | Runtime failures, security vulnerabilities (Severe/High), data loss risks, interface contract violations | Yes |
| **Warning** | Performance issues, missing error handling, fragile patterns, Medium security issues, spec deviations | Yes |
| **Suggestion** | Style improvements, refactoring opportunities, Low security issues, documentation gaps | No |

## Output Format

```markdown
### Critical
- [`file:line`] Description — recommended fix

### Warning
- [`file:line`] Description — recommended fix

### Suggestion
- [`file:line`] Description — improvement idea

### Verdict: APPROVE | REQUEST CHANGES

Reason: <one-line summary if REQUEST CHANGES>
```

**APPROVE** only if zero Critical and zero Warning findings. Suggestions don't block.

## Agent Integration

When this skill is used within the spec-driven workflow:
- **review-agent** uses its own enhanced methodology (with spec alignment, cross-task consistency, review cycle focus). This skill is for ad-hoc reviews outside that workflow
- If reviewing code produced by `coding-agent` or `devops-agent`, check their completion notes in `tasks.md` — verify claimed verification results match the code
- Use `github` or `gitlab` plugin to post review comments directly on PRs when reviewing in a Git platform context

## Common Issues to Flag

- Hardcoded credentials or API keys
- Missing input validation on external boundaries
- Unhandled promise rejections or swallowed exceptions
- Console.log / print statements left in production code
- TODO/FIXME/HACK comments without linked issues
- Secrets in environment variables that should be in AWS Secrets Manager
- Mutable shared state without synchronization
- Missing `await` on async calls
- Catch blocks that silently discard errors
