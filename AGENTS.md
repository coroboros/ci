# coroboros/ci

Reusable GitHub Actions workflows and composite actions for the Coroboros stack. `README.md` owns pipeline contracts, environment variables, security policy and consumer examples.

## Project constraints

- Reusable workflows impose shared defaults; add inputs or secrets only for legitimate variation. Declare only consumed secrets; prohibit `secrets: inherit`.
- Pin third-party actions by full commit SHA with a version comment, and tooling binaries by version plus verified SHA-256. Do not pipe remote scripts into a shell.
- Reusable workflows and consumers reference composites at `coroboros/ci/.github/actions/<name>@v0`. Local `./` refs resolve against the caller checkout; self-tests use them deliberately to exercise PR code.
- Security gates fail closed. `security/deny.toml` owns Cargo advisory, ban and source policy; consumer `deny.toml` is ignored and exception files are rejected. Propose justified transitive-advisory exceptions centrally. The separate advisory workflow owns non-blocking license/quality checks.
- Use the gitleaks CLI directly; the third-party action requires a paid organization licence. `security/.gitleaks.toml` is the canonical ruleset.
- Keep consumer-visible workflow job IDs stable: imperative kebab-case, with existing phase-call and cargo-dist names as exceptions. Quote environment values, declare them where consumed, and use GitHub log commands without ANSI escapes.
- Keep action/workflow files focused on implementation. Put rationale in the owning documentation or changelog; update affected README contracts and examples with behavior changes.

## Validation

- Workflow/composite changes: `actionlint -shellcheck=shellcheck`, `yamllint -c .yamllint .`, and the relevant self-tests.
- Check consumer impact when changing reusable contracts. Self-tests that reference `@v0` exercise the released composites; local-ref tests exercise the PR. Tag-only behavior needs evidence from an authorized release.
- Documentation changes: check claims against source, affected links and `git diff --check`.

## Release

- PR-only into `main`, then squash merge. Manually bump `package.json:version` and prepend the matching `CHANGELOG.md` entry before merge.
- After authorization, create an annotated SemVer tag without a `v` prefix on the reviewed merge commit, then a GitHub release using that version as its title and the changelog entry as notes.
- `self-release.yml` owns the rolling `v0` update. It does not bump manifests or create the GitHub release; do not move `v0` manually.
