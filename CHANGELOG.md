# Changelog

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
