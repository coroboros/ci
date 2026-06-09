# Changelog

## v0.2.3 - 09/06/2026

### Fixes
- `rust-packages` — `dist-host` seeds `target/distrib/dist-manifest.json` from the plan manifest and redirects the global build's own manifest to `$RUNNER_TEMP`. `dist build --artifacts=global` reads `dist-manifest.json` to assemble the installers, Homebrew formula, and npm shim; the previous `> target/distrib/dist-manifest.json` truncated that file before dist read it (`EOF while parsing JSON`), so the first native-CLI binary release never produced the formula or shim.

## v0.2.2 - 08/06/2026

### Configuration
- Bump the pinned action SHAs (Dependabot): `actions/checkout` v6, `actions/setup-node` v6, `actions/upload-artifact` v7, `actions/download-artifact` v8, `actions/dependency-review-action` (v4 SHA), `renovatebot/github-action` v46.1.15.

## v0.2.1 - 08/06/2026

### Refactor
- `self.yml` → `self-lint`, `self-actions` → `self-test` — align the self-CI workflow names (`self-lint` · `self-test` · `self-security` · `self-release`).

### Tests
- `self-test` — self-test `rust/base` end-to-end on a Rust fixture crate (`test/fixtures/rust-crate`): stage it at the workspace root, run the composite, assert `fmt` / `clippy` / `test` pass.
- `self-security` — self-test the `security-gate.yml` and `security.yml` reusable workflows via local `./` refs, now that `v0` carries the security composites.

### Documentation
- `README` — add a Self-CI section documenting how the repo tests its own workflows and composites.

### Configuration
- `.gitignore` — add `target/` for Rust build artifacts.

## v0.2.0 - 08/06/2026

### Features
- `rust-packages` — bundled Cargo pipeline: `preflight` (fmt / clippy / test on Linux, macOS, Windows), `security-gate`, branch-time `package`, tag-driven `publish` to crates.io, and the advisory `security` scan. Publish uses OIDC Trusted Publishing (`CARGO_REGISTRY_TOKEN` bootstraps a new crate) and re-runs fmt / clippy / test + `cargo publish`'s verify build on the tagged commit.
- `rust-packages` — opt-in binary distribution via cargo-dist `0.32.0`, gated on `[package.metadata.dist]`: prebuilt per-target archives, shell / powershell installers, a Homebrew formula in the declared `tap`, and an npm shim, attached to the GitHub Release (draft → undraft). Library crates self-skip. Optional `HOMEBREW_TAP_TOKEN` / `NPM_PACKAGE_REGISTRY_TOKEN` activate the tap and npm publishes.
- `rust-packages` — host native/C++ CLIs: the `dist-build` matrix exports `CARGO_DIST_TARGET` to the consumer's `ci/setup.sh`, which provisions the cross-toolchain per target. Host preflight runs unchanged.
- `rust-packages` — branch-time `package` job (`cargo package --locked`) verify-builds the packaged crate, so a dropped compile-time asset (`include_str!` / `build.rs` input) fails the PR, not the tagged publish.
- `security-gate` — blocking pre-release gate in its own reusable workflow that each `publish` `needs:`: `supply-chain` (cargo-deny for Rust, osv-scanner otherwise) + `secret-scan` (gitleaks). A vulnerability or leaked secret blocks the release through the job graph, unbypassable. Parity with the GitLab `security-gate` stage; the advisory `security.yml` reports in parallel.
- `rust/base`, `rust/native-deps`, `rust/test-deps` — composites. `rust/base` installs the toolchain, caches cargo + target, runs the optional `ci/setup.sh` and `ci/test-setup.sh` hooks (`ci/test.env` → job env), lints, and tests — so fixture-gated tests fail loud instead of skipping.
- `javascript/base` — wrap `pnpm install` in Socket Firewall (`sfw`), fail-closed, blocking confirmed-malicious packages before download.
- `self-release` — move the rolling `v0` tag to each stable release, so `@v0` tracks the latest without a manual push.

### Fixes
- `rust-packages` — gate `publish` on `dist-build` so a failed binary build never publishes; a library crate (no `dist-build`) still does. Serialize a repo's releases with a `concurrency` group, and rebase-retry the Homebrew tap push.
- `rust-packages` — pin the `dist-*` checkouts to the tag commit, not the moving `main`; `verify-tag` stays on `publish`, the only job pushing back to `main`.
- `rust-packages` — `dist-plan` reads `[package.metadata.dist]` or `[workspace.metadata.dist]`, so a cargo-dist 0.32 workspace layout isn't misread as a library crate.
- `rust-packages` — guard `cargo publish` with a dirty-file allowlist (`Cargo.toml` / `Cargo.lock` / `CHANGELOG.md`); an unexpected dirty file fails the release instead of shipping under `--allow-dirty`.
- `rust-packages` — `--provenance` on both npm-shim publish paths.
- `rust/base` — install the `rust-toolchain.toml` channel explicitly with `rustfmt` + `clippy`.
- `javascript-npm-packages` — gate `publish` on `security-gate` (osv-scanner + gitleaks); a vulnerability or leaked secret now blocks the npm release.
- `javascript-npm-packages` — add the per-ref `concurrency` group, so two tags can't race the commit-back to `main`.
- `release` — drop the "move rolling major tag" step from publish; reusable workflows run in the caller's context, so it force-pushed a meaningless `vN` into every consumer. `v0` now moves via `self-release`.

