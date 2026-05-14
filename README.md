<div align="center">

<img src="assets/logo.png" width="288" height="288" alt="Coroboros"/>

<!-- omit in toc -->
# coroboros/ci

**Reusable GitHub Actions CI for the Coroboros stack.**

Drop into any `@coroboros/*` repo via `uses: coroboros/ci/.github/workflows/<name>.yml@v0`, or compose around the composite actions under `.github/actions/`.

[![latest](https://img.shields.io/github/v/release/coroboros/ci?style=flat-square&label=latest&color=000000)](https://github.com/coroboros/ci/releases)
[![ci](https://img.shields.io/github/actions/workflow/status/coroboros/ci/self.yml?branch=main&style=flat-square&label=ci&color=000000)](https://github.com/coroboros/ci/actions/workflows/self.yml)
[![branch](https://img.shields.io/badge/branch-main-000000?style=flat-square)](https://github.com/coroboros/ci)
[![license](https://img.shields.io/badge/license-All%20Rights%20Reserved-000000?style=flat-square)](LICENSE.md)
[![stars](https://img.shields.io/github/stars/coroboros/ci?style=flat-square&label=stars&color=000000)](https://github.com/coroboros/ci)
[![skills](https://img.shields.io/badge/skills-000000?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDE2IDE2IiBmaWxsPSJ3aGl0ZSI+PHBvbHlnb24gcG9pbnRzPSI4LDAgMTAsNiAxNiw4IDEwLDEwIDgsMTYgNiwxMCAwLDggNiw2Ii8+PC9zdmc+)](https://github.com/coroboros/agent-skills)
[![coroboros.com](https://img.shields.io/badge/coroboros.com-000000?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiLz48cGF0aCBkPSJNMiAxMmgyME0xMiAyYTE1LjMgMTUuMyAwIDAgMSA0IDEwIDE1LjMgMTUuMyAwIDAgMS00IDEwIDE1LjMgMTUuMyAwIDAgMS00LTEwIDE1LjMgMTUuMyAwIDAgMSA0LTEweiIvPjwvc3ZnPg==)](https://coroboros.com)

</div>

- [Pipelines](#pipelines)
- [Composable actions](#composable-actions)
- [Quick start](#quick-start)
- [Development flow](#development-flow)
- [Environment](#environment)
- [Security](#security)
- [Examples](#examples)
- [License](#license)

---

## Pipelines

### `javascript-npm-packages.yml`

Bundled NPM CI. Three jobs gated by trigger event:

```
preflight  (branch push)  → check-docs → javascript/base
publish    (tag push)     → check-docs → javascript/base → pin → publish → release → commit-back
security   (every call)   → gitleaks ∥ osv-scanner ∥ dependency-review (PR only)
```

Each job runs all its steps in a single runner. `security` calls `security.yml`; no other `needs:` chain. Publish mode auto-detects: OIDC + `--provenance` when `NPM_PACKAGE_REGISTRY_TOKEN` is unset, token-based via `.npmrc` when set.

<details>
<summary><em>preflight</em></summary>

<br>

1. `actions/checkout`
2. `check-docs`
3. `javascript/base` — install + lint + build (when `scripts.build` exists) + test

</details>

<details>
<summary><em>publish</em></summary>

<br>

1. `actions/checkout` (`ref: main`, `fetch-depth: 0`)
2. Verify `main` HEAD matches the tag SHA. Fails if `main` drifted since the tag was pushed
3. `check-docs` + `javascript/base`
4. `pnpm version --allow-same-version --no-git-tag-version "${GITHUB_REF_NAME}"` — pin `package.json` to the tag
5. `release/generate-changelog` — outputs `body`
6. `pnpm publish` — `--provenance --no-git-checks` (OIDC) when `NPM_PACKAGE_REGISTRY_TOKEN` is unset, else `--no-git-checks` (token via `.npmrc`)
7. `release/github-release` — body from step 5
8. Commit `CHANGELOG.md` + `package.json` + `pnpm-lock.yaml` back to `main` as `chore: release ${tag}`
9. Move rolling major tag `vN` to the release commit (skipped on pre-release tags)

</details>

<details>
<summary><em>security</em></summary>

<br>

Three parallel jobs:

- **`gitleaks`** — upstream CLI pinned `v8.30.1`, SHA-256 verified. Reads `security/.gitleaks.toml` (fails fast if missing). SARIF emitted as the `gitleaks-report` artifact (30-day retention).
- **`dependency-review`** — runs on `pull_request` only. Fails on high-severity CVE introduced by the dep diff. `actions/dependency-review-action@v4`.
- **`osv-scanner`** — recursive lockfile scan against [OSV.dev](https://osv.dev/) (aggregates GHSA, RustSec, PyPA, Go vulndb, etc.). `google/osv-scanner-action@v2`. Fails on any known vulnerability.

</details>

### `security.yml`

Reusable sub-workflow exposing the three security jobs above. Used internally by `javascript-npm-packages.yml`, callable standalone for non-npm consumers — see [Examples](#examples).

---

## Composable actions

| Action | Type | Purpose |
| :--- | :--- | :--- |
| `check-docs` | transverse | Context dump + `README.md` presence check. |
| `javascript/base` | JS | `.node-version` resolution + Node setup + corepack + pnpm store cache + `.npmrc` generation + `pnpm install --frozen-lockfile --ignore-scripts` + `pnpm run lint` + `pnpm run build` (conditional) + `pnpm test`. |
| `release/generate-changelog` | transverse | Tag format guard (fails on `v` prefix) + generates or reuses the `## vX.Y.Z` section in `CHANGELOG.md` from Conventional Commits. Outputs `body`. Idempotent. Caller needs `fetch-depth: 0`. |
| `release/github-release` | transverse | Creates the GitHub Release for the current tag with the provided notes body. Caller needs `permissions: contents: write`. |

---

## Quick start

```yaml
# consumer-repo/.github/workflows/ci.yml
name: CI
on:
  push:
    branches: [develop, main]
    tags: ['*']
  pull_request:
  workflow_dispatch:

jobs:
  ci:
    uses: coroboros/ci/.github/workflows/javascript-npm-packages.yml@v0
    permissions:
      contents: write   # GitHub Release on tag
      id-token: write   # npm OIDC publish on tag
    secrets:
      NPM_CONFIG_FILE: ${{ secrets.NPM_CONFIG_FILE }}
      NPM_PACKAGE_REGISTRY: ${{ secrets.NPM_PACKAGE_REGISTRY }}
      NPM_PACKAGE_PROXY_REGISTRY: ${{ secrets.NPM_PACKAGE_PROXY_REGISTRY }}
      NPM_PACKAGE_REGISTRY_TOKEN: ${{ secrets.NPM_PACKAGE_REGISTRY_TOKEN }}
```

Consumer must provide at repo root:
- `.node-version` — Node version (fail-fast if missing).
- `package.json` with `packageManager: "pnpm@X.Y.Z"`, `scripts.lint`, `scripts.test`. `scripts.build` is optional (auto-detected).
- `pnpm-lock.yaml` — required for `--frozen-lockfile`.
- `security/.gitleaks.toml` — gitleaks ruleset (copy from this repo, see [Security](#security)).

---

## Development flow

Develop with Conventional Commits → tag → push. No manual CHANGELOG, no version bump.

Tags follow **SemVer strict** — `1.2.3`, never `v1.2.3`. The `publish` job auto-generates the CHANGELOG entry with the `v` prefix in the section header.

<details>
<summary><em>Branch models</em></summary>

<br>

**main-only** — feature branch → PR → squash-merge to `main` → tag the merge commit → push.

**develop + main** — PR into `develop` → tag pre-release → `release/x.y.z` branch → merge to `main` → tag final on `main`.

Nobody pushes directly to protected branches (`main`, `develop`, `production`, `staging`).

</details>

<details>
<summary><em>Conventional Commits → CHANGELOG</em></summary>

<br>

| Commit type | CHANGELOG subsection |
| :--- | :--- |
| `feat` | Features |
| `fix` | Fixes |
| `refactor` | Refactor |
| `perf` | Performance |
| `docs` | Documentation |
| `chore` / `ci` / `build` | Configuration |
| `test` | Tests |
| `style` | Style |
| Other / non-standard | Others |
| `!:` or `BREAKING CHANGE:` | Breaking Changes (always first) |

Section format: `## vX.Y.Z - DD/MM/YYYY`. Idempotent. Reuses an existing hand-curated section for the tag if present.

</details>

---

## Environment

Zero inputs on `javascript-npm-packages.yml` and on every composite — imposed, not proposed. Configuration flows through `secrets:` and the caller's `vars` context.

<details>
<summary><em>Secrets (caller's <code>secrets:</code> block)</em></summary>

<br>

| name | required | description |
| :--- | :---: | :--- |
| `NPM_CONFIG_FILE` | ✔ | `.npmrc` content. Written to repo root by `javascript/base`. `${VAR}` references inside are expanded by npm at install time. |
| `NPM_PACKAGE_REGISTRY` | ✔ | npm package registry URL. |
| `NPM_PACKAGE_PROXY_REGISTRY` |  | Optional npm proxy registry URL. |
| `NPM_PACKAGE_REGISTRY_TOKEN` |  | Set per-repo only for token-based publish (private registry). Absence triggers OIDC + provenance. Leaving it unset at the org level keeps OIDC repos token-free. |

</details>

<details>
<summary><em><code>vars</code> context</em></summary>

<br>

| name | description | default |
| :--- | :--- | :--- |
| `NPM_EXTRA_CONFIG` | Extra `.npmrc` lines appended after `NPM_CONFIG_FILE`. | `""` |

</details>

<details>
<summary><em><code>javascript/base</code> env contract (standalone composition)</em></summary>

<br>

| env | required | description |
| :-- | :---: | :--- |
| `NPM_CONFIG_FILE` | ✔ — fail if missing | `.npmrc` content |
| `NPM_EXTRA_CONFIG` |  | Appended after `NPM_CONFIG_FILE` |

Set both at the caller's workflow- or job-level `env:`.

</details>

<details>
<summary><em><code>release/*</code> composites I/O</em></summary>

<br>

**`release/generate-changelog`** — no inputs, no secrets. Reads `GITHUB_REF_NAME`. Requires `fetch-depth: 0` for `git describe`. Output:

| output | description |
| :--- | :--- |
| `body` | CHANGELOG section body — use as release notes. |

**`release/github-release`** — input:

| input | required | description |
| :--- | :---: | :--- |
| `body` | ✔ | Release notes body, typically `steps.<id>.outputs.body` from `release/generate-changelog`. |

Caller job needs `permissions: contents: write`. Uses `${{ github.token }}` internally via `GH_TOKEN`.

</details>

---

## Security

<details>
<summary><em>Supply chain — pnpm install flags</em></summary>

<br>

`pnpm install --frozen-lockfile --ignore-scripts` runs inside `javascript/base`.

- `--frozen-lockfile` — fails on stale or tampered `pnpm-lock.yaml`. Gate against transitive-dependency injection.
- `--ignore-scripts` — skips lifecycle scripts (`preinstall`, `install`, `postinstall`) of every dependency. Cuts the postinstall supply-chain vector.

pnpm CLI resolved via corepack from `packageManager`. No floating version reaches the runner.

</details>

<details>
<summary><em>Publish — OIDC vs token auth</em></summary>

<br>

Auto-detected by `NPM_PACKAGE_REGISTRY_TOKEN` presence:

- **Absent** → `pnpm publish --provenance --no-git-checks` (OIDC Trusted Publisher + provenance attestation, no long-lived token).
- **Present** → `pnpm publish --no-git-checks` (token-based via the `.npmrc` generated by `javascript/base`).

</details>

<details>
<summary><em>Secret isolation</em></summary>

<br>

Each `workflow_call.secrets:` block declares ONLY the secrets the job consumes. No `secrets: inherit` anywhere. Every secret is passed explicitly.

</details>

<details>
<summary><em>Action pinning + Dependabot</em></summary>

<br>

Third-party actions across workflows + composites are pinned to a commit SHA with an inline `# vX` comment. Floating refs (`@master`, `@main`, `@vX`) are banned.

Self-CI binaries pinned by version. `actionlint` and `gitleaks` install from release tarballs with SHA-256 verification; `yamllint` via `pip install` with version pin. No `curl | bash`.

`.github/dependabot.yml` opens weekly grouped auto-PRs to bump pinned SHAs across `.github/workflows/*` and `.github/actions/**/action.yml`. Consumers should add their own ecosystem entries (e.g., `npm`).

</details>

<details>
<summary><em>Canonical gitleaks config</em></summary>

<br>

Canonical ruleset at `security/.gitleaks.toml` in this repo. Stack-specific rules cover Resend, Neon Postgres, PostHog, and GitHub fine-grained PATs on top of the gitleaks defaults.

Consumers must place the file at `security/.gitleaks.toml` in their own repo. `security.yml` fails fast if missing:

```
https://raw.githubusercontent.com/coroboros/ci/main/security/.gitleaks.toml
```

</details>

---

## Examples

<details>
<summary><em>Standalone security scan (non-npm repo)</em></summary>

<br>

```yaml
# consumer-repo/.github/workflows/security.yml
name: Security
on:
  push:
    branches: [develop, main]
  pull_request:
  schedule:
    - cron: '0 0 * * 0'   # weekly — catches CVEs published after last push

permissions:
  contents: read

jobs:
  scan:
    uses: coroboros/ci/.github/workflows/security.yml@v0
```

</details>

<details>
<summary><em>Compose with <code>javascript/base</code></em></summary>

<br>

```yaml
jobs:
  custom:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    env:
      NPM_CONFIG_FILE: ${{ secrets.NPM_CONFIG_FILE }}
      NPM_EXTRA_CONFIG: ${{ vars.NPM_EXTRA_CONFIG }}
    steps:
      - uses: actions/checkout@v4
      - uses: coroboros/ci/.github/actions/check-docs@v0
      - uses: coroboros/ci/.github/actions/javascript/base@v0
      - run: pnpm run my-custom-script
        shell: bash
```

</details>

<details>
<summary><em>Compose a custom release pipeline (non-npm artifact)</em></summary>

<br>

```yaml
jobs:
  publish:
    if: ${{ github.ref_type == 'tag' }}
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          ref: main
          fetch-depth: 0
      - id: changelog
        uses: coroboros/ci/.github/actions/release/generate-changelog@v0
      # ...your publish step (docker push, gh release upload, etc.)...
      - uses: coroboros/ci/.github/actions/release/github-release@v0
        with:
          body: ${{ steps.changelog.outputs.body }}
```

</details>

---

## License

All Rights Reserved. See [LICENSE.md](LICENSE.md).
