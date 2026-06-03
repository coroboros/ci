# coroboros/ci

Reusable GitHub Actions workflows + composite actions for the Coroboros stack.

## Commands

- `actionlint -shellcheck=shellcheck` — workflows, `action.yml`, inline shell.
- `yamllint -c .yamllint .` — YAML lint.

## Important files

- `.github/workflows/javascript-npm-packages.yml` — bundled NPM pipeline (`preflight` / `supply-chain` / `publish` / `security`).
- `.github/workflows/rust-packages.yml` — bundled Cargo pipeline (`preflight` matrix / `supply-chain` / `publish` / `security`) + opt-in cargo-dist binary layer (`dist-plan` / `dist-build` / `dist-host` / `dist-publish`, gated on `[package.metadata.dist]`).
- `.github/workflows/security.yml` — `gitleaks` + `dependency-review` + `osv-scanner` (gitleaks/osv wrap `security/*` composites; the package `supply-chain` gates reuse them).
- `.github/workflows/{self,self-security,self-release}.yml` — self-CI: lint, gitleaks + osv (composites via local `./`), and the `v0` rolling-tag move.
- `.github/actions/{check-docs,javascript/base,rust/{base,native-deps,pin-version},security/{gitleaks,osv-scanner,cargo-deny},release/{generate-changelog,github-release,commit-artifacts,dist}}/action.yml` — composites.
- `.github/dependabot.yml` — auto-PRs for pinned actions.
- `security/.gitleaks.toml` — canonical gitleaks ruleset.
- `security/deny.toml` — canonical cargo-deny ruleset, imposed via `--config` (consumer `deny.toml` ignored; `deny.exceptions.toml` rejected).
- `README.md` — public documentation (single source for pipelines, composables, structure, flow, env, security, examples).

## Rules

- **Imposed, not proposed.** Zero `inputs:` / `secrets:` on reusable workflows unless variation is legitimate.
- **Pin third-party actions by commit SHA**, inline `# vX` comment. No `@main`, `@master`, `@vX`.
- **Pin tooling binaries by version.** SHA-256 verification on binary release tarballs. No `curl | bash`.
- **Composite refs**: `coroboros/ci/.github/actions/<name>@v0` from reusable workflows and consumers. Exception — `self-security.yml` uses local `./.github/actions/security/<name>` so a PR self-tests its own composites; a reusable workflow's `./` resolves to the caller's checkout, so `security.yml` must pin `@v0`.
- **`secrets:`** declares only what the job consumes. Never `secrets: inherit`.
- **`gitleaks` CLI direct**, not `gitleaks/gitleaks-action@v2` (paid org license).
- **House style**:
  - Env values quoted: `KEY: "value"`.
  - GH workflow log commands: `::error::`, `::warning::`, `::notice::`. No ANSI codes.
  - Declare env keys only where consumed.
- **Action and workflow files = implementation only.** Rationale lives in `CLAUDE.md` or `CHANGELOG.md`.

## Adding a workflow or composite

1. Update `README.md` (Pipelines / Composables table + Examples + Environment).
2. `actionlint -shellcheck=shellcheck` must exit 0.

## Release flow

- PR-only; no direct commits to `main`.
- In the PR (before merge): bump `package.json:version` + prepend `CHANGELOG.md` section (`## vX.Y.Z - DD/MM/YYYY`).
- Squash-merge.
- `git tag X.Y.Z && git push origin X.Y.Z` (no `v` prefix). `self-release.yml` then moves the rolling `v0` tag — no manual `git tag -f v0`.
- `gh release create X.Y.Z --title X.Y.Z --notes-file <CHANGELOG section>`.
