# Examples

Each reusable workflow under `.github/workflows/` is a full pipeline for one project type. A consumer repo wires it in via `uses: coroboros/ci/.github/workflows/<name>.yml@v0`. Composite actions under `.github/actions/` are the per-step building blocks; call them directly when you assemble your own pipeline.

See [`environment-variables.md`](environment-variables.md) for the full secret / input catalog and the *Package manager* section below for the pnpm setup.

## Full pipelines

### NPM Packages

```yaml
# consumer-repo/.github/workflows/ci.yml
name: CI
on:
  push:
    branches: [develop, master]
    tags: ['*']
  workflow_dispatch:

jobs:
  ci:
    uses: coroboros/ci/.github/workflows/javascript-npm-package.yml@v0
    permissions:
      id-token: write    # required for npm OIDC publish
      contents: read
    secrets:
      NPM_CONFIG_FILE: ${{ secrets.NPM_CONFIG_FILE }}
      NPM_PACKAGE_REGISTRY: ${{ secrets.NPM_PACKAGE_REGISTRY }}
      NPM_PACKAGE_PROXY_REGISTRY: ${{ secrets.NPM_PACKAGE_PROXY_REGISTRY }}
      NPM_PACKAGE_REGISTRY_TOKEN: ${{ secrets.NPM_PACKAGE_REGISTRY_TOKEN }}
      NPM_TOKEN: ${{ secrets.NPM_TOKEN }}   # optional, falls back to OIDC if absent
      SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## Secrets scan as a standalone workflow

```yaml
# consumer-repo/.github/workflows/security.yml
on:
  pull_request:
  push:
    branches: [develop, master]
  schedule:
    - cron: '0 0 * * 0'

jobs:
  scan:
    uses: coroboros/ci/.github/workflows/security.yml@v0
```

The workflow installs the upstream `gitleaks` CLI directly (no third-party action — `gitleaks/gitleaks-action@v2` is paid for organizations). All inputs are optional:

| input | default | description |
| :---- | :------ | :---------- |
| `config-path` | `security/.gitleaks.toml` | Path to the gitleaks config in the calling repo. Falls back to fetching `coroboros/ci`'s canonical ruleset over raw URL if the file is absent. |
| `gitleaks-version` | `8.30.1` | Pinned gitleaks CLI version. Bump in lockstep with [gitleaks releases](https://github.com/gitleaks/gitleaks/releases). |
| `gitleaks-sha256` | (pinned) | SHA-256 of `gitleaks_<version>_linux_x64.tar.gz` for end-to-end checksum verification. Empty = skip with warning. Update when bumping `gitleaks-version`. |
| `scan-mode` | `git` | `git` walks history; `dir` scans the working tree only. |
| `fail-on-leak` | `true` | Set `false` to surface findings without failing the job. |

The scan emits a SARIF report uploaded as the `gitleaks-report` artifact (30-day retention).

## Notifications as a standalone workflow

```yaml
jobs:
  notify:
    uses: coroboros/ci/.github/workflows/notify.yml@v0
    secrets:
      SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
      GOOGLE_CHAT_WEBHOOK_URL: ${{ secrets.GOOGLE_CHAT_WEBHOOK_URL }}
```

## Composing your own pipeline from composite actions

When the bundled workflows do not match, build a pipeline from individual composite actions:

```yaml
jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: coroboros/ci/.github/actions/check-docs@v0
      - uses: coroboros/ci/.github/actions/setup-npmrc@v0
        with:
          npm-config-file: ${{ secrets.NPM_CONFIG_FILE }}
      - uses: coroboros/ci/.github/actions/build-js@v0
      - uses: coroboros/ci/.github/actions/build-version@v0
      - run: |
          corepack enable
          pnpm publish --provenance --no-git-checks
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

## Package manager

All JS jobs use **pnpm** resolved via `corepack`. Pin the version in your consumer repo's `package.json`:

```json
{
  "packageManager": "pnpm@10.33.0"
}
```

`corepack enable` is called inside the composite actions; the first `pnpm` invocation downloads the pinned version and runs against the calling repo's `pnpm-lock.yaml`. Install flags applied automatically: `--frozen-lockfile --ignore-scripts` (and `--prod` where applicable).

See `docs/environment-variables.md` for the full secret / input catalog and `docs/flow.md` for the development flow.
