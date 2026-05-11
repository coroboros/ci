<div align="center">

<img src="assets/logo.png" width="288" height="288" alt="coroboros/ci"/>

<!-- omit in toc -->
# coroboros/ci

**Reusable GitHub Actions for the Coroboros stack.**

Workflows and composite actions consumed by sibling Coroboros repos. The first wave covers `@coroboros/*` npm packages: matrix verify, OIDC publish with NPM_TOKEN fallback, commit-message lint, gitleaks scan against a canonical ruleset. Container builds, deploy targets, Node-service CI/CD, and notification routing land in later waves.

[![release](https://img.shields.io/github/v/release/coroboros/ci?style=flat-square&color=000000)](https://github.com/coroboros/ci/releases)
[![ci](https://img.shields.io/github/actions/workflow/status/coroboros/ci/ci.yml?branch=main&style=flat-square&label=ci&color=000000)](https://github.com/coroboros/ci/actions/workflows/ci.yml)
[![license](https://img.shields.io/badge/license-MIT-000000?style=flat-square)](https://opensource.org/licenses/MIT)
[![stars](https://img.shields.io/github/stars/coroboros/ci?style=flat-square&label=stars&color=000000)](https://github.com/coroboros/ci)
[![coroboros.com](https://img.shields.io/badge/coroboros.com-000000?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiLz48cGF0aCBkPSJNMiAxMmgyME0xMiAyYTE1LjMgMTUuMyAwIDAgMSA0IDEwIDE1LjMgMTUuMyAwIDAgMS00IDEwIDE1LjMgMTUuMyAwIDAgMS00LTEwIDE1LjMgMTUuMyAwIDAgMSA0LTEweiIvPjwvc3ZnPg==)](https://coroboros.com)

</div>

## Requirements

- A GitHub repository with Actions enabled.
- Per-repo `package.json` with `packageManager: "pnpm@..."` (or pass `pnpm-version` upstream) — for workflows that touch pnpm.
- For OIDC publish: a npm Trusted Publisher entry pointing at the caller's `release.yml`.

## What ships in 1.0.0

| Kind | Path | Purpose |
|---|---|---|
| Reusable workflow | `.github/workflows/npm-ci.yml` | Matrix verify (lint + typecheck + test + build) with optional `pnpm publish --dry-run` on PRs |
| Reusable workflow | `.github/workflows/npm-publish.yml` | npm publish with `publish-via` (`pnpm`/`npm`) and `use-oidc` (`true`/`false`) parameters |
| Reusable workflow | `.github/workflows/commits-lint.yml` | Lint commits in a PR range via `commitlint` |
| Reusable workflow | `.github/workflows/secrets-scan.yml` | Run gitleaks against the canonical `.gitleaks.toml` in this repo |
| Composite action | `.github/actions/setup-pnpm-node` | `pnpm` + `actions/setup-node` + `pnpm install --frozen-lockfile` |
| Composite action | `.github/actions/verify-tag-version` | Fail loud if `GITHUB_REF_NAME` ≠ `package.json.version` |
| Shared config | `.gitleaks.toml` | Stack-specific rules (Resend, Neon, PostHog, GitHub fine-grained PATs) plus placeholder allowlist |

Later waves: container build/publish (Docker buildx + GHCR/ECR), deploy targets (Cloudflare Workers, AWS Lambda), Node-service CI/CD, notification routing (Slack, Google Chat), shared `CODE_OF_CONDUCT.md` / `CONTRIBUTING.md` / `SECURITY.md` / `SUPPORT.md` templates.

## Consume

Pin by floating major (`@v1`) for sibling Coroboros repos:

```yaml
# .github/workflows/ci.yml
name: ci
on:
  push: { branches: [main] }
  pull_request: { branches: [main] }
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
jobs:
  ci:
    uses: coroboros/ci/.github/workflows/npm-ci.yml@v1
  commits:
    uses: coroboros/ci/.github/workflows/commits-lint.yml@v1
  secrets:
    uses: coroboros/ci/.github/workflows/secrets-scan.yml@v1
```

```yaml
# .github/workflows/release.yml
name: release
on:
  push:
    tags: ['[0-9]+.[0-9]+.[0-9]+', '[0-9]+.[0-9]+.[0-9]+-*']
concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false
permissions:
  contents: read
  id-token: write
jobs:
  publish:
    uses: coroboros/ci/.github/workflows/npm-publish.yml@v1
    # Defaults: publish-via=pnpm, use-oidc=true, provenance=true
```

Working examples live in [`examples/oidc-npm-package/`](examples/oidc-npm-package) and [`examples/token-npm-package/`](examples/token-npm-package).

## Reusable workflow API

### `npm-ci.yml`

| Input | Type | Default | Description |
|---|---|---|---|
| `node-versions` | string (JSON array) | `'["22", "current"]'` | Matrix values |
| `working-directory` | string | `.` | Package root |
| `lint-command` | string | `pnpm lint` | Shell command |
| `typecheck-command` | string | `pnpm typecheck` | |
| `test-command` | string | `pnpm test` | |
| `build-command` | string | `pnpm build` | |
| `package-dry-run` | boolean | `true` | Run `pnpm publish --dry-run` on PRs |

### `npm-publish.yml`

| Input | Type | Default | Description |
|---|---|---|---|
| `node-version` | string | `'22'` | |
| `working-directory` | string | `.` | |
| `registry-url` | string | `https://registry.npmjs.org` | |
| `publish-via` | string | `pnpm` | `pnpm` or `npm` |
| `use-oidc` | boolean | `true` | When `false`, expects `NPM_TOKEN` secret |
| `access` | string | `public` | `public` or `restricted` |
| `provenance` | boolean | `true` | Emit provenance attestation |
| `lint-command` / `typecheck-command` / `test-command` / `build-command` | string | as in `npm-ci.yml` | |

Secrets:

| Secret | Required | Description |
|---|---|---|
| `NPM_TOKEN` | Only when `use-oidc: false` | npm publish token |

### `commits-lint.yml`

| Input | Type | Default |
|---|---|---|
| `config-path` | string | `commitlint.config.js` |
| `working-directory` | string | `.` |

### `secrets-scan.yml`

| Input | Type | Default |
|---|---|---|
| `config-ref` | string | `v1` |
| `gitleaks-version` | string | `8.21.0` |

## OIDC Trusted Publisher setup

Required when `use-oidc: true` (default). Configure the package on npmjs.com before the first release:

1. https://www.npmjs.com → package → Settings → Trusted Publishers → Add.
2. Repository: `<your-org>/<repo>`.
3. Workflow filename: the **caller's** filename (e.g., `release.yml`), not `npm-publish.yml`.
4. Environment: empty unless the caller declares one.

The reusable workflow sets `permissions: { id-token: write }`. The caller must set it too — workflow permissions do not propagate up the chain.

## Versioning

| Tag | Stability | Use when |
|---|---|---|
| `1.2.3` | Immutable | Reproducibility matters |
| `v1` | Floating major | Sibling Coroboros repos — auto-tracks non-breaking updates within the v1 line |

A breaking change cuts a new floating major (`v2`); the `v1` alias stops moving.

## Security posture

- First-party actions (`actions/*`, `pnpm/*`) pinned by floating major (`@v4`) — inside the GitHub trust boundary.
- Third-party actions pinned by 40-char SHA with a version comment, Dependabot-managed.
- gitleaks CLI installed manually (MIT). The `gitleaks-action@v2` requires a paid license for org repos.
- OIDC Trusted Publisher is the default publish path; `NPM_TOKEN` fallback is explicit and parameterized.

## Contributing

- Branch `main`. Conventional Commits enforced on PRs.
- Run `actionlint` locally before pushing workflow changes (install: `brew install actionlint`).
- New reusable workflows land with at least one example in `examples/` and an entry in this README.

## License

[MIT](LICENSE.md)