### Refactor
- `security` — split the blocking scans into `security-gate.yml` and keep `security.yml` advisory, so the gate scans run once (`publish` `needs:` one `security-gate` job). Supply-chain auto-routes by ecosystem; `licenses` moves to advisory (`continue-on-error`) — compliance, not a release blocker — matching GitLab.
- `security` — extract gitleaks, osv-scanner, and cargo-deny into `security/*` composites, reused by both workflows and self-CI. osv scans only when a supported manifest exists; `security/rust/cargo-deny` imposes the canonical `deny.toml` via `--config` (consumer `deny.toml` ignored, `deny.exceptions.toml` rejected) and takes a `checks` input (`advisories bans sources` for the gate, `licenses` for the advisory layer).
- `release/*`, `rust/pin-version` — extract the commit-back, tag-verify, and version-pin blocks duplicated across the tag-time jobs into composites.
- `rust/install-dist` — composite installing cargo-dist's `dist` from the prebuilt, SHA-256-verified tarball (Linux/macOS/Windows), replacing a multi-minute from-source `cargo install`.
- `rust/pin-version` — install only the `cargo-set-version` binary, not all of cargo-edit (~75% less build).
- `security/rust/cargo-deny` — drop the redundant `--deny unmaintained --deny unsound` flags; the imposed `deny.toml` already errors on both.

### Performance
- `rust/base`, `dist-build` — replace the hand-rolled cache with `Swatinem/rust-cache` (`v2.9.1`): keeps `-sys` / CMake dirs, forces `CARGO_INCREMENTAL=0`. `dist-build` keys per target triple; `rust/base` writes only from the default branch.

### Tests
- `self-actions` — new self-CI exercising the composites on every PR via local refs: `release/verify-tag`, `release/generate-changelog`, `release/commit-artifacts`, `security/rust/cargo-deny` override-reject, `rust/install-dist` on three OSes, and the `rust/native-deps` / `rust/test-deps` hooks. Tag-driven paths reading the runner's `GITHUB_REF_NAME` / `GITHUB_SHA` stay validated at real release time.

### Documentation
- `README`, `CLAUDE.md` — document the native-CLI contract (`ci/setup.sh` target-aware, `ci/test.env`, `ci/test-setup.sh`), the `deny.toml` advisory escape-hatch, the Rust and npm supply-chain controls, publish auth, and the binary-distribution consumer contract (cargo-dist 0.32 workspace keys + `allow-dirty = ["ci"]`, tap/npm secrets).
- `SECURITY.md` — add the security policy (vulnerability reporting, 30-day disclosure default).

### Configuration
- `package.json` — bump to `0.2.0`.
- `renovate.json` + `renovate.yml` — self-hosted Renovate auto-bumps the version-pinned tooling via review-gated PRs; a `postUpgradeTask` re-syncs each tarball SHA-256 in the same PR so version and checksum never drift.

## v0.1.14 - 01/06/2026

### Fixes
- `javascript-npm-packages` — add `--ignore-scripts` to the OIDC `pnpm publish` path, skipping publish-time lifecycle scripts. Parity with the token path (already `--ignore-scripts`) and with `coroboros/ci` on GitLab; defense in depth against a publish-time `prepack`/`postpack` payload.

### Configuration
- `package.json` — bump `packageManager` to `pnpm@11.1.2`, aligning the repo with the Coroboros stack's pnpm 11 baseline (GitLab CI templates and `nodejs-*` images). The token publish path stays on `npm publish`, so the pnpm-11 OIDC regression that pinned `10.33.0` does not resurface.

## v0.1.13 - 20/05/2026

### Documentation
- `README` — add `lockfile=true` to the recommended `NPM_CONFIG_FILE` template. Pnpm `< 11.0.0` interprets the preceding `package-lock=false` line as `lockfile=false`, disabling `pnpm-lock.yaml` reads and breaking `pnpm install --frozen-lockfile` in `javascript/base`. The new line re-enables pnpm's lockfile explicitly on pnpm 10.x and is harmless on pnpm `>= 11`, where `lockfile=true` is already the default and `package-lock` is scoped to npm's lockfile only.

