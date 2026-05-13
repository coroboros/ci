# Stages

Ten-stage conceptual pipeline. GitHub Actions has no `stages` primitive — job ordering is expressed via `jobs.<id>.needs`. The stages below drive the `needs:` graph inside each reusable workflow.

The `javascript-npm-package` pipeline exercises **`setup`**, **`check`**, **`build`**, **`test`**, **`deploy`**, **`security`** (via the standalone `security.yml`), and **`notify`** (via the standalone `notify.yml`). The remaining stages — `publish`, `pre-deploy`, `post-deploy` — are reserved for future pipelines.

1. `setup` — pre-build setup (e.g. `.npmrc` generation). *Exercised: `setup-npmrc`.*
2. `check` — linting, validation, presence checks. *Exercised: `check-docs`, `check-npm-lint`.*
3. `build` — compile / package / version extraction. *Exercised: `build-js`, `build-version`.*
4. `publish` — *reserved.* Intended for artefact pushes that precede the deploy stage.
5. `test` — unit and integration tests. *Exercised: `test-npm-unit`.*
6. `pre-deploy` — *reserved.* Intended for pre-deployment checks against deploy targets.
7. `deploy` — release-time deployment. *Exercised: `deploy-package` (`pnpm publish` on tag, OIDC + provenance with `NPM_TOKEN` fallback).*
8. `post-deploy` — *reserved.* Intended for post-deploy verification.
9. `security` — security scans. *Exercised:* the standalone `security.yml` sub-workflow runs gitleaks (pinned `v8.30.1`, SHA-256 verified) as a fail-fast leak check. Container scanning, SAST, and dependency audit may land here later.
10. `notify` — release-event notifications. *Exercised:* the standalone `notify.yml` sub-workflow gated by the `should-notify` job (Slack + Google Chat).
