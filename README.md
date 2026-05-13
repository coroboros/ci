<div align="center">

<img src="assets/logo.png" width="288" height="288" alt="Coroboros"/>

<!-- omit in toc -->
# coroboros/ci

**Reusable GitHub Actions CI for the Coroboros stack.**

Drop into any `@coroboros/*` repo via `uses: coroboros/ci/.github/workflows/<name>.yml@v0`, or compose your own pipeline from the per-step composites under `.github/actions/`.

[![latest](https://img.shields.io/github/v/release/coroboros/ci?style=flat-square&label=latest&color=000000)](https://github.com/coroboros/ci/releases)
[![ci](https://img.shields.io/github/actions/workflow/status/coroboros/ci/ci.yml?branch=main&style=flat-square&label=ci&color=000000)](https://github.com/coroboros/ci/actions/workflows/ci.yml)
[![branch](https://img.shields.io/badge/branch-main-000000?style=flat-square)](https://github.com/coroboros/ci)
[![license](https://img.shields.io/badge/license-All%20Rights%20Reserved-000000?style=flat-square)](LICENSE.md)
[![stars](https://img.shields.io/github/stars/coroboros/ci?style=flat-square&label=stars&color=000000)](https://github.com/coroboros/ci)
[![skills](https://img.shields.io/badge/skills-000000?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDE2IDE2IiBmaWxsPSJ3aGl0ZSI+PHBvbHlnb24gcG9pbnRzPSI4LDAgMTAsNiAxNiw4IDEwLDEwIDgsMTYgNiwxMCAwLDggNiw2Ii8+PC9zdmc+)](https://github.com/coroboros/agent-skills)
[![coroboros.com](https://img.shields.io/badge/coroboros.com-000000?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiLz48cGF0aCBkPSJNMiAxMmgyME0xMiAyYTE1LjMgMTUuMyAwIDAgMSA0IDEwIDE1LjMgMTUuMyAwIDAgMS00IDEwIDE1LjMgMTUuMyAwIDAgMS00LTEwIDE1LjMgMTUuMyAwIDAgMSA0LTEweiIvPjwvc3ZnPg==)](https://coroboros.com)

</div>

## Pipelines

| Workflow | Use case |
| :------- | :------- |
| `javascript-npm-package.yml` | npm libraries published to a registry. OIDC `pnpm publish --provenance` with `NPM_PACKAGE_REGISTRY_TOKEN` fallback. |
| `security.yml` | Container for all security scans (gitleaks today, container scanning / SAST / audit later). Reports rather than blocks for late-stage scans; gitleaks remains a fail-fast check on real leaks. |
| `notify.yml` | Slack + Google Chat notifications on release-triggering refs. |

## Quick start

```yaml
# consumer-repo/.github/workflows/ci.yml
name: CI
on:
  push:
    branches: [develop, main]
    tags: ['*']
  workflow_dispatch:

jobs:
  ci:
    uses: coroboros/ci/.github/workflows/javascript-npm-package.yml@v0
    permissions:
      id-token: write
      contents: read
    secrets:
      NPM_CONFIG_FILE: ${{ secrets.NPM_CONFIG_FILE }}
      NPM_PACKAGE_REGISTRY: ${{ secrets.NPM_PACKAGE_REGISTRY }}
      NPM_PACKAGE_PROXY_REGISTRY: ${{ secrets.NPM_PACKAGE_PROXY_REGISTRY }}
      NPM_PACKAGE_REGISTRY_TOKEN: ${{ secrets.NPM_PACKAGE_REGISTRY_TOKEN }}
      SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## Composable actions

Each composite action under `.github/actions/` is a single pipeline step. Use them to assemble a custom pipeline when the bundled workflows do not fit:

| Action | Purpose |
| :----- | :------ |
| `check-docs` | Fail the job if `README.md` is missing at the repo root. |
| `setup-npmrc` | Generate `.npmrc` files from secrets, upload them as an artifact. |
| `pnpm-install` | Corepack-enabled `pnpm install --frozen-lockfile --ignore-scripts`. |
| `build-js` | Run the pnpm build script if present; upload `dist/` as an artifact. |
| `build-version` | Extract the SemVer version from tag / branch / commit and pin `package.json`. |
| `notify-slack` | Post a deployment notification to a Slack webhook. |
| `notify-gchat` | Post a deployment notification to a Google Chat webhook. |

## Usage

### Stages

[`docs/stages.md`](docs/stages.md)

### Flow

[`docs/flow.md`](docs/flow.md)

### Environment Variables

[`docs/environment-variables.md`](docs/environment-variables.md)

### Examples

[`docs/examples.md`](docs/examples.md)

## Security

[`docs/security.md`](docs/security.md)

## License

All Rights Reserved. See [LICENSE.md](LICENSE.md).
