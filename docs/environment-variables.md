# Environment variables

Three sources of configuration:

1. **Workflow inputs** — declared on `workflow_call.inputs:`, passed via the caller's `with:`.
2. **Workflow secrets** — declared on `workflow_call.secrets:`, passed via the caller's `secrets:`.
3. **`vars` context** — caller's repo / org / environment variables, read directly via `${{ vars.X }}` inside the called workflow / action.

## `javascript-npm-packages.yml` inputs

The workflow has **zero inputs** by design — imposed CI, no consumer-tunable knobs. Behavior auto-detects from secrets:

- Node.js version is resolved by `javascript/base` from the consumer's `.node-version` file. Required at the repo root — the job fails if missing.
- `pnpm publish` mode is selected by `NPM_PACKAGE_REGISTRY_TOKEN` presence: set ⇒ token-based publish (via `.npmrc`); unset ⇒ OIDC Trusted Publisher + `--provenance`.

## `javascript-npm-packages.yml` secrets

| name | required | description |
| :--- | :------- | :---------- |
| `NPM_CONFIG_FILE` | X | `.npmrc` content. Exposed at workflow-level env so `javascript/base` can drop it at the repo root. |
| `NPM_PACKAGE_REGISTRY` | X | npm package registry URL (used inside `NPM_CONFIG_FILE` via `${NPM_PACKAGE_REGISTRY}` expansion at runtime). |
| `NPM_PACKAGE_PROXY_REGISTRY` | | npm package proxy registry URL. Optional — leave unset if no proxy registry. |
| `NPM_PACKAGE_REGISTRY_TOKEN` | | npm package registry token. Used for install-time auth when the registry is private, and selects publish mode (presence ⇒ token-based publish; absence ⇒ OIDC + provenance). **Set per-repo only when needed** — leaving it unset at the org level keeps OIDC Trusted Publisher repos token-free. |

## `vars` context — caller's repo / org / env

| name | description | default if unset |
| :--- | :---------- | :--------------- |
| `vars.NPM_EXTRA_CONFIG` | Extra `.npmrc` lines appended after `NPM_CONFIG_FILE` by `javascript/base`. | `""` |

## `javascript/base` composite — env contract

The composite has zero inputs. It reads two env vars from the caller (workflow- or job-level `env:`):

| env | required | description |
| :-- | :------- | :---------- |
| `NPM_CONFIG_FILE` | yes — fails the job if missing | `.npmrc` content |
| `NPM_EXTRA_CONFIG` | no | extra `.npmrc` lines appended after `NPM_CONFIG_FILE` |

The bundled `javascript-npm-packages.yml` sets both at workflow level. Standalone composers mirror the env block at the job or workflow level.

## `release/generate-changelog` composite — outputs

| output | description |
| :----- | :---------- |
| `body` | CHANGELOG section body for the current tag (used as release notes). |

No inputs, no secrets. Reads `GITHUB_REF_NAME` natively. Requires the caller to check out with `fetch-depth: 0` so `git describe` can resolve the previous tag.

## `release/github-release` composite — inputs

| input | required | description |
| :---- | :------- | :---------- |
| `body` | yes | Release notes body — typically `steps.<id>.outputs.body` from `release/generate-changelog`. |

Caller job needs `permissions: contents: write`. Uses `${{ github.token }}` internally via the `GH_TOKEN` env var.

## `security.yml` inputs

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `config-path` | string | Path to the gitleaks config in the calling repo. Falls back to fetching `coroboros/ci`'s canonical ruleset over raw URL if the file is absent. | | `security/.gitleaks.toml` |
| `gitleaks-version` | string | Pinned gitleaks CLI version (without leading `v`). | | `8.30.1` |
| `gitleaks-sha256` | string | SHA-256 of `gitleaks_<version>_linux_x64.tar.gz` for end-to-end checksum verification. Empty = skip with warning. | | (pinned) |
| `scan-mode` | string | `git` walks history; `dir` scans the working tree only. | | `git` |
| `fail-on-leak` | boolean | Fail the job when leaks are found. | | `true` |
