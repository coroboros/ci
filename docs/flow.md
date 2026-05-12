# Flow

Coroboros development flow. The reusable workflows under `.github/workflows/` are designed around this branch model.

## Trigger model

The main workflow runs on push and tag events. Pull requests are excluded by the top-level `on:` block of each reusable workflow.

Triggers used:

- `push` to `develop`, `master`, `latest`, `stable`, `release/x.y.z` branches.
- `push` of tags matching SemVer (`x.y.z`).
- `workflow_dispatch` for manual operations (e.g. `undeploy-dynamic`).

Dynamic feature environments have no native auto-stop on GHA — the documented workaround is a scheduled cleanup workflow keyed off environment metadata, or an environment protection rule with manual cleanup.

## Development flow

Development happens on the `develop` branch by pulling a new feature branch from it. Tag every time something is merged into `develop` to keep track of every patch, minor, or major improvement.

The `master` branch is used only when it must reflect what runs in production — typically when the consumer software distinguishes **development**, **integration**, and **production** environments.

The more you tag, the more precise the release cadence and the faster you ship small pieces.

Nobody should push directly to `develop` or `master`. Tags follow [SemVer](https://semver.org/).

### Libraries

For library pipelines:

- `develop` is the main and development branch; create a tag for every branch merged into it.
- Each tag deploys to the related package registry.

### Multi-environment software

For software potentially deployed to several environments — typically a service in a micro-services architecture:

- `develop`
  - main and development branch; create a tag for every branch merged into it.
  - every merge into `develop` triggers a deployment to the **development** environment.
- to deploy a version in **integration**:
  - pick a version tag;
  - create a `release/<tag>` branch — this triggers the integration deployment.

    ```shell
    git checkout 1.2.0
    git branch release/1.2.0
    git push -u origin release/1.2.0
    ```
- to deploy a version in **production**:
  - merge the `release/<tag>` branch into `master` — this triggers the production deployment.
- hot fixes land on `master` and are cherry-picked into `develop`.
