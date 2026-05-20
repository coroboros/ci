# Changelog

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
