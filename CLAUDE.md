# coroboros/ci

Reusable GitHub Actions workflows and composite actions for the Coroboros stack.

## Tech stack

- GitHub Actions reusable workflows (`workflow_call`) and composite actions (`runs.using: composite`).
- Bash for inline `run:` blocks; `sh` only inside the Kaniko container job (`publish-image`).
- Kaniko (`gcr.io/kaniko-project/executor:debug`) for image builds.
- pnpm (resolved via `corepack` from the consumer's `package.json packageManager` field). Node 22 default. `pnpm install --frozen-lockfile --ignore-scripts` is the supply-chain baseline.

## Commands

- `actionlint -shellcheck=shellcheck` — primary validator; lints workflows, action.yml files, AND inline shell scripts in one pass.
- `yamllint -c .yamllint .` — secondary YAML lint; should pass with exit 0.
- No `biome`, no `tsc`, no test suite. The repo holds only YAML and shell — `actionlint` is the contract.

## Important files

- `.github/workflows/*.yml` — six entry-point reusable workflows (`javascript-npm-package`, `javascript-image`, `javascript-assets`, `javascript-function`, `container-image`, `node-service`), two sub-workflows (`security`, `notify`), two self-CI (`ci`, `ci-security`).
- `.github/actions/*/action.yml` — seventeen composite actions, one per pipeline step.
- `security/.gitleaks.toml` — canonical gitleaks ruleset.
- `docs/usage.md`, `docs/environment-variables.md`, `docs/flow.md`, `docs/stages.md`, `docs/security.md`.

## Rules

- **Kaniko stays Kaniko**: `publish-image` runs in `gcr.io/kaniko-project/executor:debug`. Do NOT swap for `docker/build-push-action`.
- **Security baseline — non-negotiable**:
  - `pnpm install --frozen-lockfile --ignore-scripts` on every install. `--frozen-lockfile` fails on stale `pnpm-lock.yaml`; `--ignore-scripts` cuts the postinstall vector.
  - `--prod` flag added for production-only installs (e.g. function packaging, publish-time install).
  - `secrets:` blocks at the workflow_call level declare ONLY the secrets that job consumes. NEVER `secrets: inherit` anywhere in this repo's workflows.
  - `pnpm publish --provenance --no-git-checks` is the default path; `NPM_TOKEN` is opt-in via the secret being passed. OIDC Trusted Publisher is the primary auth flow.
  - **Never re-introduce npm CLI calls** in the JS composite actions or reusable workflows.
- **Composite action refs**: reusable workflows reference composite actions by full path with pinned major version: `uses: coroboros/ci/.github/actions/<name>@v0`. Never use floating `@main` or unpinned third-party actions.
- **Never use `gitleaks/gitleaks-action@v2`** — it requires a paid `gitleaks.io` license for GitHub organizations. `security.yml` invokes the upstream `gitleaks` CLI directly.
- **Version-pinning of third-party actions**: pin to commit SHA. Floating refs (`@master`, `@main`) are banned across this repo (self-CI + consumer-facing reusable workflows). Inline `# vX` comment alongside for readability.
- **No `curl | bash` for tooling**: install binaries from release tarballs with SHA-256 verification (see `ci.yml` for `actionlint` and `security.yml` for `gitleaks`). Update the SHA whenever bumping the version input.
- **Action and workflow files contain implementation only**: no editorial comments justifying choices, no provenance metadata. Rationale lives in `CLAUDE.md` or `CHANGELOG.md`.
- **Adding a new workflow or composite action**:
  1. Update `docs/usage.md` with a wire-up example.
  2. Update `docs/environment-variables.md` if new inputs / secrets are introduced.
  3. Update `README.md` pipeline / action tables.
  4. Run `actionlint -shellcheck=shellcheck` locally — must exit 0.

## Architecture notes

- `security.yml` is the container for all security scans. Today it runs gitleaks (`check-security`, early fail-fast on real leaks). Future additions (container scanning, SAST, dependency audit) land in the same file at their appropriate stage and produce reports rather than block. Consumers call it as a separate job alongside the main pipeline.
- Pipeline stage ordering: `setup → check → build → publish → test → pre-deploy → deploy → post-deploy → security → notify`. New jobs land in the matching stage.

## Out of scope

- Karate / Postman API tests.
- `check-shell` job (downstream parity — self-CI already runs `shellcheck`).
- Downstream test fixture repos.
