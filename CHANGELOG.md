# Changelog

## v0.2.0 - 06/06/2026

### Features
- `rust-packages` — host native/C++ CLIs without the shared pipeline learning zig, clang, or musl: the `dist-build` matrix exports `CARGO_DIST_TARGET` (the resolved target triple) to `rust/native-deps`'s `ci/setup.sh`, so a consumer provisions the cross-toolchain per target. Host preflight sees an empty target and runs unchanged; the shared pipeline installs no cross-toolchain itself.
- `rust/test-deps` — composite loading the optional `ci/test.env` (`KEY=value` lines → job environment) and running the optional `ci/test-setup.sh` fixture hook before `cargo test`, so model/ffmpeg-gated tests fail loud instead of silently skipping. `rust/base` runs it; a pure-Rust consumer without the files is unaffected.
- `rust-packages` — bundled Cargo pipeline: `preflight` (`cargo fmt --check` / `clippy -D warnings` / `test` on a Linux, macOS, Windows matrix), `supply-chain` (`cargo-deny`), tag-driven `publish` to crates.io, and the shared `security` scan. `supply-chain` runs on every push and gates `publish` (`needs:`), so cargo-deny re-checks the release against the latest advisory DB before it ships rather than scanning in parallel. Publish authenticates with crates.io OIDC Trusted Publishing by default (`rust-lang/crates-io-auth-action`); `CARGO_REGISTRY_TOKEN` is the first-publish bootstrap for a new crate. `publish` re-runs `rust/base` (fmt / clippy / test) on the tagged commit before `cargo publish`, mirroring the npm pipeline, so a library crate is re-validated at tag time and not only at PR time; `cargo publish`'s own verify build then runs with no `--no-verify`, so a crate that only builds in-workspace fails before an immutable release.
- `rust-packages` — add a branch-time `package` job (`cargo package --locked`, after `rust/native-deps`) that verify-builds the crate from its packaged tarball. A compile-time asset — an `include_str!`/`include_bytes!` file or a `build.rs` input — dropped from the package by an `exclude`/`.gitignore` rule now fails the PR rather than the tagged `cargo publish`, which verify-builds the same tarball at release time.
- `rust-packages` — opt-in binary-distribution layer via cargo-dist (`dist` `0.32.0`), gated on `[package.metadata.dist]`. A tagged binary crate gets prebuilt per-target archives, `shell` + `powershell` installers, a Homebrew formula in the declared `tap`, and an npm shim — attached to the single GitHub Release, alongside the crates.io publish. The pipeline stays the sole release authority: `dist` only builds (final URLs derive from repo + tag), and the release goes live through draft → undraft. Library crates self-skip. Adds `dist-plan`, `dist-build`, `dist-host`, `dist-publish` (gated by `cargo-deny` + `gitleaks`) and a `draft` input on `release/github-release`; optional `HOMEBREW_TAP_TOKEN` and `NPM_PACKAGE_REGISTRY_TOKEN` secrets activate the tap and npm publishes.
- `rust/base`, `rust/native-deps` — composites. `rust/base` installs the `rust-toolchain.toml` channel, caches `~/.cargo` + `target/`, runs the optional `ci/setup.sh` native-dependency hook, then lints and tests; `rust/native-deps` is that hook, shared with the `dist-build` matrix.
- `javascript/base` — wrap `pnpm install` in Socket Firewall (`sfw`), blocking confirmed-malicious packages before download. Fail-closed. The GitHub-runner equivalent of the image-baked firewall on GitLab.
- `self-release` — move the rolling `v0` major tag to each stable `coroboros/ci` release, so `@v0` consumers track the latest release without a manual tag push.
- `secrets` gate — gitleaks gates `publish` via `needs:` in the npm and Rust package workflows, alongside the supply-chain gate. A leaked secret blocks the release through the template's job graph, not the consumer's branch protection — parity with the GitLab `security-gate` stage.

