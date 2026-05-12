# Usage

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

### Container Images

The Coroboros default registry is **`ghcr.io`**. With it, the only credential needed is the per-run `GITHUB_TOKEN` — no long-lived registry password to manage:

```yaml
jobs:
  ci:
    uses: coroboros/ci/.github/workflows/container-image.yml@v0
    permissions:
      contents: read
      packages: write   # required for ghcr.io push
    secrets:
      IMAGE_REGISTRY: ghcr.io
      IMAGE_REGISTRY_USER: ${{ github.actor }}
      IMAGE_REGISTRY_PASSWORD: ${{ secrets.GITHUB_TOKEN }}
      SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

For a custom registry (Docker Hub, ECR, self-hosted), set `IMAGE_REGISTRY` accordingly and provide a static `IMAGE_REGISTRY_USER` / `IMAGE_REGISTRY_PASSWORD`.

### JavaScript Assets

Builds via `pnpm run build`, syncs `dist/` to S3, optionally invalidates CloudFront.

AWS auth supports two modes (the workflow picks based on what you pass):

1. **OIDC (recommended)** — pass `aws-role-dev` / `aws-role-prod` ARNs as inputs; the IAM trust policy on each role must allow `token.actions.githubusercontent.com` for the consumer repo / ref. No long-lived AWS keys.
2. **Static keys (fallback)** — pass `AWS_ACCESS_KEY_ID_*` / `AWS_SECRET_ACCESS_KEY_*` as secrets.

```yaml
jobs:
  ci:
    uses: coroboros/ci/.github/workflows/javascript-assets.yml@v0
    with:
      assets_path: dist
      cdn_invalidate_cache: 'true'
      aws-role-dev: arn:aws:iam::111111111111:role/gha-deploy-dev
      aws-role-prod: arn:aws:iam::222222222222:role/gha-deploy-prod
    secrets:
      NPM_CONFIG_FILE: ${{ secrets.NPM_CONFIG_FILE }}
      NPM_PACKAGE_REGISTRY: ${{ secrets.NPM_PACKAGE_REGISTRY }}
      NPM_PACKAGE_PROXY_REGISTRY: ${{ secrets.NPM_PACKAGE_PROXY_REGISTRY }}
      NPM_PACKAGE_REGISTRY_TOKEN: ${{ secrets.NPM_PACKAGE_REGISTRY_TOKEN }}
      AWS_ACCESS_KEY_ID_DEV: ${{ secrets.AWS_ACCESS_KEY_ID_DEV }}
      AWS_SECRET_ACCESS_KEY_DEV: ${{ secrets.AWS_SECRET_ACCESS_KEY_DEV }}
      AWS_ACCESS_KEY_ID_PROD: ${{ secrets.AWS_ACCESS_KEY_ID_PROD }}
      AWS_SECRET_ACCESS_KEY_PROD: ${{ secrets.AWS_SECRET_ACCESS_KEY_PROD }}
      ASSETS_DESTINATION: ${{ secrets.ASSETS_DESTINATION }}
      CDN_ID: ${{ secrets.CDN_ID }}
      SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### JavaScript Functions

Builds, zips, deploys to AWS Lambda, optionally invokes the function in `post-deploy`.

```yaml
jobs:
  ci:
    uses: coroboros/ci/.github/workflows/javascript-function.yml@v0
    with:
      function_name: my-lambda
      function_invoke: 'true'
    secrets:
      NPM_CONFIG_FILE: ${{ secrets.NPM_CONFIG_FILE }}
      NPM_PACKAGE_REGISTRY: ${{ secrets.NPM_PACKAGE_REGISTRY }}
      NPM_PACKAGE_PROXY_REGISTRY: ${{ secrets.NPM_PACKAGE_PROXY_REGISTRY }}
      NPM_PACKAGE_REGISTRY_TOKEN: ${{ secrets.NPM_PACKAGE_REGISTRY_TOKEN }}
      AWS_ACCESS_KEY_ID_DEV: ${{ secrets.AWS_ACCESS_KEY_ID_DEV }}
      AWS_SECRET_ACCESS_KEY_DEV: ${{ secrets.AWS_SECRET_ACCESS_KEY_DEV }}
      AWS_ACCESS_KEY_ID_PROD: ${{ secrets.AWS_ACCESS_KEY_ID_PROD }}
      AWS_SECRET_ACCESS_KEY_PROD: ${{ secrets.AWS_SECRET_ACCESS_KEY_PROD }}
      SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### JavaScript Images

Builds a JavaScript project, packages it as a container image.

```yaml
jobs:
  ci:
    uses: coroboros/ci/.github/workflows/javascript-image.yml@v0
    secrets:
      NPM_CONFIG_FILE: ${{ secrets.NPM_CONFIG_FILE }}
      NPM_PACKAGE_REGISTRY: ${{ secrets.NPM_PACKAGE_REGISTRY }}
      NPM_PACKAGE_PROXY_REGISTRY: ${{ secrets.NPM_PACKAGE_PROXY_REGISTRY }}
      NPM_PACKAGE_REGISTRY_TOKEN: ${{ secrets.NPM_PACKAGE_REGISTRY_TOKEN }}
      IMAGE_REGISTRY: ${{ secrets.IMAGE_REGISTRY }}
      IMAGE_REGISTRY_USER: ${{ secrets.IMAGE_REGISTRY_USER }}
      IMAGE_REGISTRY_PASSWORD: ${{ secrets.IMAGE_REGISTRY_PASSWORD }}
      SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Node Services

The full service pipeline: npm, container image, multi-environment deploy, optional API tests.

```yaml
jobs:
  ci:
    uses: coroboros/ci/.github/workflows/node-service.yml@v0
    secrets: inherit   # convenience for services that consume the full secret set
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
      - uses: coroboros/ci/.github/actions/check-readme@v0
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
