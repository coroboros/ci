# Changelog

## v0.2.0 - 13/05/2026

### Breaking changes
- Public surface trimmed to the npm-package pipeline only. Five reusable workflows removed: `javascript-image`, `javascript-assets`, `javascript-function`, `container-image`, `node-service`. Ten composite actions removed: `build-image-name`, `publish-image`, `build-function`, `deploy-function`, `invoke-function`, `deploy-assets`, `cdn-invalidate`, `deploy-release`, `aws-credentials`, `check-docs-api`. Consumers must vendor the prior `0.1.4` artefacts or migrate. Consumers pinning `@v0` and using only `javascript-npm-package.yml` are unaffected.
- Composite action `check-readme` renamed to `check-docs` for naming parity with the GitLab origin. Behavior unchanged — still asserts only `README.md` presence.

### Configuration
- Default branch flipped from `master` to `main`. `release-source-commit-pattern` default updated to `^Merge branch 'release[/]...' into 'main'` across `javascript-npm-package.yml`, `notify.yml`, `build-version`, `notify-slack`, `notify-gchat`. Consumers on a `master` production branch must pass the previous default explicitly to keep matching. Extraction logic and pattern inputs are unchanged — only the default value flips.

### Documentation
- `README.md` Pipelines and Composable actions tables trimmed to the new surface (3 + 7 rows); quick-start `on: push: branches:` updated to `[develop, main]`.
- `CLAUDE.md` file inventory, Tech stack, Rules, and Architecture notes updated; Kaniko / `publish-image` references removed; Karate and downstream-test-fixture bullets dropped from Out-of-scope.
- `docs/examples.md` — five non-npm pipeline sections removed; composing example updated to reference `check-docs`; consumer triggers updated to `[develop, main]`.
- `docs/environment-variables.md` — AWS, Container images, Assets, Lambda functions, Node services sections removed; Common trimmed (`dev-branch` / `prod-branch` dropped); NPM heading renamed to `## NPM — javascript-npm-package`; `release-source-commit-pattern` default cell updated for `main`.
- `docs/security.md` — AWS OIDC section removed.
- `docs/flow.md` — multi-environment software subsection removed (tied to dropped pipelines); `master` references swapped for `main`; `develop` kept as the development branch.
- `docs/stages.md` rewritten — ten-stage model preserved with pipeline-agnostic descriptions; stages exercised by `javascript-npm-package` annotated, the others marked reserved.

## v0.1.4 - 12/05/2026

### Documentation
- README: dropped the inline descriptions under `## Usage` subsections — link only.

## v0.1.3 - 12/05/2026

### Documentation
- README restructured — `## Development` replaced by `## Usage` (with `### Stages`, `### Flow`, `### Environment Variables`, `### Examples` subsections); `## Security` reduced to a single link.
- Renamed `docs/usage.md` → `docs/examples.md`. Cross-references updated.
- `docs/security.md` now opens with the pnpm-only constraint.

## v0.1.2 - 12/05/2026

### Documentation
- README badge row aligned with the Coroboros standard set — added `latest` (dynamic release link), `ci` (workflow status), `branch`, `stars`, `skills`. Dropped the static `latest-v0` badge in favour of the dynamic release shield.

## v0.1.1 - 12/05/2026

### Configuration
- Added `.claude/rules/behave.md` and imported it from `CLAUDE.md` to surface the behavioral baseline at every session start.

## v0.1.0 - 12/05/2026

### Features
- Initial release — six entry-point reusable workflows (`javascript-npm-package`, `javascript-image`, `javascript-assets`, `javascript-function`, `container-image`, `node-service`), two sub-workflows (`security`, `notify`), and seventeen composite actions under `.github/actions/`.
- JS composite actions and reusable workflows run on **pnpm** (resolved via `corepack` from the consumer's `package.json packageManager` field). Node default 22.
- Added `pnpm publish --provenance --no-git-checks` with OIDC Trusted Publisher as the primary path; `NPM_TOKEN` auto-detected as fallback when provided.
- Supply-chain hardening baseline: `pnpm install --frozen-lockfile --ignore-scripts` on every install (`--prod` for production-only installs), per-job secret isolation, no `secrets: inherit` anywhere. `--frozen-lockfile` is the integrity check that gates every install.
- Added `security.yml` reusable workflow backed by `security/.gitleaks.toml` — invokes the upstream `gitleaks` CLI directly (pinned `v8.30.1`) instead of `gitleaks/gitleaks-action@v2`, which is paid for GitHub organizations. Inputs: `config-path`, `gitleaks-version`, `scan-mode` (`git` / `dir`), `fail-on-leak`.
- Added self-CI workflows `ci.yml` (`actionlint`, `yamllint`, `shellcheck`) and `ci-security.yml`.

### Configuration
- `.gitleaks.toml` lives at `security/.gitleaks.toml`. Canonical raw URL: `https://raw.githubusercontent.com/coroboros/ci/main/security/.gitleaks.toml`.
- Added `.yamllint`.
- Self-CI hardening: `ci.yml` installs `actionlint` from the pinned release tarball with SHA-256 verification (no `curl | bash`); `yamllint` pinned to `1.38.0`; `ludeeus/action-shellcheck` pinned to commit SHA `00cae500b08a931fb5698e11e79bfbd38e612a38` (v2.0.0). `security.yml` accepts a `gitleaks-sha256` input to verify the gitleaks tarball end-to-end.
- Third-party actions across the reusable workflows + composite actions SHA-pinned: `actions/checkout`, `setup-node`, `upload-artifact`, `download-artifact`, `cache`, `aws-actions/configure-aws-credentials`. Each ref carries an inline `# v4` comment.
- `ghcr.io` documented as the default container registry — no static `IMAGE_REGISTRY_PASSWORD`, pass `github.actor` + `secrets.GITHUB_TOKEN` with `permissions: packages: write`.
- AWS OIDC — `aws-credentials` composite action assumes an IAM role via `aws-actions/configure-aws-credentials` when `aws-role-dev` / `aws-role-prod` ARNs are provided. Static `AWS_ACCESS_KEY_ID_*` / `AWS_SECRET_ACCESS_KEY_*` remain as fallback. `javascript-assets.yml` and `javascript-function.yml` expose the role ARNs as inputs; deploy / invoke jobs declare `permissions: id-token: write` for the OIDC handshake.

### Documentation
- Added `docs/usage.md` with consumer wire-up examples per workflow.
- Added `docs/environment-variables.md` with the full secrets / inputs catalog (organized by scope).
- Added `docs/flow.md` (branch model, trigger semantics) and `docs/stages.md` (ten-stage conceptual pipeline).
- Added `docs/security.md` documenting the supply-chain baseline.
- Wrote `README.md` around the composable workflow + composite-action model.