## v0.1.12 - 20/05/2026

### Documentation
- `README` — document the recommended hardened `NPM_CONFIG_FILE` `.npmrc` (per-line rationale) and the token bootstrap auth setup (`NPM_PACKAGE_REGISTRY_TOKEN` + `NPM_EXTRA_CONFIG` secrets, why `npm publish` is used on that path, migration token → OIDC after first publish). Reaffirms that every npm-publish-related value is a **secret** (encrypted), not a GitHub `var`. Reflects the v0.1.11 token-path hardening.

## v0.1.11 - 20/05/2026

### Fixes
- `javascript-npm-packages` — pass `--ignore-scripts --access public` to `npm publish` on the token bootstrap path. Defense in depth against postinstall-worm supply-chain attacks: install-time scripts are already skipped by `pnpm install --frozen-lockfile --ignore-scripts` in `javascript/base`; the publish flag now also skips `prepack`/`postpack`/`publish`/`postpublish` while the long-lived bootstrap token is in env. `prepublishOnly` still runs (known `npm publish` behavior — the flag does not cover it), but it invokes our own gates from the frozen lockfile that already ran in the base action. The bootstrap token's exposure narrows to one publish — switch to OIDC + provenance via Trusted Publisher for `1.0.1+` to eliminate the long-lived token entirely.

## v0.1.10 - 20/05/2026

### Fixes
- `javascript-npm-packages` — use `npm publish` for the token bootstrap path. v0.1.5 → v0.1.9 chased pnpm-side workarounds (env vars, configs, npx version pin, standalone binary download with SHA verify, `manage-package-manager-versions=false`) and each one hit a different pnpm 10/11 dead-end: pnpm 11 auto-attempts OIDC without `.npmrc` fallback; pnpm 10.33.0 via `npx` is intercepted by corepack; the standalone 10.33.0 binary self-switches on `packageManager: pnpm@11.x` and crashes against its own snapshot. `npm publish` is not managed by corepack, does not auto-attempt OIDC, reads `_authToken` from `.npmrc` directly, and produces an identical tarball (same `files`, same `prepublishOnly`). The OIDC branch (`pnpm publish --provenance --no-git-checks`) is unchanged — pnpm OIDC works once a Trusted Publisher is bound; only the pre-Trusted-Publisher bootstrap takes the npm CLI path. Revert to a single `pnpm publish` once pnpm 11.x's bootstrap-via-token regression is upstream-fixed.

## v0.1.9 - 20/05/2026

### Fixes
- `javascript-npm-packages` — pass `--config.manage-package-manager-versions=false` to the pinned pnpm 10.33.0 binary so it does not attempt to self-switch to the consumer's `packageManager` pin. v0.1.8 successfully fetched and SHA-verified `pnpm-linux-x64@10.33.0`, but pnpm 10.33.0 read `packageManager: pnpm@11.x` from the package's `package.json` and tried `pnpm add @pnpm/exe@11.x`, which crashes against the single-file standalone binary (`/snapshot/dist/pnpm.cjs not found`). Disabling the self-switch keeps the pinned 10.33.0 running for the publish call only.

## v0.1.8 - 20/05/2026

### Fixes
- `javascript-npm-packages` — fetch the pnpm 10.33.0 standalone binary directly for the token publish path. v0.1.7's `npx -y pnpm@10.33.0 publish` was intercepted by corepack — every `pnpm` invocation in a project with a `packageManager` field goes through the corepack shim, including the binary that `npx` resolves to, so the consumer's `pnpm@11.x` ran anyway and the same `ERR_PNPM_AUTH_TOKEN_EXCHANGE` 404 surfaced. The fix downloads `pnpm-linux-x64` from the pinned `v10.33.0` GitHub release into `${RUNNER_TEMP}`, verifies its SHA-256 (`8d4e8f7d778e8ac482022e2577011706a872542f6f6f233e795a4d9f978ea8b5`), and executes it by absolute path. Bypasses corepack entirely; the consumer package's own `packageManager` pin is untouched. The OIDC branch (`pnpm publish --provenance --no-git-checks`) is unchanged. Revert to a single pnpm version once pnpm 11.x's bootstrap-via-token regression is upstream-fixed.

## v0.1.7 - 20/05/2026

