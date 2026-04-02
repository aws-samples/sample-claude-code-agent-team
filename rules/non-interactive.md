# Non-Interactive Execution

All commands MUST run non-interactively with zero user prompts. No command may block on stdin, confirmation, or interactive input.

## Rules

1. Always pass flags to suppress confirmation (`-y`, `--yes`, `--no-input`, `--force`, `DEBIAN_FRONTEND=noninteractive`)
2. Never rely on a TTY being attached
3. Disable pagers (`--no-pager`, `GIT_PAGER=cat`)
4. Provide all inputs via arguments or files — no interactive wizards or editor pop-ups
5. Fail loudly on missing input (non-zero exit) rather than prompting

## Common Patterns

| Tool | Non-Interactive |
|------|-----------------|
| apt | `apt-get install -y foo` |
| pip | `pip install --no-input` |
| npm | `npm init -y` |
| git | `git commit -m "msg"` |
| aws cli | env vars or `--cli-input-json` |
| terraform | `terraform apply -auto-approve` |
| cdk | `cdk deploy --require-approval never` |
| docker | `docker system prune -f` |
| npx | `npx --yes create-foo` |
| vite | `npx --yes create-vite@latest my-app --template react-ts` |
