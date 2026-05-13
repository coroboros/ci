# Changelog

## v0.1.1 - 13/05/2026

### Features
- `setup-base` composite action — the pipeline's single source of defaults. Resolves Node.js version (`.node-version` file → `node-version` input → fail), release-branch pattern, release-source commit pattern, and `npm-extra-config` (caller-repo `vars.*` → hardcoded default). The workflow runs `setup-base` once in a `base` job, exposes everything as job outputs; downstream jobs inherit via `needs.base.outputs.*`; downstream actions inherit via the workflow's `with:` plumbing.
- `CI_TEXT_GREEN` env in composite actions that emit colored output (`check-docs`, `build-js`, `setup-base`), alongside `CI_TEXT_RED` and `CI_TEXT_CLEAR`. Success / info messages paint green; failures paint red.

### Configuration
- `javascript-npm-packages.yml` (workflow filename) — plural, matching the GitLab origin's `templates/javascript/npm-packages/` folder.
- The workflow's `inputs:` block declares only `node-version` (fallback for `setup-base`) and `provenance` (publish behavior toggle). Env-var-style settings (`RELEASE_BRANCH_PATTERN`, `RELEASE_SOURCE_BRANCH_COMMIT_PATTERN`, `NPM_EXTRA_CONFIG`) flow through the caller's `vars` context — set them at the org / repo / environment level and `setup-base` picks them up. Defaults live in `setup-base`.
- `node-version` on composite actions (`pnpm-install`, `build-js`, `build-version`) is `required: true` with no hardcoded default. The workflow's `base` job is the single source of truth.
- `NPM_PACKAGE_REGISTRY_TOKEN` is `required: false` on `javascript-npm-packages.yml`'s `secrets:` block. OIDC Trusted Publisher repos (`provenance: true`, default) don't pass it. Repos on token-based publish (`provenance: false`) set it per-repo.
- `NPM_PACKAGE_REGISTRY_TOKEN` does double duty: install-time registry auth when the registry is private, and `NODE_AUTH_TOKEN` at publish time when `provenance: false`.

### Documentation
- `README.md` — Pipelines table references `javascript-npm-packages.yml`; Composable actions table adds the `setup-base` row at the top.
- `docs/examples.md` — quick-start references `javascript-npm-packages.yml`; composing example threads the resolved base configuration through `setup-npmrc`, `build-js`, `build-version` via `setup-base` outputs.
- `docs/environment-variables.md` — Common section keeps only `node-version` (the only declared input besides `provenance`); env-var-style settings live under `vars` context.
- `docs/security.md` — Publish section describes the single-token model and the per-repo-only setup for `NPM_PACKAGE_REGISTRY_TOKEN`.
- `CLAUDE.md` — file inventory updated for the rename and the eight composite actions (with `setup-base` as the base step).

## v0.1.0 - 13/05/2026

### Features
- Initial release — one entry-point reusable workflow (`javascript-npm-package`), two sub-workflows (`security`, `notify`), two self-CI workflows (`ci`, `ci-security`), and seven composite actions under `.github/actions/` (`check-docs`, `setup-npmrc`, `pnpm-install`, `build-js`, `build-version`, `notify-slack`, `notify-gchat`).
- JS composite actions and reusable workflows run on **pnpm** resolved via `corepack` from the consumer's `package.json packageManager` field. Node default 22.
- `pnpm publish --provenance --no-git-checks` with OIDC Trusted Publisher as the primary path; `NPM_PACKAGE_REGISTRY_TOKEN` doubles as `NODE_AUTH_TOKEN` at publish time when `provenance: false`.
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
