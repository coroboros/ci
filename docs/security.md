# Security

Security baseline for the reusable workflows + composite actions. Every consumer pipeline inherits these guarantees by default.

> pnpm is the only supported package manager. Pin the version in the consumer's `package.json packageManager` field; `corepack` resolves it on every job.

## Supply chain — pnpm installs

`pnpm install --frozen-lockfile --ignore-scripts` runs on every install step (`--prod` for production-only installs, e.g. function packaging or publish-time install).

- `--frozen-lockfile` fails the install when `pnpm-lock.yaml` is missing, stale, or tampered with. This is the integrity gate that prevents an attacker from injecting a transitive dependency between lockfile resolution and install.
- `--ignore-scripts` skips lifecycle scripts (`preinstall`, `install`, `postinstall`) of every dependency. Cuts the postinstall supply-chain vector entirely.

The pnpm CLI is resolved via `corepack` from the consumer's `package.json packageManager` field — no floating pnpm version reaches the runner.

## Publish — OIDC + provenance

`pnpm publish --provenance --no-git-checks` is the default path for `javascript-npm-packages.yml`. It uses npm's OIDC Trusted Publisher flow when the consumer's npmjs.com package is configured for it — no long-lived publish token is required.

`NPM_PACKAGE_REGISTRY_TOKEN` does double duty: it authenticates `pnpm install` against the registry when the registry is private, and acts as the `NODE_AUTH_TOKEN` at publish time when `provenance: false`. Set the secret **per-repo, not at the org level** — leaving it unset across the org keeps OIDC Trusted Publisher repos token-free; only repos still on token-based publish (`provenance: false`) need the secret defined.

Set `provenance: false` on the workflow when Trusted Publisher is not yet configured for the package on npmjs.com.

## Secret isolation

Each `workflow_call` `secrets:` block declares ONLY the secrets the workflow consumes. No `secrets: inherit` anywhere — every secret is passed explicitly. Install / lint / test jobs never see registry credentials, AWS keys, or publish tokens; only the jobs that need them do.

## Secret scanning — `security.yml`

`security.yml` invokes the upstream `gitleaks` CLI directly (pinned `v8.30.1`, SHA-256 verified) — NOT `gitleaks/gitleaks-action@v2`, which requires a paid `gitleaks.io` license for GitHub organizations.

Consumers call it as a separate job:

```yaml
jobs:
  security:
    uses: coroboros/ci/.github/workflows/security.yml@v0
```

Inputs:

| input | default | description |
| :---- | :------ | :---------- |
| `config-path` | `security/.gitleaks.toml` | Path to the gitleaks config in the calling repo. Falls back to fetching `coroboros/ci`'s canonical ruleset over raw URL if the file is absent. |
| `gitleaks-version` | `8.30.1` | Pinned gitleaks CLI version. Bump in lockstep with [gitleaks releases](https://github.com/gitleaks/gitleaks/releases). |
| `gitleaks-sha256` | (pinned) | SHA-256 of `gitleaks_<version>_linux_x64.tar.gz` for end-to-end checksum verification. Empty = skip with warning. Update when bumping `gitleaks-version`. |
| `scan-mode` | `git` | `git` walks history; `dir` scans the working tree only. |
| `fail-on-leak` | `true` | Set `false` to surface findings without failing the job. |

The scan emits a SARIF report uploaded as the `gitleaks-report` artifact (30-day retention).

## Action pinning

Third-party actions across the reusable workflows + composite actions are pinned to a commit SHA (with an inline `# vX` comment for readability). Floating refs (`@master`, `@main`, `@vX`) are banned across this repo.

Self-CI binaries (`actionlint`, `gitleaks`, `yamllint`) are installed from pinned release tarballs with SHA-256 verification — no `curl | bash`.

## Canonical gitleaks config

The canonical ruleset is `security/.gitleaks.toml` at the root of `coroboros/ci`. Stack-specific rules cover Resend API keys, Neon Postgres connection strings, PostHog personal API keys, and GitHub fine-grained PATs in addition to the gitleaks default rule set.

Raw URL (used by `security.yml` as the cross-repo fallback):

```
https://raw.githubusercontent.com/coroboros/ci/main/security/.gitleaks.toml
```