### Fixes
- `rust-packages` — gate `publish` on `dist-build` (`needs:` plus an explicit `!cancelled() && … && needs.dist-build.result != 'failure'`), so a failed binary build never produces a crates.io publish while the GitHub release stays a draft; a library crate (`dist-build` skipped) still publishes. Add a `concurrency` group that serializes a repo's releases — keyed per-repo on tags so one release's commit-back can't race another's, per-ref on branches where superseded CI cancels — and a `git pull --rebase` retry around the Homebrew tap push so concurrent releases don't clobber the shared tap.
- `javascript-npm-packages` — add the ref-keyed `concurrency` group (tags serialize per repo, branches key per ref and cancel superseded CI), matching `rust-packages`, so two release tags can't race `release/commit-artifacts`' push to `main`.
- `rust/base` — install the `rust-toolchain.toml` channel explicitly (`rustup toolchain install` with `rustfmt` + `clippy`) instead of relying on lazy auto-resolution on the first `cargo` invocation.
- `rust-packages` — pass `--provenance` on both npm-shim publish paths (token bootstrap and OIDC), attesting the shim via the job's `id-token` regardless of the auth path.
- `javascript-npm-packages` — gate `publish` on a new `supply-chain` job (osv-scanner, `needs:`). A known vulnerability now blocks the npm release; previously osv-scanner ran only in the parallel `security` job and could not stop a publish.
- `release` — drop the "move rolling major tag" step from the npm and Rust publish jobs. Reusable workflows run in the caller's context, so it force-pushed a meaningless `vN` ref into every consumer repo; the `v0` ref now moves on `coroboros/ci`'s own release (see `self-release`).
- `rust-packages` — pin the `dist-plan`, `dist-build`, `dist-host` checkouts to the tag commit (`ref: ${{ github.sha }}`) rather than the moving `main`, dropping the unused `fetch-depth: 0` and `dist-plan`'s now-redundant `verify-tag`. The per-target binaries build the exact source the tag points to regardless of the `publish` commit-back timing; `verify-tag` stays on the `publish` jobs, the only ones that check out `main` to push back.
- `rust-packages` — `dist-plan` detects binary distribution from `[package.metadata.dist]` or `[workspace.metadata.dist]`, so a cargo-dist 0.32 workspace-layout consumer isn't misread as a library crate.
- `rust-packages` — guard `cargo publish` with a `git status --porcelain` allowlist (`Cargo.toml`/`Cargo.lock`/`CHANGELOG.md`); an unexpected dirty file now fails the release before the immutable crates.io publish instead of shipping silently under `--allow-dirty`.

### Refactor
- `rust-packages`, `javascript-npm-packages` — rename the `secrets` gate job to `secret-scan`, disambiguating it from the workflow's `secrets:` block; the dependent `publish` (and `rust-packages` `dist-build`) `needs:` follow.
- `security` — extract the gitleaks, osv-scanner, and cargo-deny scanners into `security/*` composites (single source). `security.yml` references them and the package `supply-chain` gates reuse them, so osv-scanner is defined once. The osv composite scans only when a supported manifest is present (`pnpm-lock.yaml`, `Cargo.lock`, `go.mod`, and the rest), so a dependency-less repo wiring in `security.yml` skips the scan instead of failing on osv's no-manifest error. `self-security.yml` runs the composites via local refs to self-test them pre-release. The `cargo-deny` composite imposes a canonical `security/deny.toml` via `--config` — a consumer `deny.toml` is ignored and a `deny.exceptions.toml` is rejected.
- `release/commit-artifacts` — extract the commit-back step shared by the npm and Rust publish jobs into a composite (`files` input, `[skip ci]`), mirroring GitLab's `commit-release-artifacts`.
- `release/verify-tag`, `rust/pin-version` — extract two blocks that were duplicated across the tag-time jobs into composites (single source). `release/verify-tag` is the "main HEAD matches the tag SHA" guard shared by the npm and Rust `publish` jobs; `rust/pin-version` is the `cargo-set-version` install + `cargo set-version` stamp shared by `publish` and the three `dist-*` jobs.
- `security/cargo-deny` — drop the redundant `--deny unmaintained --deny unsound` CLI flags. The imposed `deny.toml` already errors on both at `"all"` scope (the v2 advisories schema cannot downgrade them), so the policy stays single-sourced in the ruleset.
- `rust/pin-version` — move the `cargo-edit` version pin into the composite as a step-level env; it lived at the `rust-packages` workflow level. The composite is now self-contained like `security/gitleaks`, with the pin declared where it is consumed and callable standalone.
- `rust/install-dist` — new composite installing cargo-dist's `dist` from the prebuilt, SHA-256-verified release tarball (per-OS: Linux/macOS/Windows), shared by `dist-plan`/`dist-build`/`dist-host`. Replaces a multi-minute `cargo install --locked` from-source compile in each and satisfies the binary-pinning rule (version + checksum, like `security/gitleaks`); the version pin lives in the composite.
- `rust/pin-version` — install only the `cargo-set-version` binary (`cargo install --bin`), the one subcommand used, instead of all of cargo-edit — ~75% less from-source build. cargo-edit ships no prebuilt binary, so the source install stays.

