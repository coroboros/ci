# Flow

Coroboros development flow. The reusable workflows under `.github/workflows/` are designed around this branch model.

## Trigger model

The main workflow runs on push and tag events. Pull requests are excluded by the top-level `on:` block of each reusable workflow.

Triggers used:

- `push` to `main`, `latest`, `stable`, `release/x.y.z` branches.
- `push` of tags matching SemVer (`x.y.z`).

## Development flow

Development happens on `main` by pulling a feature branch from it. PR back into `main`, squash-merge, then tag the merge commit with a SemVer version. The tag push triggers the deploy chain (`build-version`, `deploy-package`, `notify`).

The more you tag, the more precise the release cadence and the faster you ship small pieces.

Nobody pushes directly to `main`. Tags follow [SemVer](https://semver.org/).

### Libraries

For library pipelines:

- `main` is the default and development branch; create a tag for every branch merged into it.
- Each tag deploys to the related package registry.
