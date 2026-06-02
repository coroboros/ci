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

**Imposed, not proposed.** Pipelines expose zero `inputs:`. Every Coroboros repo inherits identical install flags, publish auth, and security gates. Consumers wire it in.

- [Pipelines](#pipelines)
- [Composable actions](#composable-actions)
- [Development flow](#development-flow)
- [Environment](#environment)
- [Security](#security)
- [Examples](#examples)
- [License](#license)

---

## Pipelines

### `javascript-npm-packages.yml`

Bundled NPM CI.

Consumer requirements:
- `.node-version`
- `package.json` with
  - `packageManager: "pnpm@X.Y.Z"`, `scripts.lint`, `scripts.test`.
  - `scripts.build` is optional (auto-detected).
- `pnpm-lock.yaml` — required for `--frozen-lockfile`.

<details>
<summary><em>preflight</em></summary>

<br>

**Trigger**: `branch push`

**Sequence**:
1. Checkout
2. Run [`check-docs`](#composable-actions)
3. Run [`javascript/base`](#composable-actions)

</details>

<details>
<summary><em>supply-chain</em></summary>

<br>

**Trigger**: `every push`. Gates `publish` via `needs:` — a release waits on it.

`osv-scanner` scans `pnpm-lock.yaml` against [OSV.dev](https://osv.dev/). `javascript/base` already gates the install (Socket Firewall + `--frozen-lockfile`); this adds the known-CVE gate so a vulnerable dependency blocks the release, not just the parallel `security` scan. See [Security](#security).

</details>

<details>
<summary><em>publish</em></summary>

<br>

**Trigger**: `tag push`. Gated by `supply-chain` (`needs:`) — osv-scanner must pass first.

**Sequence**:
1. Checkout `main` with full history
2. Verify `main` HEAD matches the tag SHA
3. Run [`check-docs`](#composable-actions)
4. Run [`javascript/base`](#composable-actions)
5. Pin `package.json` version to the tag
6. Generate `CHANGELOG.md` section via [`release/generate-changelog`](#composable-actions)
7. Publish to npm — OIDC + provenance or token-based via `.npmrc` (see [Security](#security))
8. Create GitHub Release via [`release/github-release`](#composable-actions)
9. Commit release artifacts back to `main` via [`release/commit-artifacts`](#composable-actions)

</details>

<details>
<summary><em>security</em></summary>

<br>

**Trigger**: `every call`

Calls `security.yml` — see [Security](#security).

</details>

### `rust-packages.yml`

Bundled Cargo CI. Tag-driven release, same as the npm pipeline.

Consumer requirements:
- `rust-toolchain.toml` — pins the channel and lists the `clippy` + `rustfmt` components (`rustup` installs them on first `cargo` use; omit them and `fmt`/`clippy` fail on a pinned channel).
- `Cargo.toml` and a committed `Cargo.lock` — `clippy` and `test` run `--locked`.
- `deny.toml` — the cargo-deny supply-chain policy (sources, licenses, bans, advisories). See [Security](#security) for the baseline.
- `ci/setup.sh` — optional. Installs native build dependencies (a `-sys` crate's toolchain, test fixtures) and exports env via `$GITHUB_ENV`. A no-op when absent.
- crates.io publishing — configure [OIDC Trusted Publishing](#security), or set `CARGO_REGISTRY_TOKEN` to bootstrap the first publish of a new crate. Tagged builds always publish.

<details>
<summary><em>preflight</em></summary>

<br>

**Trigger**: `branch push`. **Matrix**: `ubuntu-latest`, `macos-latest`, `windows-latest`.

**Sequence**:
1. Checkout
2. Run [`check-docs`](#composable-actions)
3. Run [`rust/base`](#composable-actions)

</details>

<details>
<summary><em>supply-chain</em></summary>

<br>

**Trigger**: `every push`. Gates `publish` via `needs:` — a release waits on it.

`cargo-deny check` (SHA-pinned action) reads `deny.toml`: crate sources, licenses, bans, and advisories (vulnerabilities, unmaintained, yanked). Running on every push re-checks a tagged release against the latest advisory DB before it ships, not only at PR time. See [Security](#security).

</details>

<details>
<summary><em>publish</em></summary>

<br>

**Trigger**: `tag push`. Gated by `supply-chain` (`needs:`) — cargo-deny must pass first.

**Sequence**:
1. Checkout `main` with full history
2. Verify `main` HEAD matches the tag SHA
3. Run [`check-docs`](#composable-actions)
4. Run [`rust/native-deps`](#composable-actions) — native deps for the publish verify build
5. Pin `Cargo.toml` to the tag (`cargo set-version`)
6. Generate `CHANGELOG.md` section via [`release/generate-changelog`](#composable-actions)
7. `cargo publish` to crates.io — OIDC by default, token bootstrap for a new crate (see [Security](#security))
8. Create GitHub Release via [`release/github-release`](#composable-actions)
9. Commit `Cargo.toml`, `Cargo.lock`, `CHANGELOG.md` back to `main` via [`release/commit-artifacts`](#composable-actions)

</details>

<details>
<summary><em>security</em></summary>

<br>

**Trigger**: `every call`. Calls `security.yml`.

</details>

### `security.yml`

Reusable sub-workflow with three parallel scans:

- **`gitleaks`** — Installs `v8.30.1` (SHA-256 verified), scans git history with the [`security/.gitleaks.toml`](security/.gitleaks.toml) ruleset, fails on detected leaks. Emits SARIF as the `gitleaks-report` artifact (30-day retention).
- **`dependency-review`** — PR-only; needs repo's **Dependency graph** enabled. Fails on high-severity CVE introduced by the dep diff. Uses `actions/dependency-review-action@v4`.
- **`osv-scanner`** — Scans dependency manifests recursively against [OSV.dev](https://osv.dev/) via `google/osv-scanner-action@v2`, failing on any known vulnerability. Runs only when a supported manifest is present — `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock`, `Cargo.lock`, `go.mod`, `requirements.txt`, `poetry.lock`, `Pipfile.lock`, `pdm.lock`, `uv.lock`, `Gemfile.lock`, `composer.lock`. A repo with none — docs, config — skips the scan rather than failing on osv's no-manifest error. Per-repo exceptions go in an `osv-scanner.toml` at the repo root (`[[IgnoredVulns]]`). Extend the list in the `security/osv-scanner` composite as ecosystems land.

`gitleaks` and `osv-scanner` wrap the [`security/*` composites](#composable-actions) — the same definitions the package `supply-chain` gates reuse; `dependency-review` is inline. Imposed on every Coroboros workflow. Standalone wire-up — see [Examples](#examples).

---

**Notes** — pin via `@v0` (rolling major) or `@x.y.z`. `self-release.yml` moves `v0` to each stable release, so `@v0` always tracks the latest. `@x.y.z` pins the workflow file. The composite actions it calls are hardcoded `@v0`, so `@x.y.z` is not a full freeze — the nested actions still follow `v0`. Jobs run in parallel except each `publish`, which `needs: supply-chain` so the release is re-checked (cargo-deny for Rust, osv-scanner for npm) before it ships. `security.yml` scans in parallel for reporting — it does not gate `publish` (see [Security](#security)). The only sub-workflow call is `security` → `security.yml`.

---

## Composable actions

| Action | Type | Purpose |
| :--- | :--- | :--- |
| `check-docs` | transverse | Context dump + documentation check. |
| `javascript/base` | JavaScript | Sets up Node + corepack pnpm, caches the store, writes `.npmrc` from env, then installs, lints, builds (when present), tests. |
| `rust/base` | Rust | Resolves the toolchain from `rust-toolchain.toml`, caches the `~/.cargo` deps, runs [`rust/native-deps`](#composable-actions), then `cargo fmt --check`, `clippy -D warnings`, `test`. |
| `rust/native-deps` | Rust | Runs the optional `ci/setup.sh` native build-dependency hook. Shared by `rust/base` and the publish verify build. No-op when absent. |
| `security/gitleaks` | transverse | Installs gitleaks (SHA-256 verified), scans with the canonical ruleset, emits SARIF. The shared definition behind `security.yml` and self-CI. |
| `security/osv-scanner` | transverse | Scans dependency manifests for known vulnerabilities (OSV.dev); skips a repo with no supported manifest. Shared by `security.yml` and the npm `supply-chain` gate. |
| `security/cargo-deny` | Rust | Runs cargo-deny (sources, licenses, bans, advisories) against `deny.toml`. The Rust `supply-chain` gate. |
| `release/generate-changelog` | transverse | SemVer-strict tag guard + generates or reuses the `## vX.Y.Z` section in `CHANGELOG.md` from Conventional Commits. Outputs `body`. Idempotent. |
| `release/github-release` | transverse | Creates the GitHub Release for the current tag. Body typically chained from `release/generate-changelog` (see [Examples](#examples)). |
| `release/commit-artifacts` | transverse | Stages the given files and commits them back to `main` as `chore: release ${tag} [skip ci]`. No-op when nothing changed. |

---

## Development flow

Develop with Conventional Commits → tag → push. No manual CHANGELOG, no version bump.

Tags follow **SemVer strict** — `1.2.3`, never `v1.2.3`.

<details>
<summary><em>Branch models</em></summary>

<br>

**main-only** — feature branch → PR → squash-merge to `main` → tag the merge commit → push.

**develop + main** — PR into `develop` → tag → `release/x.y.z` branch → merge to `main` → `main` reflects production.

Nobody pushes directly to protected branches (`main`, `develop`, `release/x.y.z`).

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

Zero `inputs:` — configuration flows through the caller's `secrets:` block. Every npm-publish-related value is a **secret** (encrypted at rest, masked in logs); none are GitHub `vars`.

<details>
<summary><em>Secrets (caller's <code>secrets:</code> block)</em></summary>

<br>

| name | required | description |
| :--- | :---: | :--- |
| `NPM_CONFIG_FILE` | ✔ | `.npmrc` content. Written to repo root by `javascript/base`. `${VAR}` references inside are expanded by npm at install time. |
| `NPM_EXTRA_CONFIG` |  | Extra `.npmrc` lines appended after `NPM_CONFIG_FILE`. A **secret** — it lands in `.npmrc`, so it can carry auth material and must stay masked. |
| `NPM_PACKAGE_REGISTRY` | ✔ | npm package registry URL. |
| `NPM_PACKAGE_PROXY_REGISTRY` |  | Optional npm proxy registry URL. |
| `NPM_PACKAGE_REGISTRY_TOKEN` |  | npm Granular Access Token, scoped to the publishing organization with create-new-package permission. Required only for the token bootstrap (first publish of a new scoped package, before npm Trusted Publisher is bound). Absent → OIDC. |

</details>

<details>
<summary><em><code>javascript/base</code> env contract (standalone composition)</em></summary>

<br>

A composite reads `env`, not `secrets:`. Composing `javascript/base` outside the bundled pipeline, set the same `NPM_CONFIG_FILE` (required, fails if missing) and `NPM_EXTRA_CONFIG` (optional) from the Secrets table above at the caller's workflow- or job-level `env:`.

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

`sfw pnpm install --frozen-lockfile --ignore-scripts` runs inside `javascript/base` (Socket Firewall wraps the fetch — see Firewall below).

- `--frozen-lockfile` — fails on stale or tampered `pnpm-lock.yaml`. Gate against transitive-dependency injection.
- `--ignore-scripts` — skips lifecycle scripts (`preinstall`, `install`, `postinstall`) of every dependency. Cuts the postinstall supply-chain vector.

pnpm CLI resolved via corepack from `packageManager`. No floating version reaches the runner.

</details>

<details>
<summary><em>Firewall — Socket Firewall (<code>sfw</code>)</em></summary>

<br>

`javascript/base` installs Socket Firewall (`npm i -g sfw`, the free tokenless build) and runs the install through it (`sfw pnpm install ...`). `sfw` proxies the registry fetch and blocks packages Socket has confirmed malicious before they download. It is the GitHub-runner equivalent of the image-baked firewall in the GitLab pipeline.

Fail-closed: if `sfw` cannot install or run, the install step fails rather than fetching unprotected. The free build needs no account or token, and inspects public-registry fetches out of the box. Packages pulled through a private proxy registry pass uninspected — `sfw` knows the public npm registry, and the release-age [cooldown](#security) still covers them. The trade-off of the runtime install (no shared image) is a dependency on Socket's service at fetch time.

</details>

<details>
<summary><em>Cooldown — minimum release age</em></summary>

<br>

Quarantine freshly published versions so a hijacked release is not pulled inside the window most campaigns are caught in. pnpm 11 reads the setting from `pnpm-workspace.yaml`, not `.npmrc`. Add to the consuming repo:

```yaml
# pnpm-workspace.yaml
minimumReleaseAge: 10080            # 7 days, in minutes
minimumReleaseAgeExclude:
  - '@coroboros/*'                  # internal packages install immediately
```

On pnpm 10.x the `.npmrc` form `minimum-release-age=10080` also works. `@coroboros/*` is excluded so a pipeline can consume a just-published internal package.

</details>

<details>
<summary><em>Supply chain — Rust (<code>rust-packages.yml</code>)</em></summary>

<br>

The GitLab pipeline hardens npm at the image layer — cooldown, Socket Firewall, `--ignore-scripts`, digest pins. GitHub-hosted runners share no base image, so the Rust pipeline enforces the same risk model in the workflow:

| Risk | Rust control |
| :--- | :--- |
| Untrusted source, typosquat | `cargo-deny` sources — crates.io only; git and alternative registries denied |
| Lock drift, tampered dependencies | committed `Cargo.lock` + `--locked` on `clippy` and `test` — fails on a stale or altered lock |
| Known vulnerability | `osv-scanner` (Cargo.lock) and `cargo-deny` advisories — RustSec vulnerabilities, unmaintained, yanked |
| License drift | `cargo-deny` licenses — allow-list |
| Banned or wildcard dependency | `cargo-deny` bans |

`cargo-deny` runs on every push via a SHA-pinned action and gates `publish` (`needs:`), so a tagged release is re-checked against the latest advisory DB before it ships — `security.yml` scans in parallel for reporting and does not block the release. It reads the repo's `deny.toml`. The baseline:

```toml
[advisories]
version = 2
yanked = "deny"

[licenses]
version = 2
allow = [
  "MIT", "Apache-2.0", "Apache-2.0 WITH LLVM-exception", "BSD-2-Clause",
  "BSD-3-Clause", "0BSD", "ISC", "Zlib", "MPL-2.0", "Unicode-3.0",
  "Unlicense", "CDLA-Permissive-2.0", "BSL-1.0",
]

[bans]
multiple-versions = "warn"
wildcards = "deny"

[sources]
unknown-registry = "deny"
unknown-git = "deny"
```

**Publish auth.** crates.io publish uses OIDC Trusted Publishing by default — `rust-lang/crates-io-auth-action` mints a short-lived token per run, no long-lived secret in the repo. `CARGO_REGISTRY_TOKEN` is needed only to bootstrap the first publish of a new crate (Trusted Publishing binds to an existing crate); configure Trusted Publishing on crates.io afterwards and drop the token. The verify build runs on publish (no `--no-verify`). It compiles the packaged tarball standalone, catching a crate that only builds in-workspace before the immutable release lands.

Two residual risks have no clean CI control. Both are documented here:
- **Build scripts run.** `cargo` has no `--ignore-scripts`; `build.rs` and proc-macros execute at build time. `--locked`, `cargo-deny` bans, and dependency review reduce the exposure; they do not remove it.
- **No publish cooldown.** crates.io has no `minimumReleaseAge`, so a freshly hijacked version is held off by the committed lock and `cargo-deny` advisories rather than a time delay.

</details>

<details>
<summary><em>Recommended <code>NPM_CONFIG_FILE</code> contents</em></summary>

<br>

Minimal hardened `.npmrc` for every Coroboros consumer. Stored as a **secret** (encrypted; carries `${VAR}` expansions resolved at install time):

```ini
@coroboros:registry=https:${NPM_PACKAGE_REGISTRY}
save-exact=true
fund=false
audit=false
ignore-scripts=true
package-lock=false
lockfile=true
prefer-online=true
```

| Line | Why |
| :--- | :--- |
| `@coroboros:registry=https:${NPM_PACKAGE_REGISTRY}` | Scope-resolved registry — `${NPM_PACKAGE_REGISTRY}` expands from the same-named secret. |
| `save-exact=true` | Pin exact versions on `add` / `install`. |
| `fund=false` | Suppress funding noise in CI logs. |
| `audit=false` | `osv-scanner` (in `security.yml`) covers vulnerability scans natively. |
| `ignore-scripts=true` | Defense in depth against postinstall supply-chain attacks — backs up the `--ignore-scripts` flag already passed by `javascript/base` on every `pnpm install`. |
| `package-lock=false` | Prevent `npm` from emitting a parasitic `package-lock.json` in pnpm repos. |
| `lockfile=true` | Explicit `pnpm-lock.yaml` enablement. Required on pnpm `< 11.0.0` consumers, where the preceding `package-lock=false` is interpreted as `lockfile=false` and collides with `pnpm install --frozen-lockfile`. Pnpm `>= 11` already defaults to `true` and ignores `package-lock` for `pnpm-lock.yaml`, so the line is harmless there. |
| `prefer-online=true` | Re-fetch dep metadata each install — local cache cannot mask a yanked or republished version. |

</details>

<details>
<summary><em>Publish — OIDC vs token bootstrap</em></summary>

<br>

Auto-detected by `NPM_PACKAGE_REGISTRY_TOKEN` **secret** presence on the consumer repo:

| Token secret | Mode | Command |
| :--- | :--- | :--- |
| absent | **OIDC + provenance** (default) | `pnpm publish --provenance --no-git-checks` |
| present | **Token bootstrap** | `npm publish --ignore-scripts --access public` |

**OIDC + provenance** — no long-lived token in the repo; npm trusts a per-run id-token issued by GitHub Actions for `coroboros/<repo>/ci.yml`. Requires the npm Trusted Publisher form, which only accepts an existing package — so the very first publish has to take the token bootstrap below.

**Token bootstrap** — publishes the first version of a new scoped package. Set two additional **secrets** on the consumer (encrypted; forwarded via the caller's `secrets:` block):

| Secret | Contents |
| :--- | :--- |
| `NPM_PACKAGE_REGISTRY_TOKEN` | npm Granular Access Token scoped to the publishing organization with create-new-package permission. Long-lived; revoke after migrating to OIDC. |
| `NPM_EXTRA_CONFIG` | `${NPM_PACKAGE_REGISTRY}:_authToken=${NPM_PACKAGE_REGISTRY_TOKEN}` — appended to `.npmrc` by `javascript/base`. Stored as a **secret** because it carries auth expansion. |

`npm publish` is used on the bootstrap path (not `pnpm publish`) because pnpm `>= 11.1.3` in CI auto-attempts the OIDC token exchange and does not fall back to the `.npmrc` token if OIDC fails. `--ignore-scripts --access public` skips publish-time lifecycle hooks (`prepublishOnly` excepted — known `npm` behavior). The published tarball is identical to `pnpm publish`'s.

After the first publish, configure the npm Trusted Publisher form (Publisher type: GitHub Actions; Organization: the publishing org; Repository: consumer repo; Workflow filename: `ci.yml`; Environment: empty), then open a `chore(ci):` PR dropping `NPM_PACKAGE_REGISTRY_TOKEN` + `NPM_EXTRA_CONFIG` from the caller's `secrets:` block. Revoke the npm token. `1.0.1+` publishes via OIDC + provenance.

</details>

<details>
<summary><em>Secret isolation</em></summary>

<br>

Each `workflow_call.secrets:` block declares ONLY the secrets the job consumes. No `secrets: inherit` anywhere.

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

The `security/gitleaks` composite sparse-checks the file out of `coroboros/ci` at runtime — imposed, no consumer override.

</details>

---

## Examples

<details>
<summary><em><code>javascript-npm-packages.yml</code> wire-up</em></summary>

<br>

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
      # Token bootstrap (drop both after npm Trusted Publisher is wired — see Security):
      NPM_EXTRA_CONFIG: ${{ secrets.NPM_EXTRA_CONFIG }}
      NPM_PACKAGE_REGISTRY_TOKEN: ${{ secrets.NPM_PACKAGE_REGISTRY_TOKEN }}
```

</details>

<details>
<summary><em><code>rust-packages.yml</code> wire-up</em></summary>

<br>

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
    uses: coroboros/ci/.github/workflows/rust-packages.yml@v0
    permissions:
      contents: write   # GitHub Release + commit-back on tag
      id-token: write   # crates.io OIDC publish on tag
    secrets:
      # First publish of a new crate only — drop once Trusted Publishing is configured (see Security):
      CARGO_REGISTRY_TOKEN: ${{ secrets.CARGO_REGISTRY_TOKEN }}
```

</details>

<details>
<summary><em><code>security.yml</code> standalone (non-npm repo)</em></summary>

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
      NPM_EXTRA_CONFIG: ${{ secrets.NPM_EXTRA_CONFIG }}
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
      # ...the publish step (docker push, gh release upload, etc.)...
      - uses: coroboros/ci/.github/actions/release/github-release@v0
        with:
          body: ${{ steps.changelog.outputs.body }}
```

</details>

---

## License

All Rights Reserved. See [LICENSE.md](LICENSE.md).
