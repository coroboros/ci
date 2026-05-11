# coroboros/ci

Reusable GitHub Actions workflows + composite actions for `@coroboros/*` repos. Private. Full roadmap per `../MIGRATION_GITLAB_CI_TO_GITHUB_ACTIONS.md`.

## Canonical rules

Global rules (`~/.claude/rules/*`) inherit automatically — tech-standards, writing, find-docs, git-conventions, privacy, overrides, changelog. Divergences below.

## Tech Stack

- GitHub Actions (composite + `workflow_call`).
- YAML only. No application code, no runtime deps.
- Node.js 22 LTS (consumer-side, default in `setup-pnpm-node`).

## Commands

- `actionlint -color` — lint workflows + composite actions. Install: `brew install actionlint`.

## Important Files

- `.github/workflows/npm-ci.yml` — matrix verify (`check-docs` → `check-npm-lint` → `check-npm-typecheck` → `build-js` → `test-npm-unit`) + PR `pack-check`
- `.github/workflows/npm-publish.yml` — tag-triggered release: bump → changelog → publish → commit-back → GitHub release
- `.github/workflows/commits-lint.yml` — PR commit-range lint via `commitlint`
- `.github/workflows/secrets-scan.yml` — gitleaks against canonical `.gitleaks.toml`
- `.github/workflows/ci.yml` — this repo's own CI (actionlint + composite smoke)
- `.github/workflows/release.yml` — this repo's release (floating-major alias-tag pusher)
- `.github/actions/setup-pnpm-node/` — `pnpm` + `actions/setup-node` + `pnpm install --frozen-lockfile` + `registry-url`
- `.github/actions/bump-version-from-tag/` — rewrites `package.json.version = github.ref_name` (GitLab `build-version` equivalent)
- `.github/actions/generate-changelog/` — Conventional Commits → CHANGELOG entry + release-notes body
- `.github/actions/verify-tag-version/` — verify-only opt-out (set `auto-version: false`)
- `.gitleaks.toml` — canonical ruleset (Resend, Neon, PostHog, GitHub fine-grained PATs) plus placeholder allowlist
- `examples/oidc-npm-package/` — OIDC Trusted Publisher consumer
- `examples/token-npm-package/` — `NPM_TOKEN` fallback consumer
- `../MIGRATION_GITLAB_CI_TO_GITHUB_ACTIONS.md` — full per-job mapping, divergence log, wave plan

## Public API contract

- `coroboros/ci/.github/workflows/<name>.yml@v1` resolves the floating major. Consumers pin `@v1` (or `@1.2.3` for immutable).
- **Visibility** — private, Actions access set to *"Accessible from repositories owned by 'coroboros'"*. Caller repos must live in the `coroboros` org; fork-PR mitigations in `../MIGRATION_GITLAB_CI_TO_GITHUB_ACTIONS.md` § Visibility model.
- Each workflow's inputs / secrets / outputs are documented in `README.md`.
- Breaking changes cut a new floating major (`v2`); the `v1` alias stops moving.

## Rules

- **NEVER** break the public API of a tagged major. Add new inputs with defaults; deprecate before removal.
- **NEVER** add a workflow that requires a paid third-party action.
- **NEVER** ship a workflow that depends on undocumented GitHub Actions internals.
- **Step naming** — every new step or job follows the GitLab `<stage>-<focus>` pattern (`stage ∈ {setup, check, build, test, deploy, post-deploy, security, notify}`); stage order `check → build → test → deploy → post-deploy`. Deviations carry a reason in `../MIGRATION_GITLAB_CI_TO_GITHUB_ACTIONS.md` § Divergence log — silent renames and cosmetic drift are out.
- **CI owns the floating-major alias.** `release.yml` re-points `vN` on each `N.x.y` tag push; never push `v1` manually.
- **SHA-pin third-party actions** with a version comment. First-party (`actions/*`, `pnpm/*`) float on major.
- **No runtime deps in this repo.** Workflows install their own tools at run-time (pnpm via `pnpm/action-setup`, gitleaks via curl).
- **Privacy** — no local paths or personal identifiers leak into committed YAML, markdown, or examples.
- **Git** — branch `main`; release flow below. All other rules in `@~/.claude/rules/git-conventions.md` apply.

## Release flow

Manual flow per `@~/.claude/rules/git-conventions.md` and `@~/.claude/rules/changelog.md` — `coroboros/ci` itself is `private: true` and does not run its own `npm-publish.yml`.

Repo-specific divergences:

- On tag push, `release.yml` re-points `v<major>` to the tag SHA (force-push the alias). Prerelease tags (`x.y.z-rc.1`, etc.) skip the alias step.
- Consumers of `npm-publish.yml` skip the manual bump entirely when `auto-version: true` (the default). See `README.md` § Consume.
