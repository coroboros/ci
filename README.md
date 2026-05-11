<div align="center">

<img src="assets/logo.png" width="288" height="288" alt="coroboros/ci"/>

<!-- omit in toc -->
# coroboros/ci

**Coroboros-internal GitHub Actions workflows + composite actions.**

npm-package CI, OIDC + NPM_TOKEN publish, commit-message lint, gitleaks scan. Consumed by every `@coroboros/*` repo via `uses: coroboros/ci/.github/workflows/<name>.yml@v1`. Container builds, deploy targets, Node-service CI/CD, and notification routing land in later waves.

[![coroboros.com](https://img.shields.io/badge/coroboros.com-000000?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiLz48cGF0aCBkPSJNMiAxMmgyME0xMiAyYTE1LjMgMTUuMyAwIDAgMSA0IDEwIDE1LjMgMTUuMyAwIDAgMS00IDEwIDE1LjMgMTUuMyAwIDAgMS00LTEwIDE1LjMgMTUuMyAwIDAgMSA0LTEweiIvPjwvc3ZnPg==)](https://coroboros.com)

</div>

## Visibility

`coroboros/ci` is **private**, with Actions access toggled to *"Accessible from repositories owned by 'coroboros'"*. The encoded conventions — step names, stage ordering, security posture, release flow — are Coroboros-specific. This is internal infrastructure, not a generic library.

- Caller repos inside the `coroboros` org (public or private): reference the reusable workflows normally.
- Caller repos outside the org (forks of public `@coroboros/*` packages, third-party): no access. Mainline CI runs fine; PRs from forks lose CI coverage until the change moves into an internal branch.

### Fork PR handling

Three options, in order of effort:

1. **Accept**. Maintainers reproduce the PR locally or pull it into an internal branch to run CI. Suitable for ~5 external PRs per month.
2. **Inline-critical, reusable-heavy**. Duplicate `lint` and `typecheck` as inline steps in the public package's own `.github/workflows/` so fork PRs get fast feedback. Heavy checks (`pack-check`, `secrets-scan`, release) stay reusable and run only on the internal mainline.
3. **`pull_request_target` + label-gating**. Label the fork PR `safe-to-test`; a workflow triggered by the label runs CI in the base-repo context, which has access to the private reusables. Requires careful checkout — never check out the PR head blindly, or the fork can RCE the runner.

## Requirements

- Caller repo lives in the `coroboros` GitHub organization.
- Caller repo has Actions enabled.
- Per-repo `package.json` with `packageManager: "pnpm@..."` and `scripts.lint` / `typecheck` / `test` / `build` — defaults assume pnpm.
- For OIDC publish: an npm Trusted Publisher entry pointing at the caller's `release.yml`.
- For the default auto-version flow: caller grants `contents: write` and `id-token: write` on `release.yml` so CI can commit the bump back to `main` and emit provenance.

## What ships in 1.1.0

| Kind | Path | Purpose |
|---|---|---|
| Reusable workflow | `.github/workflows/npm-ci.yml` | Matrix verify with GitLab-named stages: `check-docs` → `check-npm-lint` → `check-npm-typecheck` → `build-js` → `test-npm-unit`, plus `pack-check` (`pnpm publish --dry-run`) on PRs |
| Reusable workflow | `.github/workflows/npm-publish.yml` | Tag-triggered release: bumps `package.json.version` from the tag, generates a CHANGELOG entry from Conventional Commits, publishes via OIDC (default) or `NPM_TOKEN`, then commits the bump back to `main` and opens a GitHub release |
| Reusable workflow | `.github/workflows/commits-lint.yml` | Lint commits in a PR range via `commitlint` |
| Reusable workflow | `.github/workflows/secrets-scan.yml` | Run gitleaks against the canonical `.gitleaks.toml` in this repo |
| Composite action | `.github/actions/setup-pnpm-node` | `pnpm` + `actions/setup-node` + `pnpm install --frozen-lockfile` |
| Composite action | `.github/actions/bump-version-from-tag` | Rewrites `package.json.version = github.ref_name` (GitLab `build-version` equivalent) |
| Composite action | `.github/actions/generate-changelog` | Builds a CHANGELOG entry from Conventional Commits since the previous tag |
| Composite action | `.github/actions/verify-tag-version` | Verify-only path. Fail loud if `github.ref_name` ≠ `package.json.version`. Used when `auto-version: false` |
| Shared config | `.gitleaks.toml` | Stack-specific rules (Resend, Neon, PostHog, GitHub fine-grained PATs) plus placeholder allowlist |

Later waves: container build/publish (Docker buildx + GHCR/ECR), deploy targets (Cloudflare Workers, AWS Lambda), Node-service CI/CD, notification routing (Slack, Google Chat), shared `CODE_OF_CONDUCT.md` / `CONTRIBUTING.md` / `SECURITY.md` / `SUPPORT.md` templates.

## Consume

Pin by floating major (`@v1`) — auto-tracks non-breaking updates:

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
  contents: write    # commit-back of the bump + CHANGELOG entry
  id-token: write    # OIDC Trusted Publisher
jobs:
  publish:
    uses: coroboros/ci/.github/workflows/npm-publish.yml@v1
    # Defaults: publish-via=pnpm, use-oidc=true, provenance=true,
    #           auto-version=true, default-branch=main.
```

Release flow (caller side): `git tag x.y.z && git push origin x.y.z`. CI handles the rest — bump, CHANGELOG entry, npm publish, commit-back, GitHub release.

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
| `auto-version` | boolean | `true` | CI rewrites `package.json.version` from `github.ref_name`, generates the CHANGELOG entry, commits the bump back to `default-branch`. When `false`, falls back to verify-only (`verify-tag-version`) and skips commit-back |
| `default-branch` | string | `main` | Branch the release-bump commit is pushed back to. Only used when `auto-version: true` |
| `lint-command` / `typecheck-command` / `test-command` / `build-command` | string | as in `npm-ci.yml` | |

Secrets:

| Secret | Required | Description |
|---|---|---|
| `NPM_TOKEN` | Only when `use-oidc: false` | npm publish token |

Stage map (matches the GitLab `npm-packages` reference):

```
check-docs → check-npm-lint → check-npm-typecheck → build-js
  → build-version    # auto-bump from tag, or verify-only
  → build-changelog  # only when auto-version
  → test-npm-unit
  → deploy-package   # one of: pnpm/oidc, pnpm/token, npm/oidc, npm/token
  → post-deploy-commit-back, post-deploy-github-release   # only when auto-version
```

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
| `v1` | Floating major | Auto-tracks non-breaking updates within the v1 line |

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
