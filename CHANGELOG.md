# Changelog

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
