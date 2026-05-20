# Changelog

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
