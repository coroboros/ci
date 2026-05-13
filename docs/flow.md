# Flow

Coroboros development flow. The reusable workflows under `.github/workflows/` are designed around this branch model.

## Trigger model

The main workflow runs on push and tag events. Pull requests are excluded by the top-level `on:` block of each reusable workflow.

Triggers used:

- `push` to `develop`, `main`, `latest`, `stable`, `release/x.y.z` branches.
- `push` of tags matching SemVer (`x.y.z`).

## Development flow

Development happens on the `develop` branch by pulling a new feature branch from it. Tag every time something is merged into `develop` to keep track of every patch, minor, or major improvement.

The `main` branch is used only when it must reflect what runs in production — typically when the consumer software distinguishes **development**, **integration**, and **production** environments.

The more you tag, the more precise the release cadence and the faster you ship small pieces.

Nobody should push directly to `develop` or `main`. Tags follow [SemVer](https://semver.org/).

### Libraries

For library pipelines:

- `develop` is the main and development branch; create a tag for every branch merged into it.
- Each tag deploys to the related package registry.