### Performance
- `rust/base`, `dist-build` — replace the hand-rolled `~/.cargo` cache with `Swatinem/rust-cache` (`v2.9.1`), caching `~/.cargo` + `target/` soundly: it keeps `-sys` / CMake `out/` dirs and `registry/src`, prunes the rest, and forces `CARGO_INCREMENTAL=0` (so a C++/CMake build is not recompiled every run, and the installed `cargo-set-version` is cached). `dist-build` keys the cache per target triple to avoid cross-leg poisoning; `rust/base` writes only from the default branch.

### Tests
- `self-actions` — smoke `rust/native-deps` target passthrough (empty on host preflight, the exported triple on a cross leg) and `rust/test-deps` (absent → no-op; present → `ci/test-setup.sh` runs and `ci/test.env` propagates to the job environment).
- `self-actions` — new self-CI workflow exercising the composites on every PR via local refs: `release/verify-tag` (HEAD match + moved-HEAD failure), `release/generate-changelog` (SemVer-gate rejection of a non-tag ref), `release/commit-artifacts` (push / no-op / `FILES` word-split against a local bare remote, `contents: read` backstop), `security/cargo-deny` (consumer-override reject guard), and `rust/install-dist` (download + checksum + run on Linux, macOS, Windows — the zip and tarball extraction paths differ). A regression in the reachable logic now fails the PR. Tag-driven paths that read the runner's `GITHUB_REF_NAME`/`GITHUB_SHA` (generate-changelog auto-gen, pin-version stamp) can't be faked on a non-tag event — those reserved defaults aren't overridable into a composite — so they stay validated at real release time.

### Documentation
- `README`, `CLAUDE.md` — document the native-CLI consumer contract (`ci/setup.sh` target-aware via `CARGO_DIST_TARGET`, `ci/test.env`, `ci/test-setup.sh`; each optional and a no-op when absent), the `deny.toml` escape-hatch for an unfixable transitive advisory (a justified central `ignore`, never per repo), and that the shared dist binaries are CPU-only so a consumer may keep a supplemental per-package workflow.
- `README`, `SECURITY.md` — document the Rust supply-chain model (`cargo-deny` baseline, residual `build.rs` and no-cooldown gaps), the Socket Firewall and release-age cooldown, and the publish auth paths; collapse cross-references to remove duplication; add the `sfw` proxy-inspection caveat for parity with GitLab; document the opt-in binary-distribution layer (jobs, consumer contract, optional tap/npm secrets) and the imposed `cargo-deny` ruleset.
- `README` — correct the `release/verify-tag` row (shared by the npm and Rust `publish` jobs, not "every job that acts on `main`"; the `dist-*` jobs pin to the tag commit) and the cargo-dist install note (`rust/install-dist`, prebuilt + SHA-256 verified); add the `rust/install-dist` composable row.
- `README` — binary-distribution consumer contract: cargo-dist `0.32` takes its workspace-global keys (`cargo-dist-version`/`ci`/`publish-jobs`/`allow-dirty`) from `[workspace.metadata.dist]` only, and needs `allow-dirty = ["ci"]` so `dist plan` doesn't claim its own workflow — without these a binary consumer's `dist plan` fails.

### Configuration
- `package.json` — bump to `0.2.0` (was `0.1.13`, lagging the `0.1.14` tag).
- `renovate.json` + `renovate.yml` — self-hosted Renovate (scheduled workflow, `RENOVATE_TOKEN` PAT) auto-bumps the version-pinned tooling (gitleaks, actionlint, yamllint, cargo-dist, cargo-edit) via review-gated PRs, scoped so Dependabot keeps the action SHAs. A `postUpgradeTask` (`.github/renovate/sync-tool-sha.sh`) re-syncs each paired tarball SHA-256 to the bumped version in the same PR, so version and checksum never drift.

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
