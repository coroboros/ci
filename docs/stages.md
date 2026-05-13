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

Steps 1–3 same as `preflight`.

4. `pnpm version --allow-same-version --no-git-tag-version "${GITHUB_REF_NAME}"` — pin `package.json` to the tag.
5. Extract the matching `## vX.Y.Z` (or `## X.Y.Z`) section from `CHANGELOG.md`. Fails the job when no matching section is found.
6. `pnpm publish --provenance --no-git-checks` (OIDC, default) or `pnpm publish --no-git-checks` (token fallback, when `provenance: false` — `NPM_PACKAGE_REGISTRY_TOKEN` flows in as `NODE_AUTH_TOKEN`).
7. `gh release create "${GITHUB_REF_NAME}" --title "${GITHUB_REF_NAME}" --notes-file <changelog-section>`.

## `security` (every trigger)

Calls `security.yml`. gitleaks pinned + SHA-256 verified, runs against the calling repo's git history. SARIF report uploaded as the `gitleaks-report` artifact (30-day retention).
