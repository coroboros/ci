# coroboros/ci

Reusable GitHub Actions workflows and composite actions for the Coroboros stack.

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
- `.github/workflows/security.yml` — reusable sub-workflow running gitleaks. Called internally by `javascript-npm-packages.yml` AND directly by standalone consumers / `self-security.yml`. Requires `security/.gitleaks.toml` at the calling repo root — fails fast if missing.
- `.github/workflows/self.yml` — self-CI: `actionlint`, `yamllint`, `shellcheck`.
- `.github/workflows/self-security.yml` — self-CI: calls `security.yml` on push + PR.
- `.github/actions/check-docs/action.yml` — transverse composite: run context dump + `README.md` presence check. Called first by `preflight` and `publish`.
- `.github/actions/javascript/base/action.yml` — JS-specific composite: `.node-version` resolution (required; fail if missing) + Node setup + corepack + pnpm store cache + `.npmrc` generation + `pnpm install` + `pnpm run lint` + `pnpm run build` (conditional) + `pnpm test`. Called by `preflight` and `publish`.
- `.github/actions/release/generate-changelog/action.yml` — transverse composite: tag format validation (fails on `v` prefix) + Conventional Commits parsed since previous tag into `## vX.Y.Z - DD/MM/YYYY` section in `CHANGELOG.md`, with `Others` bucket for non-standard types. Outputs `body` for release notes. Idempotent. Called by `publish`.
- `.github/actions/release/github-release/action.yml` — transverse composite: creates the GitHub Release for the current tag with the provided `body`. Called by `publish`.
- `security/.gitleaks.toml` — canonical gitleaks ruleset.
- `docs/{examples,environment-variables,flow,security,stages}.md`.

## Rules

- **Internal CI = imposed, not proposed.** Reusable workflows accept zero `inputs:` / `secrets:` unless the consumer has a legitimate reason to vary the value. `workflow_call:` stays for reusability; configurability gets stripped when one value fits everyone.
- **House style**:
  - Env values quoted: `KEY: "value"`. Never bare strings.
  - No dead env vars — declare a key only where a step in the same file consumes it.
  - Log severity via GH workflow commands (`echo "::error::..."`, `::warning::`, `::notice::`). Step's green checkmark conveys success natively. No ANSI escape codes.
- **Surgical iteration before any orphan flatten.** Every file reaches its final form before the orphan commit — the new root captures one clean state, no follow-up cleanup commits.
- **Security baseline — non-negotiable**:
  - `pnpm install --frozen-lockfile --ignore-scripts` on every install. `--frozen-lockfile` fails on stale `pnpm-lock.yaml`; `--ignore-scripts` cuts the postinstall vector.
  - `secrets:` blocks at the workflow_call level declare ONLY the secrets that job consumes. NEVER `secrets: inherit` anywhere in this repo's workflows.
  - `pnpm publish` auto-detects: `--provenance --no-git-checks` (OIDC Trusted Publisher) when `NPM_PACKAGE_REGISTRY_TOKEN` is unset; `--no-git-checks` (token-based via `.npmrc`) when set. No input toggle.
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
- Four composite actions: `check-docs` (transverse — run context dump + README check), `javascript/base` (JS-specific — full preamble + install + lint + build + test), `release/generate-changelog` (transverse — tag format guard + CHANGELOG section generation/reuse, outputs `body`), `release/github-release` (transverse — GitHub Release creation). `check-docs` + `javascript/base` called by `preflight` and `publish`; `release/*` called by `publish` only.
- `javascript/base` has zero inputs. Reads `NPM_CONFIG_FILE` (required, fails if missing) + `NPM_EXTRA_CONFIG` (optional) from inherited workflow env. The bundled workflow sets both at workflow level from `secrets.NPM_CONFIG_FILE` + `vars.NPM_EXTRA_CONFIG`; standalone callers mirror the env block.
- `security.yml` is the reusable container for ALL security scans. Today it runs gitleaks. Future additions (container scanning, SAST, dependency audit) land here as more steps.
- `publish` job auto-generates the `## vX.Y.Z` CHANGELOG section from conventional commits since the previous tag (per `~/.claude/rules/changelog.md` convention), uses it as the GitHub Release body, then commits the CHANGELOG + bumped `package.json` + `pnpm-lock.yaml` back to `main` as `chore: release X.Y.Z`. Dev workflow: develop with conventional commits, tag, push — no manual CHANGELOG or bump. If a section for the tag already exists in `CHANGELOG.md` (hand-curated), `publish` reuses it instead of generating.

## Out of scope

- `check-shell` job (downstream parity — self-CI already runs `shellcheck`).
