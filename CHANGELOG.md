# Changelog

## v0.1.1 - 13/05/2026

### Features
- `resolve-node-version` composite action. Reads `.node-version` from the consumer repo if present, falls back to the `node-version` input, fails the job if neither is set. The workflow runs it once in `check-docs` and exposes the resolved version as a job output; downstream Node-using jobs consume `needs.check-docs.outputs.node-version`.
- `CI_TEXT_GREEN` env in composite actions that emit colored output (`check-docs`, `build-js`, `resolve-node-version`), alongside `CI_TEXT_RED` and `CI_TEXT_CLEAR`. `check-docs` emits a green `README.md present` line on success; `build-js` paints the `Non required script 'build' skipped` info line green; `resolve-node-version` logs the resolved version + source in green.

### Configuration
- `node-version` on composite actions (`pnpm-install`, `build-js`, `build-version`) is `required: true` with no hardcoded default. The workflow is the single source of truth — `inputs.node-version` (default `"22"`) flows into `resolve-node-version` in `check-docs` and propagates from there.
- `NPM_PACKAGE_REGISTRY_TOKEN` is `required: false` on `javascript-npm-package.yml`'s `secrets:` block. OIDC Trusted Publisher repos (`provenance: true`, default) don't need to pass it. Repos on token-based publish (`provenance: false`) set it per-repo.
- `NPM_PACKAGE_REGISTRY_TOKEN` does double duty: install-time registry auth when the registry is private, and `NODE_AUTH_TOKEN` at publish time when `provenance: false`.

### Documentation
- `README.md` Composable actions table — adds the `resolve-node-version` row.
- `docs/examples.md` — composing example threads the resolved Node.js version through `build-js` and `build-version` via `resolve-node-version` outputs.
- `docs/environment-variables.md` — `node-version` row documents the file-then-input-then-fail resolution; `NPM_PACKAGE_REGISTRY_TOKEN` row marks the secret optional and documents the per-repo-only setup.
- `docs/security.md` — Publish section describes the single-token model and the per-repo-only setup.

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
