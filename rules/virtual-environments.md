# Project Dependency Isolation

All projects MUST use language-appropriate dependency isolation. Never install project dependencies globally.

## By Language

| Language | Isolation | Version Pinning | Lock File |
|----------|-----------|-----------------|-----------|
| Python | `python -m venv .venv` + `source .venv/bin/activate` | `requirements.txt` or `pyproject.toml` | `requirements.txt` |
| JS/TS | Local `node_modules/` (default) | `.nvmrc` + `corepack enable` | `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` |
| Rust | Cargo per-project (default) | `rust-toolchain.toml` | `Cargo.lock` (for binaries) |
| Go | `go mod` (default) | N/A | `go.mod` + `go.sum` |
| Java/JVM | Maven/Gradle per-project | `.sdkmanrc` + `mvnw`/`gradlew` wrappers | `pom.xml` / `build.gradle` lock |
| Ruby | `bundle config set --local path 'vendor/bundle'` | `.ruby-version` | `Gemfile.lock` |

## Rules

1. **Pin everything** — language version, package manager version, dependency versions
2. **Isolation dirs in `.gitignore`** — `.venv/`, `node_modules/`, `vendor/bundle/`, `target/`
3. **Lock files in version control** — always commit lock files
4. **CI must match local** — same isolation and pinned versions
5. **No global installs for project deps**
