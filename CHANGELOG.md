# Changelog

## v0.1.0 - 13/05/2026

### Features
- One reusable entry-point workflow (`javascript-npm-packages.yml`) with three jobs gated by trigger event:
  - **`preflight`** (on branches) — `javascript/base` + `pnpm run lint` + `pnpm run build` (if `scripts.build` exists) + `pnpm test`.
  - **`publish`** (on tags) — preflight chain + pin `package.json` to tag + `pnpm publish` + GitHub Release with the matching `CHANGELOG.md` section as body + Slack / Google Chat notifications (inline, skipped when webhook secrets are empty).
  - **`security`** (always) — calls `security.yml` as a sub-workflow.
- One composite action (`javascript/base`) holds the shared preamble: `.node-version` resolution + `actions/setup-node` + corepack + pnpm store cache + `.npmrc` generation (from `NPM_CONFIG_FILE` secret + `vars.NPM_EXTRA_CONFIG`) + README presence check + `pnpm install --frozen-lockfile --ignore-scripts`. Called by `preflight` and `publish`.
- `security.yml` reusable sub-workflow runs gitleaks against the calling repo's tree. Pinned `v8.30.1` with SHA-256 verification. Callable internally (`javascript-npm-packages.yml#security` job) and standalone (consumers wanting only the security scan).
- Self-CI workflows: `ci.yml` (`actionlint`, `yamllint`, `shellcheck`) and `ci-security.yml` (calls `security.yml` on push + PR + weekly schedule).

### Configuration
- pnpm via corepack (resolved from the consumer's `package.json` `packageManager` field). Node version resolved from the consumer's `.node-version` file; falls back to `DEFAULT_NODE_VERSION` (`22`) hardcoded in `javascript/base`.
- `NPM_PACKAGE_REGISTRY_TOKEN` is the single npm token: install-time registry auth when the registry is private, publish-time `NODE_AUTH_TOKEN` when `provenance: false`. Set per-repo only when needed.
- Env-var-style settings (`NPM_EXTRA_CONFIG`) cascade via the caller's `vars` context.
- Workflow input: `provenance` (publish behavior toggle, default `true`).
- Workflow secrets: `NPM_CONFIG_FILE` (required), `NPM_PACKAGE_REGISTRY` (required), `NPM_PACKAGE_PROXY_REGISTRY` (required), `NPM_PACKAGE_REGISTRY_TOKEN` (optional), `SLACK_WEBHOOK_URL` (optional), `GOOGLE_CHAT_WEBHOOK_URL` (optional).
- `publish` job declares `permissions: contents: write` (for GitHub Release creation) and `id-token: write` (for npm OIDC). Consumer grants both at the caller-job level.
- `.gitleaks.toml` lives at `security/.gitleaks.toml`. Canonical raw URL fallback for cross-repo use.
- Log severity via GitHub workflow commands (`::error::`, `::warning::`, `::notice::`); step status checkmark conveys success natively.
- Third-party actions SHA-pinned (`actions/checkout`, `setup-node`, `cache`, `upload-artifact`, `download-artifact`, `ludeeus/action-shellcheck`). `actionlint`, `gitleaks`, `yamllint` installed from pinned release tarballs with SHA-256 verification.

### Documentation
- `README.md` describes the 3-job model + Quick start + `javascript/base` composable.
- `docs/examples.md` — consumer wire-up for `javascript-npm-packages.yml` + standalone `security.yml` + composing with `javascript/base`.
- `docs/environment-variables.md` — workflow inputs, secrets, and the `vars` context cascade.
- `docs/flow.md` — branch model and trigger semantics.
- `docs/stages.md` — the 3-job pipeline + per-job step sequence.
- `docs/security.md` — supply-chain baseline + gitleaks model.
