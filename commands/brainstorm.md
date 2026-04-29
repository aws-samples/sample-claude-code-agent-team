# New Project Ideation

Explores a new project idea through structured questioning and produces a requirements file that feeds into the spec-driven workflow.

## Input

Project idea: $ARGUMENTS

## Process

1. **Analyze the idea** — Read and analyze the initial project idea. Identify the domain, target users, and core value proposition.

2. **Clarifying questions** — Ask up to 10 clarifying questions one at a time. Cover:
   - Target users and their primary pain points
   - Core functionality vs. nice-to-have features
   - Scale expectations (users, data volume, traffic patterns)
   - Integration requirements (APIs, third-party services, data sources)
   - Non-functional requirements (availability, latency, security, compliance)
   - Budget and timeline constraints
   - Team capabilities and technology preferences
   - Deployment environment (AWS, on-prem, hybrid)
   - Edge cases and failure scenarios
   - What "done" looks like — MVP scope vs. full vision

   Wait for the answer to each question before proceeding to the next. Adapt follow-up questions based on previous answers — don't ask questions that have already been answered.

3. **Synthesize requirements** — Think deeply about the idea to identify functional requirements, non-functional requirements, edge cases, and out-of-scope items. Organize into a structured requirements document.

4. **Review with user** — Present the requirements document. Iteratively refine until the user confirms the requirements are good to proceed with.

5. **Name the spec** — Ask the user for a short kebab-case slug (e.g., `my-app`).

6. **Save requirements** — Write the final requirements to `.claude/specs/<slug>/requirements.md` with these sections:
   - `## Project Summary` — summary of the finalized project idea
   - `## Functional Requirements` — organized by feature area with numbered items
   - `## Non-Functional Requirements` — performance, security, availability, compliance targets
   - `## Edge Cases` — edge cases to account for
   - `## Out of Scope` — explicitly excluded items and future considerations
   - `## Open Questions` — unresolved items that need answers during the spec phase
   - `## Notes` — any relevant information not covered elsewhere

7. **Offer next steps** — Offer to scaffold the full spec structure to continue into the build phase:
   - `spec.md` — design decisions, constraints, alternatives considered
   - `design.md` — architecture, repository structure, infrastructure design
   - `tasks.md` — parallelized task groups with agent assignments

   This feeds directly into the spec-driven workflow defined in the `spec-workflow` skill.
