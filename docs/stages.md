# Stages

Ten-stage conceptual pipeline. GitHub Actions has no `stages` primitive — job ordering is expressed via `jobs.<id>.needs`. The stages below drive the `needs:` graph inside each reusable workflow.

1. `setup` — `.npmrc` generation and other pre-build setup.
2. `check` — linting, YAML/shell validation, README/docs presence checks. **`check-security`** (gitleaks fail-fast on real leaks) also lands here — see `security.yml`.
3. `build` — JavaScript build, image-name computation, version extraction.
4. `publish` — container image push via Kaniko.
5. `test` — unit tests. Karate / Postman API tests not yet wired up.
6. `pre-deploy` — reserved; currently unused.
7. `deploy` — deployments to `development` / `int` / `production` and dynamic feature environments; Lambda updates; S3 asset uploads. AWS auth via OIDC role assumption with static-key fallback.
8. `post-deploy` — Lambda invocation, CDN cache invalidation.
9. `security` — container scanning, SAST, dependency audit — reports rather than blocking. Today only gitleaks is wired (in `check-security` above); the `security` stage proper is reserved for image / SAST scans landing later via `security.yml`.
10. `notify` — Slack and Google Chat notifications on deployment events.

Dynamic feature environments have no native auto-stop on GHA.
