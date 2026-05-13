# Pipeline structure

`javascript-npm-packages.yml` runs in **three jobs**, gated by the trigger event:

```
preflight  (branch pushes)  → check-docs → javascript/base
publish    (tag pushes)     → check-docs → javascript/base → pin version → npm publish → GitHub release
security   (every trigger)  → gitleaks scan (calls security.yml)
```

Each job runs all its steps in a **single runner** — no inter-job artifacts, no `needs:` chain except `security` invoking `security.yml`. The transverse `check-docs` composite runs first; the JS-specific `javascript/base` composite carries the full preamble + install + lint + build + test.

## `preflight` (branches)

1. `actions/checkout`.
2. `check-docs` — run context dump + `README.md` presence check.
3. `javascript/base` — `.node-version` resolution (required; fail if missing) + `actions/setup-node` + corepack + pnpm store cache + `.npmrc` generation (from inherited `NPM_CONFIG_FILE` + `NPM_EXTRA_CONFIG` env) + `pnpm install --frozen-lockfile --ignore-scripts` + `pnpm run lint` + `pnpm run build` (conditional on `scripts.build`) + `pnpm test`.

## `publish` (tags)

Different checkout from `preflight`: checks out `main` with full history (`fetch-depth: 0`) to access tag metadata for CHANGELOG generation. Verifies the tag points to `main` HEAD — fails fast if `main` has moved since the tag was pushed.

1. `actions/checkout` (`ref: main`, `fetch-depth: 0`).
2. Verify `main` HEAD matches tag SHA — fail if not.
3. `check-docs` + `javascript/base` (install + lint + build + test).
4. `pnpm version --allow-same-version --no-git-tag-version "${GITHUB_REF_NAME}"` — pin `package.json` to the tag.
5. Generate the `## vX.Y.Z - DD/MM/YYYY` section in `CHANGELOG.md` from conventional commits since the previous tag (or all commits if first release). Prepend after the `# Changelog` header. Handles missing/empty `CHANGELOG.md`. Idempotent — reuses the existing section on rerun.
6. `pnpm publish` — auto-detect by `NPM_PACKAGE_REGISTRY_TOKEN` presence: `--provenance --no-git-checks` (OIDC) when absent; `--no-git-checks` (token-based via `.npmrc`) when set.
7. `gh release create "${GITHUB_REF_NAME}" --title "${GITHUB_REF_NAME}" --notes-file <changelog-section>`.
8. Commit `CHANGELOG.md` + `package.json` + `pnpm-lock.yaml` back to `main` as `chore: release ${GITHUB_REF_NAME}`. Push via default `GITHUB_TOKEN` (workflow has `permissions: contents: write`).

## `security` (every trigger)

Calls `security.yml`. gitleaks pinned + SHA-256 verified, runs against the calling repo's git history. SARIF report uploaded as the `gitleaks-report` artifact (30-day retention).
