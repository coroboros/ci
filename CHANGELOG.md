# Changelog

## v1.2.0 - 12/05/2026

### Features
- Extract every reusable npm-package step into its own composite action under `.github/actions/`: `check-docs`, `check-npm-lint`, `check-npm-typecheck`, `build-js`, `test-npm-unit`, `pack-check`, `deploy-npm-package`, `post-deploy-commit-back`, `post-deploy-github-release`. Future workflows compose from atoms instead of re-inlining bash
- `build-js` honors GitLab's graceful-skip behavior — when `package.json` has no `scripts.build`, the step exits 0 (`skip-if-missing: true` default)
- `check-docs` gains optional `require-docs-dir` input for opt-in GitLab npm-packages parity (default `false` — README.md only)
- `deploy-npm-package` exposes the 4 publish modes (pnpm \| npm × oidc \| token) behind a single composite

### Refactoring
- `npm-ci.yml` and `npm-publish.yml` rewired onto the new composites — public API (inputs / secrets / outputs) unchanged
- `commits-lint.yml` — name the previously-anonymous step `check-commit-messages`
- `secrets-scan.yml` — rename steps to `setup-gitleaks-config`, `setup-gitleaks`, `security-scan-secrets` (`<stage>-<focus>` pattern)
- `ci.yml` — rename `Run actionlint` → `check-workflow-lint`, name the smoke step `check-tool-versions`
- `release.yml` — rename `Push floating major (vN) tag` job + step to `deploy-floating-major-alias`

### CI
- Pin `actionlint` to v1.7.12 (was floating on `main`)

### Documentation
- `CLAUDE.md` — composite table, factored-architecture rule, strict step-naming policy (every step carries `name:`)
- `README.md` — composite table, factored-consume example for custom workflows
- `MIGRATION_GITLAB_CI_TO_GITHUB_ACTIONS.md` — rewritten as faithful GitLab → GHA map. Per-composite map, divergence log extended (D13 `check-docs` README-only default, D14 per-step composite extraction), 1.2.0 wave entry, decommission-criteria status block

## v1.1.2 - 11/05/2026

### Documentation
- `LICENSE.md` — canonical Coroboros private-repo wording: `text, code, configuration, and any derivative work` (was per-repo scope `GitHub Actions workflows, composite actions, configuration, ...`). Identical content now across `coroboros/brain`, `coroboros/claude-config`, `coroboros/ci`.

## v1.1.1 - 11/05/2026

### Documentation
- `LICENSE.md` — flip from MIT to All Rights Reserved (private + org-internal repo; aligns with `coroboros/brain` and `coroboros/claude-config`). Copyright line carries the Coroboros `2026–End of Time` signature
- `README.md` — header badge `license-MIT` → `license-All Rights Reserved`; footer `[MIT](LICENSE.md)` → `All Rights Reserved. See [LICENSE.md](LICENSE.md).`
- `package.json` — `license` field `MIT` → `SEE LICENSE IN LICENSE.md` (SPDX-compatible value when the file is the source of truth)

## v1.1.0 - 11/05/2026

### Features
- Align `npm-ci.yml` and `npm-publish.yml` step names with the GitLab `npm-packages` reference: `check-docs`, `check-npm-lint`, `check-npm-typecheck`, `build-js`, `build-version`, `build-changelog`, `test-npm-unit`, `deploy-package`, `post-deploy-*`
- Add `check-docs` step — fail loud if `README.md` is missing at project root
- Reorder to GitLab stage sequence — `check → build → test → deploy` (tests now run against the built `dist/`)
- Add `bump-version-from-tag` composite — rewrites `package.json.version = github.ref_name` (GitLab `build-version` equivalent)
- Add `generate-changelog` composite — parses Conventional Commits since the previous tag, groups by type, prepends to `CHANGELOG.md`, exposes the rendered body for the GitHub release
- Add `auto-version` input on `npm-publish.yml` (default `true`) — CI bumps, generates the CHANGELOG entry, publishes, commits back to `default-branch`, and opens the GitHub release. Set `auto-version: false` to keep the verify-only path
- Add lightweight stage-banner comments inside the workflows so reviewers can read the GitLab → GHA mapping at a glance

### Documentation
- README rewritten around the auto-version flow with explicit stage map
- `MIGRATION_GITLAB_CI_TO_GITHUB_ACTIONS.md` rewritten — per-job mapping, divergence log, wave plan

## v1.0.0 - 11/05/2026

Initial release of `coroboros/ci`.
