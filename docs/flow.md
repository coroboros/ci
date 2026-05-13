# Flow

Coroboros development flow for repos consuming `javascript-npm-packages.yml`.

## Trigger model

The reusable workflow's three jobs gate on the GitHub event:

- `preflight` runs when `github.ref_type == 'branch'` — on push to any branch the caller workflow listens to.
- `publish` runs when `github.ref_type == 'tag'` — on tag push, full deploy chain.
- `security` runs on every trigger.

Pull request handling depends on the caller's `on:` block. Consumers typically wire:

```yaml
on:
  push:
    branches: [develop, main]
    tags: ['*']
  pull_request:
```

## Development flow

Two supported branch models:

### main-only (libraries)

- `main` is the default branch.
- Pull a feature branch from `main` → PR → squash-merge into `main`.
- Tag the merge commit with a SemVer version (`x.y.z`, no `v` prefix).
- The tag push triggers `publish` → npm publish + GitHub Release.

### develop + main (multi-stage)

- `develop` is the dev branch.
- PR into `develop` → squash-merge → tag a pre-release version.
- For production: create a `release/x.y.z` branch from a develop tag → merge to `main` once integration validates → tag the final version on `main`.

Nobody pushes directly to `main` (or `develop`). Tags follow [SemVer](https://semver.org/).

## CHANGELOG and release artifacts

The `publish` job auto-generates the `## vX.Y.Z - DD/MM/YYYY` section in `CHANGELOG.md` from conventional commits since the previous tag, then commits `CHANGELOG.md` + `package.json` (bumped to the tag) + `pnpm-lock.yaml` (if changed) back to `main` as `chore: release X.Y.Z`. The GitHub Release body uses the same section.

Dev workflow: develop with conventional commits → tag → push. No manual CHANGELOG or version bump.

Conventional commit types map to CHANGELOG subsections:

| Commit type | CHANGELOG subsection |
| :---------- | :------------------- |
| `feat` | Features |
| `fix` | Fixes |
| `refactor` | Refactor |
| `perf` | Performance |
| `docs` | Documentation |
| `chore` / `ci` / `build` | Configuration |
| `test` | Tests |
| `style` | Style |
| `!:` or `BREAKING CHANGE:` | Breaking Changes (always first) |

Idempotent — if the section for the tag already exists in `CHANGELOG.md` (e.g., hand-curated), `publish` reuses it instead of generating a new one.
