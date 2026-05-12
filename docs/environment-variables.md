# Environment variables

Each variable below is passed either as a **secret** (`secrets:` block on `workflow_call`) or as an **input** (`inputs:` block).

> The JS workflows use **pnpm** (resolved via corepack). `NPM_*` variable names are kept — pnpm reads the same `.npmrc` syntax. See `usage.md` § *Package manager*.

**Naming convention**: inputs are `kebab-case`, secrets are `UPPER_SNAKE_CASE`. A variable is mandatory only when the workflow that consumes it is in use; workflows outside a scope do not require the scope's variables.

## Common — across most workflows

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `node-version` | input | Node.js version. | | `22` |
| `release-branch-pattern` | input | ERE pattern matching release branches. | | `^release[/]((0\|[1-9][0-9]*)\.(0\|[1-9][0-9]*)\.(0\|[1-9][0-9]*))$` |
| `release-source-commit-pattern` | input | ERE pattern matching the release-source merge commit message. Used to extract the version when merging `release/x.y.z` into the production branch. | | `^Merge branch 'release[/]((0\|[1-9][0-9]*)\.(0\|[1-9][0-9]*)\.(0\|[1-9][0-9]*))' into 'master'` |
| `npm-extra-config` | input | Extra `.npmrc` content appended after `NPM_CONFIG_FILE`. | | `""` |
| `dev-branch` | input | Branch that gates `deploy-dev` jobs and (in AWS workflows) routes the DEV AWS credentials. | | `develop` |
| `prod-branch` | input | Branch that gates `deploy-prod` jobs and (in AWS workflows) routes the PROD AWS credentials. | | `master` |

## NPM — `javascript-*` workflows

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `provenance` | input (bool) | When `true`, pass `--provenance` to `pnpm publish` (requires npm Trusted Publisher OIDC). Set to `false` when only `NPM_TOKEN` is available. *(npm-package only)* | | `true` |
| `NPM_CONFIG_FILE` | secret | `.npmrc` content, consumed by `setup-npmrc`. | X | none |
| `NPM_PACKAGE_REGISTRY` | secret | npm package registry URL. | X | none |
| `NPM_PACKAGE_PROXY_REGISTRY` | secret | npm package proxy registry URL. | X | none |
| `NPM_PACKAGE_REGISTRY_TOKEN` | secret | npm package registry token. | X | none |
| `NPM_TOKEN` | secret | npmjs.com publish token. Optional — if absent, OIDC Trusted Publisher is used. *(npm-package only)* | | none |

## AWS — `javascript-assets`, `javascript-function`

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `aws-role-dev` | input | IAM role ARN to assume for the dev account via OIDC. Recommended over static keys. | | `""` |
| `aws-role-prod` | input | IAM role ARN to assume for the prod account via OIDC. Recommended over static keys. | | `""` |
| `AWS_ACCESS_KEY_ID_DEV` | secret | Static fallback for the dev account. Required only when `aws-role-dev` is unset. | | none |
| `AWS_SECRET_ACCESS_KEY_DEV` | secret | Static fallback for the dev account. Required only when `aws-role-dev` is unset. | | none |
| `AWS_ACCESS_KEY_ID_PROD` | secret | Static fallback for the prod account. Required only when `aws-role-prod` is unset. | | none |
| `AWS_SECRET_ACCESS_KEY_PROD` | secret | Static fallback for the prod account. Required only when `aws-role-prod` is unset. | | none |

## Container images — `javascript-image`, `container-image`, `node-service`

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `dockerfile-path` | input | Dockerfile path. | | `Dockerfile` |
| `image-target` | input | Target path under the registry. Defaults to the repo owner. | | `""` |
| `image-tag` | input | Override for the main image tag. Falls back to git tag, then ref slug. | | `""` |
| `image-build-args` | input | Build args passed to Kaniko (e.g. `--build-arg NPM_PACKAGE_REGISTRY_TOKEN=${NPM_PACKAGE_REGISTRY_TOKEN}`). | | `""` |
| `image-registry-mirror` | input | Additional registry mirror flag (e.g. `--registry-mirror https://my-mirror`). | | `""` |
| `IMAGE_REGISTRY` | secret | Container registry URL. The Coroboros default is `ghcr.io` (no static password — pass `github.actor` + `secrets.GITHUB_TOKEN`). | X | none (recommended: `ghcr.io`) |
| `IMAGE_REGISTRY_USER` | secret | Container registry user. | X | none |
| `IMAGE_REGISTRY_PASSWORD` | secret | Container registry password. | X | none |
| `IMAGE_CACHE_REPO` | secret | Repository for Kaniko's layer cache. | | none |

## Assets — `javascript-assets`

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `assets-path` | input | Local path to the built assets. | | `dist` |
| `assets-region` | input | AWS region for the destination bucket. | | `us-east-1` |
| `assets-options` | input | Extra options passed to `aws s3 sync` ([reference](https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html#synopsis)). | | `--exclude "*.DS_Store" --cache-control "max-age=31536000"` |
| `cdn-invalidate-cache` | input | Whether to invalidate CDN cache in `post-deploy` (`true` or `1`). | | `false` |
| `cdn-invalidate-paths` | input | Paths to invalidate. | | `/*` |
| `ASSETS_DESTINATION` | secret | S3 bucket (and optional prefix) to sync to. | X | none |
| `CDN_ID` | secret | CloudFront distribution ID. Required when `cdn-invalidate-cache=true`. | | none |

## Lambda functions — `javascript-function`

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `function-name` | input | Base function name. The deploy action appends `-dev` or `-prod` based on the current branch. | X | none |
| `function-archive` | input | Output archive filename. | | `function.zip` |
| `function-path` | input | Directory holding the build output. | | `dist` |
| `function-region` | input | AWS region for the Lambda function. | | `us-east-1` |
| `function-deploy-disable` | input | When `true` or `1`, skip deployment. | | `false` |
| `function-invoke` | input | When `true` or `1`, invoke the function in `post-deploy`. | | `false` |
| `function-invoke-options` | input | Additional options for [`aws lambda invoke`](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html). | | `""` |

## Node services — `node-service`

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `release` | input | Release name, typically the project name. | | `${{ github.event.repository.name }}` |
| `deploy-dynamic-branch-regex` | input | Branch pattern allowing dynamic deployment. | | `^feat/.*` |

## Notifications — `notify` (called from every entry-point workflow)

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `SLACK_WEBHOOK_URL` | secret | Slack webhook URL. Notification is skipped when empty. | | none |
| `GOOGLE_CHAT_WEBHOOK_URL` | secret | Google Chat webhook URL. Notification is skipped when empty. | | none |

## Security — `security.yml`

| name | type | description | required | default |
| :--- | :--- | :---------- | :------- | :------ |
| `config-path` | input | Path to the gitleaks config in the calling repo. Falls back to fetching `coroboros/ci`'s canonical ruleset over raw URL if the file is absent. | | `security/.gitleaks.toml` |
| `gitleaks-version` | input | Pinned gitleaks CLI version (without leading `v`). | | `8.30.1` |
| `gitleaks-sha256` | input | SHA-256 of `gitleaks_<version>_linux_x64.tar.gz` for end-to-end checksum verification. Empty = skip with warning. Update when bumping `gitleaks-version`. | | (pinned) |
| `scan-mode` | input | `git` walks history; `dir` scans the working tree only. | | `git` |
| `fail-on-leak` | input (bool) | Fail the job when leaks are found. | | `true` |
