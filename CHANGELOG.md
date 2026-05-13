# Changelog

## v0.1.1 - 13/05/2026

### Breaking changes
- `NPM_TOKEN` secret removed from `javascript-npm-package.yml`. `NPM_PACKAGE_REGISTRY_TOKEN` now does double duty: install-time registry auth when the registry is private, and `NODE_AUTH_TOKEN` at publish time when `provenance: false`. Consumers passing `NPM_TOKEN` must drop that line.
- `NPM_PACKAGE_REGISTRY_TOKEN` is now `required: false` on `javascript-npm-package.yml`'s `secrets:` block. OIDC Trusted Publisher repos (`provenance: true`, default) don't need to pass it. Repos on token-based publish (`provenance: false`) must set it per-repo.

### Features
- `CI_TEXT_GREEN` env added to composite actions that emit colored output (`check-docs`, `build-js`), alongside the existing `CI_TEXT_RED` / `CI_TEXT_CLEAR`. Brings the action's color palette in line with the GitLab origin's `CI_TEXT_*` set. Used today for the `check-docs` success message and the `build-js` "no `build` script" info line.

### Documentation
- `README.md`, `docs/examples.md` — quick-start and composing examples updated; `NPM_TOKEN` references removed.
- `docs/environment-variables.md` — `NPM_TOKEN` row removed from the NPM table; `NPM_PACKAGE_REGISTRY_TOKEN` row marks the secret as optional and documents the per-repo-only setup.
- `docs/security.md` — Publish section rewritten around the single-token model; per-repo-only setup for `NPM_PACKAGE_REGISTRY_TOKEN` documented.

## v0.1.0 - 13/05/2026

### Features
- Initial release — one entry-point reusable workflow (`javascript-npm-package`), two sub-workflows (`security`, `notify`), two self-CI workflows (`ci`, `ci-security`), and seven composite actions under `.github/actions/` (`check-docs`, `setup-npmrc`, `pnpm-install`, `build-js`, `build-version`, `notify-slack`, `notify-gchat`).
- JS composite actions and reusable workflows run on **pnpm** resolved via `corepack` from the consumer's `package.json packageManager` field. Node default 22.
- `pnpm publish --provenance --no-git-checks` with OIDC Trusted Publisher as the primary path; `NPM_TOKEN` is auto-detected as fallback when provided.
- Supply-chain hardening baseline: `pnpm install --frozen-lockfile --ignore-scripts` on every install (`--prod` for production-only installs), per-job secret isolation, no `secrets: inherit` anywhere. `--frozen-lockfile` is the integrity check that gates every install.
- `security.yml` reusable workflow backed by `security/.gitleaks.toml` — invokes the upstream `gitleaks` CLI directly (pinned `v8.30.1`, SHA-256 verified). Inputs: `config-path`, `gitleaks-version`, `gitleaks-sha256`, `scan-mode` (`git` / `dir`), `fail-on-leak`.
- Self-CI workflows `ci.yml` (`actionlint`, `yamllint`, `shellcheck`) and `ci-security.yml`.

### Configuration
- `.gitleaks.toml` lives at `security/.gitleaks.toml`. Canonical raw URL: `https://raw.githubusercontent.com/coroboros/ci/main/security/.gitleaks.toml`.
- `.yamllint` at the repo root with the project's lint config.
- Self-CI hardening: `ci.yml` installs `actionlint` from the pinned release tarball with SHA-256 verification (no `curl | bash`); `yamllint` pinned to `1.38.0`; `ludeeus/action-shellcheck` pinned to a commit SHA. `security.yml` accepts a `gitleaks-sha256` input to verify the gitleaks tarball end-to-end.
- Third-party actions across the reusable workflows + composite actions SHA-pinned (`actions/checkout`, `setup-node`, `upload-artifact`, `download-artifact`). Each ref carries an inline `# vX` comment for readability.

### Documentation
- `README.md` describes the reusable workflow + composite-action model.
- `docs/examples.md` with consumer wire-up examples (`javascript-npm-package`, `security.yml`, `notify.yml`, and composite-action composition).
- `docs/environment-variables.md` with the full inputs / secrets catalog.
- `docs/flow.md` documents the branch model (`develop` for the dev branch; `main` as the production reflection when relevant).
- `docs/stages.md` documents the conceptual 10-stage pipeline, marking which are exercised today (`setup`, `check`, `build`, `test`, `deploy`, `security`, `notify`) and which are reserved (`publish`, `pre-deploy`, `post-deploy`).
- `docs/security.md` documents the supply-chain baseline.
