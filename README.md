# coroboros/ci

Reusable GitHub Actions workflows and composite actions for `@coroboros/*` npm packages.

[![ci](https://github.com/coroboros/ci/actions/workflows/ci.yml/badge.svg)](https://github.com/coroboros/ci/actions/workflows/ci.yml)
[![license](https://img.shields.io/badge/license-MIT-000000?style=flat-square)](LICENSE.md)

## What ships

| Kind | Path | Purpose |
|---|---|---|
| Reusable workflow | `.github/workflows/npm-ci.yml` | Matrix verify (lint + typecheck + test + build) with optional `pnpm publish --dry-run` on PRs |
| Reusable workflow | `.github/workflows/npm-publish.yml` | npm publish with `publish-via` (pnpm/npm) and `use-oidc` (true/false) parameters |
| Reusable workflow | `.github/workflows/commits-lint.yml` | Lint commits in a PR range via `commitlint` |
| Reusable workflow | `.github/workflows/secrets-scan.yml` | Run gitleaks against the canonical `.gitleaks.toml` in this repo |
| Composite action | `.github/actions/setup-pnpm-node` | `pnpm` + `actions/setup-node` + `pnpm install --frozen-lockfile` |
| Composite action | `.github/actions/verify-tag-version` | Fail loud if `GITHUB_REF_NAME` ≠ `package.json.version` |
| Shared config | `.gitleaks.toml` | Stack-specific rules (Resend, Neon, PostHog, GitHub PAT) plus placeholder allowlist |

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

Full working examples in [`examples/oidc-npm-package/`](examples/oidc-npm-package) and [`examples/token-npm-package/`](examples/token-npm-package).

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

## OIDC Trusted Publisher setup (prerequisite for `use-oidc: true`)

Before the first release, configure the package on npmjs.com:

1. https://www.npmjs.com → package → Settings → Trusted Publishers → Add.
2. Repository: `<your-org>/<repo>`.
3. Workflow filename: **caller's** filename (e.g., `release.yml`), not `npm-publish.yml`.
4. Environment: leave empty unless your caller uses one.

The reusable workflow already sets `permissions: { id-token: write }`; the caller must also set it (workflows inherit but the entry point is the caller).

## Versioning

| Tag | Stability | Use when |
|---|---|---|
| `1.2.3` | Immutable | You need exact reproducibility |
| `v1` | Floating major | Default for sibling Coroboros repos — auto-tracks non-breaking updates within the v1 line |

A breaking change cuts a new floating major (`v2`); the `v1` alias stops moving.

## Security posture

- First-party actions (`actions/*`, `pnpm/*`) pinned by floating major (`@v4`) — within the GitHub trust boundary.
- Third-party actions pinned by 40-char SHA with version comment, Dependabot-managed.
- gitleaks CLI installed manually (MIT) — the `gitleaks-action@v2` requires a paid license for org repos.
- OIDC Trusted Publisher is the default publish path; `NPM_TOKEN` fallback is explicit and parameterized.

## Contributing

- Branch `main`. Conventional Commits enforced on PRs.
- Run `bash <(curl -fsSL https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash) && ./actionlint -color` before pushing workflow changes.
- New reusable workflows land with at least one example in `examples/` and an entry in this README.

## License

[MIT](LICENSE.md)
