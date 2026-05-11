# coroboros/ci

Reusable GitHub Actions workflows + composite actions for the Coroboros stack. Private repo, org-internal access (Actions setting: "Accessible from repositories owned by 'coroboros'"). No npm publish — the workflows themselves are the artifact. The 1.x line covers `@coroboros/*` npm-package CI. Container builds, deploy targets, Node-service CI/CD, and notification routing land in later waves per `../MIGRATION_GITLAB_CI_TO_GITHUB_ACTIONS.md`.

## Canonical rules

Global rules (`~/.claude/rules/*`) inherit automatically — tech-standards, writing, find-docs, git-conventions, privacy, overrides. Divergences below.

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
- `../MIGRATION_GITLAB_CI_TO_GITHUB_ACTIONS.md` — full per-job mapping and divergence log

## Public API contract

- `coroboros/ci/.github/workflows/<name>.yml@v1` resolves the floating major. Consumers pin `@v1` (or `@1.2.3` for immutable).
- **Visibility** — repo is private, with Actions access set to *"Accessible from repositories owned by 'coroboros'"*. Caller repos must be inside the `coroboros` org. Forks outside the org cannot reach the reusable workflows; see README § Fork PR handling.
- Each workflow's inputs / secrets / outputs are documented in `README.md`.
- Breaking changes cut a new floating major (`v2`); the `v1` alias stops moving.

## Workflow authoring conventions

Step and job names follow the 5-year GitLab vocabulary at `~/Desktop/Dev/coroboros/ci-gitlab/`. Pattern: `<stage>-<focus>` where `stage ∈ {setup, check, build, test, deploy, post-deploy, security, notify}`.

Stage order: `check → build → test → deploy → post-deploy`. Tests run AFTER the build because libraries that ship compiled output test against `dist/`.

The migration doc lists every job mapping and every divergence with its reason. Read it before adding a new workflow or renaming a step. Divergences carry a reason in the divergence log; silent renames and cosmetic drift are out.

## Roadmap

- **1.x** — npm-package workflows, composite actions, canonical gitleaks ruleset, auto-version release flow.
- **2.x** — container build / publish (Docker buildx + GHCR / ECR), Node-service CI/CD, `notify.yml` (Slack + Google Chat), JS assets, JS-image (Node + Docker), shared community-health files.
- **3.x** — deploy targets (Cloudflare Workers, AWS Lambda), CDN cache invalidation, S3 / R2 sync, multi-env `environments:` orchestration.

## Rules

- **NEVER** break the public API of a tagged major. Add new inputs with defaults; deprecate before removal.
- **NEVER** add a workflow that requires a paid third-party action.
- **NEVER** ship a workflow that depends on undocumented GitHub Actions internals.
- **CI owns the floating-major alias.** `release.yml` re-points `vN` on each `N.x.y` tag push; never push `v1` manually.
- **SHA-pin third-party actions** with a version comment. First-party (`actions/*`, `pnpm/*`) float on major.
- **No runtime deps in this repo.** Workflows install their own tools at run-time (pnpm via `pnpm/action-setup`, gitleaks via curl).
- **Step naming** — every new step or job follows the GitLab `<stage>-<focus>` pattern. Any deviation carries a documented reason in `../MIGRATION_GITLAB_CI_TO_GITHUB_ACTIONS.md` § Divergence log.
- **Privacy** — no local paths or personal identifiers leak into committed YAML, markdown, or examples.
- **Git** — branch `main`; release flow below. All other rules in `@~/.claude/rules/git-conventions.md` apply.

## Release flow

`coroboros/ci` itself is `private: true` and does not run its own `npm-publish.yml`. Manual flow per Coroboros git-conventions:

1. PR → squash-merge to `main`.
2. Bump `package.json.version` and prepend a `CHANGELOG.md` entry per `@~/.claude/rules/changelog.md`.
3. `git tag x.y.z` on the merge commit (SemVer-strict, no `v` prefix).
4. `git push origin x.y.z` — `release.yml` fires, re-points `v<major>` to the same SHA, force-pushes the alias.
5. `gh release create x.y.z --title "x.y.z" --notes-file <body>`.

Prerelease tags (`x.y.z-rc.1`, etc.) skip the alias step.

Consumers of `npm-publish.yml` do steps 2–5 from CI when `auto-version: true` (the default). See `README.md` § Consume.
