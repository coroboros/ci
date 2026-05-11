# coroboros/ci

Reusable GitHub Actions workflows + composite actions. Public repo, open to any consumer. No npm publish — workflows-only artifact. The 1.0.0 wave covers npm packages; container builds, deploy targets, Node-service CI/CD, and notification routing land in later waves.

## Canonical rules

Global rules (`~/.claude/rules/*`) inherit automatically — tech-standards, writing, find-docs, git-conventions, privacy, overrides. Divergences below.

## Tech Stack

- GitHub Actions (composite + `workflow_call`).
- YAML only. No application code, no runtime deps.
- Node.js 22 LTS (consumer-side, baked into composite default).

## Commands

- `brew install actionlint` then `actionlint -color` — lint workflows + composite actions.

## Important Files

- `.github/workflows/npm-ci.yml` — matrix verify
- `.github/workflows/npm-publish.yml` — OIDC + token publish
- `.github/workflows/commits-lint.yml` — PR commit-range lint
- `.github/workflows/secrets-scan.yml` — gitleaks
- `.github/workflows/ci.yml` — this repo's own CI (actionlint + composite smoke)
- `.github/workflows/release.yml` — this repo's release (alias-tag pusher)
- `.github/actions/setup-pnpm-node/action.yml` — pnpm + node + frozen install
- `.github/actions/verify-tag-version/action.yml` — tag vs package.json guard
- `.gitleaks.toml` — canonical secret-scan ruleset (Resend, Neon, PostHog, GitHub fine-grained PATs)
- `examples/oidc-npm-package/` — OIDC consumer example
- `examples/token-npm-package/` — NPM_TOKEN fallback example

## Public API contract

- `coroboros/ci/.github/workflows/<name>.yml@v1` resolves the **floating major** tag. Consumers use `@v1` (or `@1.2.3` for immutable pin).
- Inputs / secrets / outputs documented in `README.md` per workflow.
- Breaking changes cut a new floating major (`v2`). The `v1` alias stops moving.

## Roadmap

The repo is org-wide CI infrastructure, not an npm-package-only repo.

- **1.x** — npm package workflows, composite actions, canonical gitleaks ruleset.
- **Later waves**: container build/publish, deploy targets (Cloudflare Workers, AWS Lambda), Node-service CI/CD, notification routing (Slack + Google Chat), shared `CODE_OF_CONDUCT.md` / `CONTRIBUTING.md` / `SECURITY.md` / `SUPPORT.md` templates.

## Rules

- **NEVER** break the public API of a tagged major. Add new inputs with defaults; deprecate before removal.
- **NEVER** add a workflow that requires a paid third-party action.
- **NEVER** ship a workflow that depends on undocumented GitHub Actions internals.
- **CI owns the floating-major alias.** `release.yml` re-points `vN` on each `N.x.y` tag push; never push `v1` manually.
- **SHA-pin third-party actions** with a version comment. First-party (`actions/*`, `pnpm/*`) float on major.
- **No runtime deps in this repo.** Workflows install their own tools at run-time (pnpm via `pnpm/action-setup`, gitleaks via curl).
- **Privacy** — no local paths or personal identifiers leak into committed YAML, markdown, or examples.
- **Git** — branch `main`; release flow per `@~/.claude/rules/git-conventions.md`. All other rules in `@~/.claude/rules/git-conventions.md` apply.

## Release flow

1. Land changes on `main` via PR (squash-merge).
2. Update `CHANGELOG.md` with the new version entry.
3. `git tag x.y.z` on the merge commit (no `v` prefix per Coroboros git-conventions).
4. `git push origin x.y.z`.
5. `release.yml` fires on the tag push, re-points `vN` alias to the same SHA, pushes it.
6. `gh release create x.y.z --title "x.y.z" --notes-from-tag` — GitHub release.

Prerelease tags (`x.y.z-rc.1`, etc.) skip the alias step.
