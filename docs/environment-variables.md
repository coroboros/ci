# Environment variables

Each variable below is passed either as a **secret** (`secrets:` block on `workflow_call`) or as an **input** (`inputs:` block).

> The JS workflows use **pnpm** (resolved via corepack). `NPM_*` variable names are kept — pnpm reads the same `.npmrc` syntax. See `examples.md` § *Package manager*.

**Naming convention**: inputs are `kebab-case`, secrets are `UPPER_SNAKE_CASE`. A variable is mandatory only when the workflow that consumes it is in use; workflows outside a scope do not require the scope's variables.

## Common — across most workflows

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `node-version` | input | Node.js fallback version. The workflow's `base` job calls `setup-base`, which reads `.node-version` from the consumer repo if present, falls back to this input, and fails the job if neither is set. | | `""` |

## NPM — `javascript-npm-package`

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `provenance` | input (bool) | When `true`, pass `--provenance` to `pnpm publish` (requires npm Trusted Publisher OIDC). Set to `false` to fall back to publishing with `NPM_PACKAGE_REGISTRY_TOKEN` as `NODE_AUTH_TOKEN`. | | `true` |
| `NPM_CONFIG_FILE` | secret | `.npmrc` content, consumed by `setup-npmrc`. | X | none |
| `NPM_PACKAGE_REGISTRY` | secret | npm package registry URL. | X | none |
| `NPM_PACKAGE_PROXY_REGISTRY` | secret | npm package proxy registry URL. | X | none |
| `NPM_PACKAGE_REGISTRY_TOKEN` | secret | npm package registry token. Used for install-time auth when the registry is private, and as `NODE_AUTH_TOKEN` at publish time when `provenance: false`. **Set per-repo only when needed** — leaving it unset at the org level keeps OIDC Trusted Publisher repos token-free. | | none |

## Notifications — `notify` (called from `javascript-npm-package`)

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `SLACK_WEBHOOK_URL` | secret | Slack webhook URL. Notification is skipped when empty. | | none |
| `GOOGLE_CHAT_WEBHOOK_URL` | secret | Google Chat webhook URL. Notification is skipped when empty. | | none |

## Security — `security.yml`

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `config-path` | input | Path to the gitleaks config in the calling repo. Falls back to fetching `coroboros/ci`'s canonical ruleset over raw URL if the file is absent. | | `security/.gitleaks.toml` |
| `gitleaks-version` | input | Pinned gitleaks CLI version (without leading `v`). | | `8.30.1` |
| `gitleaks-sha256` | input | SHA-256 of `gitleaks_<version>_linux_x64.tar.gz` for end-to-end checksum verification. Empty = skip with warning. Update when bumping `gitleaks-version`. | | (pinned) |
| `scan-mode` | input | `git` walks history; `dir` scans the working tree only. | | `git` |
| `fail-on-leak` | input (bool) | Fail the job when leaks are found. | | `true` |
