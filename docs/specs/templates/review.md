# Review: <slug>

> Reviewer instances write here. The team lead does NOT author this file (self-review is a category error). For parallel per-scope review, each reviewer owns `review-<scope>.md` instead; the lead consolidates verdicts (any FAIL ⇒ group FAILs).

## Cycle N — YYYY-MM-DD

Reviewing: Group M — <description> [scope: <your scope>]

### Spec Alignment
Does each task satisfy its acceptance criteria and interface contracts? Note deviations.

### Critical
- [`file:line`] Issue and recommended fix
  > Critical = runtime failures, Severe/High security, data loss, broken contracts.

### Warning
- [`file:line`] Issue and recommended fix
  > Warning = perf issues, missing error handling, Medium security, unjustified deviations.

### Suggestion
- [`file:line`] Improvement
  > Suggestion = style, Low security, doc gaps. Does not block.

### Cross-Task Consistency
Interfaces match across tasks? Naming consistent? Conflicting assumptions?

### Security & Compliance
- [ ] Encryption at rest verified (KMS key present)
- [ ] Encryption in transit verified (`aws:SecureTransport` / TLS)
- [ ] Access logging enabled
- [ ] Data classification tags present
- [ ] Scan findings triaged (bandit / semgrep / safety / checkov) — no unaddressed Critical/High

### Tests
- [ ] All tests passing
- [ ] Test coverage adequate

### Verdict: PASS | FAIL
Reason: <one-line if FAIL>

---

> **Cycle focus:** Cycle 1 = full review, wide net. Cycle 2 = verify fixes + regressions, flag only new Critical/Warning. Cycle 3 = final verification; if issues persist, summarize for user escalation. Max 3 cycles per group.
