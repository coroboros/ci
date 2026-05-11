<div align="center">

<img src="assets/logo.png" width="288" height="288" alt="Coroboros"/>

<!-- omit in toc -->
# coroboros/ci

**Reusable CI for Coroboros.**

GitHub Actions workflows and composite actions. Drop into any `@coroboros/*` repo via `uses: coroboros/ci/.github/workflows/<name>.yml@v1`.

[![visibility](https://img.shields.io/badge/visibility-internal-000000?style=flat-square)](https://github.com/coroboros)
[![latest](https://img.shields.io/badge/latest-v1-000000?style=flat-square)](CHANGELOG.md)
[![license](https://img.shields.io/badge/license-All%20Rights%20Reserved-000000?style=flat-square)](LICENSE.md)
[![coroboros.com](https://img.shields.io/badge/coroboros.com-000000?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiLz48cGF0aCBkPSJNMiAxMmgyME0xMiAyYTE1LjMgMTUuMyAwIDAgMSA0IDEwIDE1LjMgMTUuMyAwIDAgMS00IDEwIDE1LjMgMTUuMyAwIDAgMS00LTEwIDE1LjMgMTUuMyAwIDAgMSA0LTEweiIvPjwvc3ZnPg==)](https://coroboros.com)

</div>

- [Workflows](#workflows)
- [Consume](#consume)
- [Release flow](#release-flow)
- [License](#license)

---

## Workflows

| Workflow | Trigger | What it does |
|---|---|---|
| `npm-ci.yml` | PR / push | Matrix verify: `check-docs` → `check-npm-lint` → `check-npm-typecheck` → `build-js` → `test-npm-unit`. PR-only `pack-check` (`pnpm publish --dry-run`). |
| `npm-publish.yml` | Tag push | `build-version` (bump from tag) → `build-changelog` (Conventional Commits) → `deploy-package` → `post-deploy-commit-back` → `post-deploy-github-release`. Set `auto-version: false` for the verify-only fallback. |
| `commits-lint.yml` | PR | Conventional Commits lint over the PR commit range. |
| `secrets-scan.yml` | PR / push | gitleaks against the canonical `.gitleaks.toml`. |

Composites: `setup-pnpm-node`, `bump-version-from-tag`, `generate-changelog`, `verify-tag-version`. Inputs and secrets live at the top of each YAML.

---

## Consume

```yaml
# .github/workflows/ci.yml
name: ci
on:
  push: { branches: [main] }
  pull_request: { branches: [main] }
permissions: { contents: read }
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
jobs:
  ci:      { uses: coroboros/ci/.github/workflows/npm-ci.yml@v1 }
  commits: { uses: coroboros/ci/.github/workflows/commits-lint.yml@v1 }
  secrets: { uses: coroboros/ci/.github/workflows/secrets-scan.yml@v1 }
```

```yaml
# .github/workflows/release.yml
name: release
on:
  push:
    tags: ['[0-9]+.[0-9]+.[0-9]+', '[0-9]+.[0-9]+.[0-9]+-*']
permissions:
  contents: write   # auto-version commit-back
  id-token: write   # OIDC Trusted Publisher
concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false
jobs:
  publish:
    uses: coroboros/ci/.github/workflows/npm-publish.yml@v1
```

OIDC: configure the Trusted Publisher on npmjs.com pointing at `<your-repo>/release.yml` before the first tag push.

Worked examples: [`examples/oidc-npm-package/`](examples/oidc-npm-package), [`examples/token-npm-package/`](examples/token-npm-package).

---

## Release flow

```bash
git tag x.y.z
git push origin x.y.z
```

CI handles the rest — `package.json` bump, CHANGELOG entry, npm publish, commit-back to `main`, GitHub release. SemVer-strict, no `v` prefix.

Set `auto-version: false` in `release.yml` for the manual flow. Caller bumps `package.json` and `CHANGELOG.md` in a prior PR; CI then asserts via `verify-tag-version`.

---

## License

All Rights Reserved. See [LICENSE.md](LICENSE.md).
