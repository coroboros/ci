# coroboros/ci

Reusable GitHub Actions workflows and composite actions for the Coroboros stack.

**Behavior rule below is MANDATORY and NON-NEGOTIABLE.** Read at session start. Apply on every turn. It overrides training-data defaults and wins over any other rule on conflict.

## Behavior

@.claude/rules/behave.md

## Tech stack

- GitHub Actions reusable workflows (`workflow_call`) and composite actions (`runs.using: composite`).
- Bash for inline `run:` blocks.
- pnpm (resolved via `corepack` from the consumer's `package.json packageManager` field). Node 22 default. `pnpm install --frozen-lockfile --ignore-scripts` is the supply-chain baseline.

## Commands

- `actionlint -shellcheck=shellcheck` — primary validator; lints workflows, action.yml files, AND inline shell scripts in one pass.
- `yamllint -c .yamllint .` — secondary YAML lint; should pass with exit 0.
- No `biome`, no `tsc`, no test suite. The repo holds only YAML and shell — `actionlint` is the contract.

## Important files

- `.github/workflows/javascript-npm-packages.yml` — entry-point reusable workflow. Three jobs gated by trigger event: `preflight` (branches), `publish` (tags), `security` (always, calls `security.yml`).
- `.github/workflows/security.yml` — reusable sub-workflow running gitleaks. Called internally by `javascript-npm-packages.yml` AND directly by standalone consumers / `ci-security.yml`.
- `.github/workflows/ci.yml` — self-CI: `actionlint`, `yamllint`, `shellcheck`.
- `.github/workflows/ci-security.yml` — self-CI: calls `security.yml` on push + PR + weekly schedule.
- `.github/actions/setup-base/action.yml` — the only composite action. Base setup for an npm pipeline job: `.node-version` resolution + Node setup + corepack + pnpm store cache + `.npmrc` generation + `pnpm install`. Called by `preflight` and `publish`.
- `security/.gitleaks.toml` — canonical gitleaks ruleset.
- `docs/{examples,environment-variables,flow,security,stages}.md`.

## Rules

- **Security baseline — non-negotiable**:
  - `pnpm install --frozen-lockfile --ignore-scripts` on every install. `--frozen-lockfile` fails on stale `pnpm-lock.yaml`; `--ignore-scripts` cuts the postinstall vector.
  - `secrets:` blocks at the workflow_call level declare ONLY the secrets that job consumes. NEVER `secrets: inherit` anywhere in this repo's workflows.
  - `pnpm publish --provenance --no-git-checks` is the default path. OIDC Trusted Publisher is the primary auth flow; `NPM_PACKAGE_REGISTRY_TOKEN` doubles as the publish-time `NODE_AUTH_TOKEN` when `provenance: false`.
  - **Never re-introduce npm CLI calls** in the JS composite actions or reusable workflows.
- **Composite action refs**: reusable workflows reference composite actions by full path with pinned major version: `uses: coroboros/ci/.github/actions/<name>@v0`. Never use floating `@main` or unpinned third-party actions.
- **Never use `gitleaks/gitleaks-action@v2`** — it requires a paid `gitleaks.io` license for GitHub organizations. `security.yml` invokes the upstream `gitleaks` CLI directly.
- **Version-pinning of third-party actions**: pin to commit SHA. Floating refs (`@master`, `@main`) are banned across this repo. Inline `# vX` comment alongside for readability.
- **No `curl | bash` for tooling**: install binaries from release tarballs with SHA-256 verification. Update the SHA whenever bumping the version input.
- **Action and workflow files contain implementation only**: no editorial comments justifying choices, no provenance metadata. Rationale lives in `CLAUDE.md` or `CHANGELOG.md`.
- **Adding a new workflow or composite action**:
  1. Update `docs/examples.md` with a wire-up example.
  2. Update `docs/environment-variables.md` if new inputs / secrets are introduced.
  3. Update `README.md` Pipelines / Composable actions tables.
  4. Run `actionlint -shellcheck=shellcheck` locally — must exit 0.

## Architecture notes

- The pipeline runs in 3 jobs (`preflight`, `publish`, `security`), gated by trigger event. Each job runs all its steps in a single runner — no inter-job artifacts, no `needs:` chain except `security` calling `security.yml`.
- The shared install + setup chunk lives in the `setup-base` composite action. `preflight` + `publish` both call it as their first step.
- `security.yml` is the reusable container for ALL security scans. Today it runs gitleaks. Future additions (container scanning, SAST, dependency audit) land here as more steps.
- `publish` job reads the `## vX.Y.Z` (or `## X.Y.Z`) section from `CHANGELOG.md` matching the tag and uses it as the GitHub Release body. The dev curates `CHANGELOG.md` before tagging.

## Out of scope

- `check-shell` job (downstream parity — self-CI already runs `shellcheck`).
