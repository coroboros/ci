# Pipeline structure

`javascript-npm-packages.yml` runs in **three jobs**, gated by the trigger event:

```
preflight  (branch pushes)  → setup → lint → build → test
publish    (tag pushes)     → setup → lint → build → test → pin version → npm publish → GitHub release → notify
security   (every trigger)  → gitleaks scan (calls security.yml)
```

Each job runs all its steps in a **single runner** — no inter-job artifacts, no `needs:` chain except `security` invoking `security.yml`. The shared install + setup chunk lives in the `javascript/base` composite action and runs as the first step of both `preflight` and `publish`.

## `preflight` (branches)

1. `actions/checkout`.
2. `javascript/base` — `.node-version` resolution (else `DEFAULT_NODE_VERSION=22`) + `actions/setup-node` + corepack + pnpm store cache + `.npmrc` generation (from `NPM_CONFIG_FILE` secret + `vars.NPM_EXTRA_CONFIG`) + README presence check + `pnpm install --frozen-lockfile --ignore-scripts`.
3. `pnpm run lint`.
4. `pnpm run build` (only if `scripts.build` exists in `package.json`; otherwise logs `Non required script 'build' skipped` in green).
5. `pnpm test`.

## `publish` (tags)

Steps 1–5 same as `preflight` (re-run on tag for safety).

6. `pnpm version --allow-same-version --no-git-tag-version "${GITHUB_REF_NAME}"` — pin `package.json` to the tag.
7. Extract the matching `## vX.Y.Z` (or `## X.Y.Z`) section from `CHANGELOG.md`. Fails the job when no matching section is found.
8. `pnpm publish --provenance --no-git-checks` (OIDC, default) or `pnpm publish --no-git-checks` (token fallback, when `provenance: false` — `NPM_PACKAGE_REGISTRY_TOKEN` flows in as `NODE_AUTH_TOKEN`).
9. `gh release create "${GITHUB_REF_NAME}" --title "${GITHUB_REF_NAME}" --notes-file <changelog-section>`.
10. Notify Slack — `curl` to `SLACK_WEBHOOK_URL`. Skipped when the secret is empty. `continue-on-error: true` (webhook outage is non-blocking).
11. Notify Google Chat — same pattern.

## `security` (every trigger)

Calls `security.yml`. gitleaks pinned + SHA-256 verified, runs against the calling repo's git history (or working tree, configurable via `scan-mode`). SARIF report uploaded as the `gitleaks-report` artifact (30-day retention).