### Fixes
- `javascript-npm-packages` — invoke pnpm 10.33.0 via `npx` for the token publish path only. v0.1.5 (`env -u`) and v0.1.6 (`NPM_CONFIG_PROVENANCE=false`) both failed to stop pnpm `>= 11.1.3` from attempting OIDC in CI; after OIDC fails (no Trusted Publisher on a bootstrap publish), pnpm 11.x does not fall back to the `.npmrc` `_authToken` and the PUT 404s. pnpm 10.33.0 has no OIDC code path, reads `_authToken` from `.npmrc` directly, and publishes. Using `npx pnpm@10.33.0` keeps the consumer package's own `packageManager` pin (typically `pnpm@11.x`) intact — corepack still drives every other step (`install`, `lint`, `build`, `test`, the OIDC branch); only the token-path `pnpm publish` call uses 10.33.0. The OIDC branch (`pnpm publish --provenance --no-git-checks`) is unchanged. Revert to a single pnpm version once the pnpm 11.x bootstrap-via-token regression is upstream-fixed.

## v0.1.6 - 20/05/2026

### Fixes
- `javascript-npm-packages` — disable provenance auto-detection on the token publish path. v0.1.5's `env -u` of the GitHub OIDC env vars caused pnpm `>= 11.1.3` to emit `ERR_PNPM_ID_TOKEN_GITHUB_WORKFLOW_INCORRECT_PERMISSIONS` and still fail the PUT with 404 — pnpm in CI auto-enables `provenance=true` regardless of the OIDC env vars, and skipping OIDC after the auto-enable leaves the publish without usable auth. Set `NPM_CONFIG_PROVENANCE=false` on the token-path command instead: pnpm sees provenance explicitly disabled, never attempts OIDC, and reads `_authToken` from `.npmrc` directly. The OIDC branch is unchanged. Workflow stays pnpm-version-agnostic.

## v0.1.5 - 20/05/2026

### Fixes
- `javascript-npm-packages` — isolate the token publish path from pnpm 11's auto-OIDC. pnpm `>= 11.1.3` auto-attempts the OIDC token exchange whenever `ACTIONS_ID_TOKEN_REQUEST_URL` / `ACTIONS_ID_TOKEN_REQUEST_TOKEN` are present (GitHub sets them when `id-token: write` is granted at the job level — required for the post-bootstrap OIDC branch). On the token bootstrap path (a new scoped package without a Trusted Publisher binding, or any token-locked exception), the auto-attempt resolves to 404 from npm and pnpm then publishes with no usable auth — the PUT fails with 404. The fix `env -u`'s both vars on the token-path command only — the OIDC branch is unchanged. Keeps the workflow pnpm-version-agnostic: both 10.x and 11.x work on the token path, and 11.x (>= 11.0.7) still drives OIDC when the token is absent.

## v0.1.4 - 15/05/2026

### Fixes
- `javascript-npm-packages` — read `NPM_EXTRA_CONFIG` from `secrets`, not `vars`. It is appended verbatim into `.npmrc`, so it can carry auth material; a variable would expose that in plaintext and in logs. Declared as an optional `workflow_call` secret; callers forward it via their `secrets:` block.

## v0.1.3 - 15/05/2026

### Fixes
- `javascript-npm-packages` — add `--no-git-checks` to the `pnpm version` step. pnpm 11 refuses to bump on an unclean working tree (the install/build steps dirty it beforehand); pnpm 10 did not check. Without the flag the publish job fails with `ERR_PNPM_UNCLEAN_WORKING_TREE` on every pnpm 11 consumer.

## v0.1.2 - 15/05/2026

### Fixes
- `release/generate-changelog` — append a trailing newline before the heredoc closing delimiter so reused CHANGELOG sections set the GitHub Actions output correctly. Without it, `$(awk)` substitution stripped the trailing newline and `CHANGELOG_EOF` landed on the same line as the last body character, failing the parser with `Matching delimiter not found`.

## v0.1.1 - 14/05/2026

### Fixes
- `release/generate-changelog` — switch `git log --pretty=format:` to `--pretty=tformat:` so the last commit line is read by the `while read` loop. Previously, a single-commit range produced an empty body and fell back to `- Release X.Y.Z`.

## v0.1.0 - 14/05/2026

Initial release.

### Features
- Reusable workflow `javascript-npm-packages.yml` — three jobs gated by trigger event: `preflight` (branches), `publish` (tags), `security` (every call). Publish mode auto-detected: OIDC + `--provenance` or token-based via `.npmrc`.
- Reusable workflow `security.yml` — three parallel scans: `gitleaks`, `dependency-review`, `osv-scanner`. Canonical gitleaks ruleset sparse-checked out from `coroboros/ci` at runtime.
- Composite actions: `check-docs` (transverse), `javascript/base` (JS pipeline), `release/generate-changelog` + `release/github-release` (transverse release).
- Canonical gitleaks ruleset (`security/.gitleaks.toml`) — Resend, Neon Postgres, PostHog, and GitHub fine-grained PATs on top of the gitleaks defaults.
- `.github/dependabot.yml` — weekly grouped auto-PRs for pinned third-party actions.
- Self-CI workflows: `actionlint` + `yamllint` + `shellcheck`; security scans on push and PR.
