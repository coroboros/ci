# Environment variables

Each variable below is passed either as a **secret** (`secrets:` block on `workflow_call`) or as an **input** (`inputs:` block).

> The JS workflows use **pnpm** (resolved via corepack). `NPM_*` variable names are kept — pnpm reads the same `.npmrc` syntax. See `examples.md` § *Package manager*.

**Naming convention**: inputs are `kebab-case`, secrets are `UPPER_SNAKE_CASE`. A variable is mandatory only when the workflow that consumes it is in use; workflows outside a scope do not require the scope's variables.

## Common — across most workflows

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `node-version` | input | Node.js version. | | `22` |
| `release-branch-pattern` | input | ERE pattern matching release branches. | | `^release[/]((0\|[1-9][0-9]*)\.(0\|[1-9][0-9]*)\.(0\|[1-9][0-9]*))$` |
| `release-source-commit-pattern` | input | ERE pattern matching the release-source merge commit message. Used to extract the version when merging `release/x.y.z` into the production branch. | | `^Merge branch 'release[/]((0\|[1-9][0-9]*)\.(0\|[1-9][0-9]*)\.(0\|[1-9][0-9]*))' into 'master'` |
| `npm-extra-config` | input | Extra `.npmrc` content appended after `NPM_CONFIG_FILE`. | | `""` |

## NPM — `javascript-npm-package`

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `provenance` | input (bool) | When `true`, pass `--provenance` to `pnpm publish` (requires npm Trusted Publisher OIDC). Set to `false` when only `NPM_TOKEN` is available. | | `true` |
| `NPM_CONFIG_FILE` | secret | `.npmrc` content, consumed by `setup-npmrc`. | X | none |
| `NPM_PACKAGE_REGISTRY` | secret | npm package registry URL. | X | none |
| `NPM_PACKAGE_PROXY_REGISTRY` | secret | npm package proxy registry URL. | X | none |
| `NPM_PACKAGE_REGISTRY_TOKEN` | secret | npm package registry token. | X | none |
| `NPM_TOKEN` | secret | npmjs.com publish token. Optional — if absent, OIDC Trusted Publisher is used. | | none |

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
