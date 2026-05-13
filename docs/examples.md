# Examples

Each reusable workflow under `.github/workflows/` is a full pipeline for one project type. A consumer repo wires it in via `uses: coroboros/ci/.github/workflows/<name>.yml@v0`. The single composite action under `.github/actions/javascript/base/` is the shared preamble used by the workflow's jobs internally — also callable directly when you assemble your own pipeline.

## NPM Packages

```yaml
# consumer-repo/.github/workflows/ci.yml
name: CI
on:
  push:
    branches: [develop, main]
    tags: ['*']
  pull_request:
  workflow_dispatch:

jobs:
  ci:
    uses: coroboros/ci/.github/workflows/javascript-npm-packages.yml@v0
    permissions:
      contents: write   # GitHub Release creation on tag
      id-token: write   # npm OIDC publish on tag
    secrets:
      NPM_CONFIG_FILE: ${{ secrets.NPM_CONFIG_FILE }}
      NPM_PACKAGE_REGISTRY: ${{ secrets.NPM_PACKAGE_REGISTRY }}
      NPM_PACKAGE_PROXY_REGISTRY: ${{ secrets.NPM_PACKAGE_PROXY_REGISTRY }}
      NPM_PACKAGE_REGISTRY_TOKEN: ${{ secrets.NPM_PACKAGE_REGISTRY_TOKEN }}
      SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
      GOOGLE_CHAT_WEBHOOK_URL: ${{ secrets.GOOGLE_CHAT_WEBHOOK_URL }}
```

The three jobs trigger based on the event:

- `preflight` — branch pushes. Install + lint + build + test.
- `publish` — tag pushes. Preflight chain + pin `package.json` to tag + `pnpm publish` + GitHub Release (body = matching `CHANGELOG.md` section) + Slack / Google Chat notifications.
- `security` — every trigger. Calls `security.yml`.

## Standalone security scan

For a non-npm repo that wants only gitleaks:

```yaml
# consumer-repo/.github/workflows/security.yml
name: Security
on:
  push:
    branches: [develop, main]
  pull_request:
  schedule:
    - cron: '0 0 * * 0'

permissions:
  contents: read

jobs:
  scan:
    uses: coroboros/ci/.github/workflows/security.yml@v0
```

## Composing with `javascript/base`

When the bundled workflow doesn't fit, build a pipeline around `javascript/base`:

```yaml
jobs:
  custom:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    env:
      CI_TEXT_RED: "\e[31m"
      CI_TEXT_GREEN: "\e[32m"
      CI_TEXT_CLEAR: "\e[0m"
    steps:
      - uses: actions/checkout@v4
      - uses: coroboros/ci/.github/actions/javascript/base@v0
        with:
          node-version: "22"   # fallback when .node-version is absent
          npm-config-file: ${{ secrets.NPM_CONFIG_FILE }}
      - run: pnpm run my-custom-script
        shell: bash
```

## CHANGELOG-driven releases

The `publish` job reads the section in `CHANGELOG.md` matching the tag — either `## vX.Y.Z` or `## X.Y.Z` — and uses its body as the GitHub Release notes. Curate the entry before tagging. Tag `0.2.1` ⇒ workflow looks for `## v0.2.1` first, then `## 0.2.1`, fails if neither is found.

## Package manager

All JS jobs use **pnpm** resolved via `corepack`. Pin the version in your consumer repo's `package.json`:

```json
{
  "packageManager": "pnpm@10.33.0"
}
```

`corepack enable` runs inside `javascript/base`; the first `pnpm` invocation downloads the pinned version and runs against the calling repo's `pnpm-lock.yaml`. Install flags applied automatically: `--frozen-lockfile --ignore-scripts`.

See `docs/environment-variables.md` for the full secret / input / `vars` catalog and `docs/flow.md` for the development flow.
