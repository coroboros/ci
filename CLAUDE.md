# coroboros/ci

Reusable GitHub Actions workflows + composite actions for `@coroboros/*` repos. Private. Full GitLab→GHA mapping in `../MIGRATION_GITLAB_CI_TO_GITHUB_ACTIONS.md`.

## Canonical rules

Global rules (`~/.claude/rules/*`) inherit automatically — tech-standards, writing, find-docs, git-conventions, privacy, overrides, changelog. Divergences below.

## Tech Stack

- GitHub Actions (composite actions + `workflow_call` reusable workflows).
- YAML only. No application code, no runtime deps.
- Node.js 22 LTS (consumer-side, default in `setup-pnpm-node`).

## Commands

- `actionlint -color` — lint workflows + composite actions. Install: `brew install actionlint`. Pinned in CI to v1.7.12.

## Architecture

Two layers, each independently importable:

1. **Composite actions** (`.github/actions/<name>`) — the atomic, reusable unit. One step = one composite. Any workflow (current or future: node-service, javascript-image, container-image, etc.) imports the steps it needs via `uses: coroboros/ci/.github/actions/<name>@v1`.
2. **Reusable workflows** (`.github/workflows/<name>.yml` with `workflow_call`) — opinionated stage compositions for full pipelines (npm-package CI, npm-package release, commit-message lint, secrets scan). Consumers call them via `uses: coroboros/ci/.github/workflows/<name>.yml@v1`.

Composites stay small and orthogonal. Workflows compose them and add stage banners + matrix logic.

## Important Files

### Reusable workflows (`workflow_call`)

- `.github/workflows/npm-ci.yml` — matrix verify (`check-docs` → `check-npm-lint` → `check-npm-typecheck` → `build-js` → `test-npm-unit`) + PR `pack-check`
- `.github/workflows/npm-publish.yml` — tag-triggered release (`check` → `build` → `build-version` → `build-changelog` → `test` → `deploy-npm-package` → `post-deploy-commit-back` → `post-deploy-github-release`)
- `.github/workflows/commits-lint.yml` — PR commit-range Conventional Commits lint
- `.github/workflows/secrets-scan.yml` — gitleaks against canonical `.gitleaks.toml`

### Composite actions (per-step, importable)

| Composite | GitLab analogue | Purpose |
|---|---|---|
| `setup-pnpm-node` | `setup-npmrc` + image | pnpm + Node + cache + registry-url |
| `check-docs` | `check-docs` | Require README.md (and optional `docs/` dir) |
| `check-npm-lint` | `check-npm-lint` | Run lint command |
| `check-npm-typecheck` | (added — TS-strict) | Run typecheck command |
| `build-js` | `build-js` | Run build command with GitLab-faithful skip-if-missing |
| `bump-version-from-tag` | `build-version` | Rewrite `package.json.version = github.ref_name` |
| `verify-tag-version` | (auto-version: false path) | Assert tag matches `package.json.version` |
| `generate-changelog` | (added) | Conventional Commits → CHANGELOG entry + release-notes body |
| `test-npm-unit` | `test-npm-unit` | Run test command |
| `pack-check` | (added) | `pnpm publish --dry-run` on PRs |
| `deploy-npm-package` | `deploy-package` | 4-mode publish (pnpm\|npm × oidc\|token) |
| `post-deploy-commit-back` | (added) | Bot commit + push of release artifacts |
| `post-deploy-github-release` | (added) | `gh release create` with rendered notes |

### Internal CI (this repo)

- `.github/workflows/ci.yml` — actionlint + composite smoke (`check-tool-versions`)
- `.github/workflows/release.yml` — floating-major alias-tag pusher (`deploy-floating-major-alias`)

### Config + examples

- `.gitleaks.toml` — canonical ruleset (Resend, Neon, PostHog, GitHub fine-grained PATs) plus placeholder allowlist
- `examples/oidc-npm-package/` — OIDC Trusted Publisher consumer
- `examples/token-npm-package/` — `NPM_TOKEN` fallback consumer
- `../MIGRATION_GITLAB_CI_TO_GITHUB_ACTIONS.md` — per-job map, per-composite map, divergence log, wave plan

## Public API contract

- `coroboros/ci/.github/workflows/<name>.yml@v1` and `coroboros/ci/.github/actions/<name>@v1` resolve the floating major. Consumers pin `@v1` (or `@1.2.3` for immutable).
- **Visibility** — private, Actions access set to *"Accessible from repositories owned by 'coroboros'"*. Caller repos must live in the `coroboros` org; fork-PR mitigations in `../MIGRATION_GITLAB_CI_TO_GITHUB_ACTIONS.md` § Visibility model.
- Each composite + workflow documents its inputs / secrets / outputs at the top of its YAML. README.md summarizes.
- Breaking changes cut a new floating major (`v2`); the `v1` alias stops moving.

## Rules

- **NEVER** break the public API of a tagged major. Add new inputs with defaults; deprecate before removal. New composites and new optional inputs are additive (minor bump).
- **NEVER** add a workflow that requires a paid third-party action.
- **NEVER** ship a workflow that depends on undocumented GitHub Actions internals.
- **Step naming** — every step and every job carries an explicit `name:` field that follows the GitLab `<stage>-<focus>` pattern (`stage ∈ {setup, check, build, test, deploy, post-deploy, security, notify}`); stage order `check → build → test → deploy → post-deploy`. Implicit `uses:`-only steps without a `name:` are allowed only for `actions/checkout` and `setup-pnpm-node` (pure pre-stage setup). Deviations carry a reason in `../MIGRATION_GITLAB_CI_TO_GITHUB_ACTIONS.md` § Divergence log — silent renames and cosmetic drift are out.
- **GitLab vocabulary is canon.** When porting a GitLab job, the GHA composite/step keeps the same name unless the divergence log carries a reason. Five years of consumer muscle memory beats GHA aesthetics.
- **Per-step composites.** New reusable steps land as composite actions under `.github/actions/<name>/action.yml` so any future workflow (node-service, javascript-image, etc.) imports them. Inline bash inside a workflow is reserved for non-reusable glue (matrix definition, stage banners, conditionals).
- **CI owns the floating-major alias.** `release.yml` re-points `vN` on each `N.x.y` tag push; never push `v1` manually.
- **Pin third-party** — SHA-pin third-party actions with a version comment. First-party (`actions/*`, `pnpm/*`) float on major. Tools fetched via curl pin to a tagged release (e.g. `actionlint v1.7.12`), never to `main`.
- **No runtime deps in this repo.** Workflows install their own tools at run-time (pnpm via `pnpm/action-setup`, gitleaks via curl).
- **Privacy** — no local paths or personal identifiers leak into committed YAML, markdown, or examples.
- **Git** — branch `main`; release flow below. All other rules in `@~/.claude/rules/git-conventions.md` apply.

## Release flow

Manual flow per `@~/.claude/rules/git-conventions.md` and `@~/.claude/rules/changelog.md` — `coroboros/ci` itself is `private: true` and does not run its own `npm-publish.yml`.

Repo-specific divergences:

- On tag push, `release.yml` re-points `v<major>` to the tag SHA (force-push the alias). Prerelease tags (`x.y.z-rc.1`, etc.) skip the alias step.
- Consumers of `npm-publish.yml` skip the manual bump entirely when `auto-version: true` (the default). See `README.md` § Consume.
