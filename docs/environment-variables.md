# Environment variables

Three sources of configuration:

1. **Workflow inputs** — declared on `workflow_call.inputs:`, passed via the caller's `with:`.
2. **Workflow secrets** — declared on `workflow_call.secrets:`, passed via the caller's `secrets:`.
3. **`vars` context** — caller's repo / org / environment variables, read directly via `${{ vars.X }}` inside the called workflow / action.

## `javascript-npm-packages.yml` inputs

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `node-version` | string | Fallback Node.js version. `setup-base` reads `.node-version` from the consumer repo if present, falls back to this input, fails the job if neither is set. | | `""` |
| `provenance` | boolean | When `true`, pass `--provenance` to `pnpm publish` (requires npm Trusted Publisher OIDC). Set to `false` to fall back to publishing with `NPM_PACKAGE_REGISTRY_TOKEN` as `NODE_AUTH_TOKEN`. | | `true` |

## `javascript-npm-packages.yml` secrets

| name | required | description |
| :--- | :------- | :---------- |
| `NPM_CONFIG_FILE` | X | `.npmrc` content, dropped at repo root by `setup-base`. |
| `NPM_PACKAGE_REGISTRY` | X | npm package registry URL (used inside `NPM_CONFIG_FILE` via `${NPM_PACKAGE_REGISTRY}` expansion at runtime). |
| `NPM_PACKAGE_PROXY_REGISTRY` | X | npm package proxy registry URL. |
| `NPM_PACKAGE_REGISTRY_TOKEN` | | npm package registry token. Used for install-time auth when the registry is private, and as `NODE_AUTH_TOKEN` at publish time when `provenance: false`. **Set per-repo only when needed** — leaving it unset at the org level keeps OIDC Trusted Publisher repos token-free. |
| `SLACK_WEBHOOK_URL` | | Slack webhook. Notification step in the `publish` job is skipped when empty. |
| `GOOGLE_CHAT_WEBHOOK_URL` | | Google Chat webhook. Notification step in the `publish` job is skipped when empty. |

## `vars` context — caller's repo / org / env

| name | description | default if unset |
| :--- | :---------- | :--------------- |
| `vars.NPM_EXTRA_CONFIG` | Extra `.npmrc` lines appended after `NPM_CONFIG_FILE` by `setup-base`. | `""` |

## `security.yml` inputs

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `config-path` | string | Path to the gitleaks config in the calling repo. Falls back to fetching `coroboros/ci`'s canonical ruleset over raw URL if the file is absent. | | `security/.gitleaks.toml` |
| `gitleaks-version` | string | Pinned gitleaks CLI version (without leading `v`). | | `8.30.1` |
| `gitleaks-sha256` | string | SHA-256 of `gitleaks_<version>_linux_x64.tar.gz` for end-to-end checksum verification. Empty = skip with warning. | | (pinned) |
| `scan-mode` | string | `git` walks history; `dir` scans the working tree only. | | `git` |
| `fail-on-leak` | boolean | Fail the job when leaks are found. | | `true` |
