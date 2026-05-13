# Security

Security baseline for `javascript-npm-packages.yml`.

> pnpm is the only supported package manager. Pin the version in the consumer's `package.json` `packageManager` field; corepack resolves it on every job.

## Supply chain — pnpm installs

`pnpm install --frozen-lockfile --ignore-scripts` runs inside `setup-base` (called by `preflight` and `publish`).

- `--frozen-lockfile` fails the install when `pnpm-lock.yaml` is missing, stale, or tampered with. Integrity gate against transitive-dependency injection between lockfile resolution and install.
- `--ignore-scripts` skips lifecycle scripts (`preinstall`, `install`, `postinstall`) of every dependency. Cuts the postinstall supply-chain vector.

The pnpm CLI is resolved via corepack from the consumer's `package.json packageManager` field — no floating pnpm version reaches the runner.

## Publish — OIDC + provenance

`pnpm publish --provenance --no-git-checks` is the default path. It uses npm's OIDC Trusted Publisher flow when the consumer's npmjs.com package is configured for it — no long-lived publish token is required.

`NPM_PACKAGE_REGISTRY_TOKEN` does double duty: install-time registry auth when the registry is private, and `NODE_AUTH_TOKEN` at publish time when `provenance: false`. Set the secret **per-repo, not at the org level** — leaving it unset across the org keeps OIDC Trusted Publisher repos token-free; only repos still on token-based publish (`provenance: false`) need the secret.

## Secret isolation

Each `workflow_call.secrets:` block declares ONLY the secrets the workflow consumes. No `secrets: inherit` anywhere — every secret is passed explicitly.

## Secret scanning — `security.yml`

`security.yml` invokes the upstream `gitleaks` CLI directly (pinned `v8.30.1`, SHA-256 verified) — NOT `gitleaks/gitleaks-action@v2`, which requires a paid `gitleaks.io` license for GitHub organizations.

The `security` job in `javascript-npm-packages.yml` calls it automatically on every trigger — consumers get gitleaks for free. Also callable standalone for non-npm repos:

```yaml
jobs:
  scan:
    uses: coroboros/ci/.github/workflows/security.yml@v0
```

Inputs are documented in `docs/environment-variables.md`. The scan emits a SARIF report as the `gitleaks-report` artifact (30-day retention).

## Action pinning

Third-party actions across the reusable workflows + composite actions are pinned to a commit SHA (with an inline `# vX` comment for readability). Floating refs (`@master`, `@main`, `@vX`) are banned across this repo.

Self-CI binaries (`actionlint`, `gitleaks`, `yamllint`) are installed from pinned release tarballs with SHA-256 verification — no `curl | bash`.

## Canonical gitleaks config

The canonical ruleset is `security/.gitleaks.toml` at the root of `coroboros/ci`. Stack-specific rules cover Resend API keys, Neon Postgres connection strings, PostHog personal API keys, and GitHub fine-grained PATs in addition to the gitleaks default rule set.

Raw URL (used by `security.yml` as the cross-repo fallback):

```
https://raw.githubusercontent.com/coroboros/ci/main/security/.gitleaks.toml
```
