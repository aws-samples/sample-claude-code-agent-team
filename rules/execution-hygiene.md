# Execution Hygiene

Always-on rules covering how commands are executed and how project dependencies are isolated. Apply universally — every session, every task, every agent. This file is auto-loaded as a global rule.

## Non-Interactive Execution

All commands MUST run non-interactively with zero user prompts. No command may block on stdin, confirmation, editor pop-up, or pager.

### Rules

1. Always pass flags that suppress confirmation: `-y`, `--yes`, `--no-input`, `--force`, `DEBIAN_FRONTEND=noninteractive`
2. Never rely on a TTY being attached
3. Disable pagers: `--no-pager`, `--no-cli-pager`, `GIT_PAGER=cat`
4. Provide all inputs via arguments, env vars, or files — no interactive wizards or editor pop-ups
5. Fail loudly on missing input (non-zero exit) rather than prompting
6. Shell scripts: start with `set -euo pipefail`; never call `read -p` or any blocking stdin read; default any "confirm?" variable to yes

### Common Patterns

| Tool | Non-Interactive Form |
|------|----------------------|
| apt | `apt-get install -y foo` (with `DEBIAN_FRONTEND=noninteractive` for installs) |
| pip | `pip install --no-input` |
| npm | `npm init -y`, `npm install` (non-interactive by default) |
| npx | `npx --yes create-foo` |
| vite scaffold | `npx --yes create-vite@latest my-app --template react-ts` |
| git | `git --no-pager <cmd>`, `GIT_PAGER=cat git <cmd>`, `git commit -m "..."`, `git merge --no-edit`, `git rebase --no-edit` |
| aws cli | `aws ... --no-cli-pager`, `--output json|table|text|yaml`, env vars or `--cli-input-json` for inputs |
| terraform | `terraform apply -auto-approve`, `terraform init -input=false` |
| cdk | `cdk deploy --require-approval never` |
| sam | `sam init --no-interactive`, `sam build`, `sam deploy --no-confirm-changeset --no-fail-on-empty-changeset` |
| amplify | `npx ampx sandbox --once` (non-interactive sandbox deploy) |
| docker | `docker system prune -f` |
| kubectl | `kubectl delete --wait=false` (when blocking is undesirable); never use `--edit` |
| gh / glab | `--yes` on confirm-prompts; pipe body via `--body-file` or `--body` rather than editor |
| ssh | `-o BatchMode=yes -o StrictHostKeyChecking=accept-new` for automation |

### Pager Discipline

Pagers break agent output. Always disable:

```bash
git --no-pager log -10
GIT_PAGER=cat git show HEAD
aws ec2 describe-instances --no-cli-pager
kubectl get pods            # kubectl is non-pager by default; if a wrapper changes that, force `| cat`
```

## Dependency Isolation

All projects MUST use language-appropriate dependency isolation. Never install project dependencies globally.

### By Language

| Language | Isolation | Version Pinning | Lock File |
|----------|-----------|-----------------|-----------|
| Python | `python -m venv .venv` + `source .venv/bin/activate` (or `uv venv`) | `pyproject.toml` or `requirements.txt` | `requirements.txt` / `uv.lock` / `poetry.lock` |
| JS/TS | Local `node_modules/` (default) | `.nvmrc` + `corepack enable` | `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` |
| Rust | Cargo per-project (default) | `rust-toolchain.toml` | `Cargo.lock` (binaries) |
| Go | `go mod` (default) | go directive in `go.mod` | `go.mod` + `go.sum` |
| Java/JVM | Maven/Gradle per-project | `.sdkmanrc` + `mvnw` / `gradlew` wrappers | `pom.xml` / `build.gradle` lock |
| Ruby | `bundle config set --local path 'vendor/bundle'` | `.ruby-version` | `Gemfile.lock` |

### Rules

1. **Pin everything** — language version, package manager version, dependency versions
2. **Isolation dirs in `.gitignore`** — `.venv/`, `node_modules/`, `vendor/bundle/`, `target/`
3. **Lock files in version control** — always commit lock files
4. **CI matches local** — same isolation strategy, same pinned versions
5. **No global installs for project deps** — global tooling (e.g., `pipx`-installed CLIs) is a separate concern from project deps and should still be pinned where possible

## Why Always-On

These rules can't be silently skipped by an agent that forgot to load a skill. They apply equally to:

- Direct user sessions (no team context)
- Team-coordinated builds (every teammate inherits this)
- Background tasks, hooks, and CI

If something legitimately needs interactive input (e.g., `gcloud auth login`), have the user run it themselves — don't try to drive an interactive flow.
