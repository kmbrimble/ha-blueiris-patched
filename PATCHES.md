# Local patches

Gitea (`kmbrimble/ha-blueiris-patched`) is the primary repo. GitHub is a push mirror that exists only so HACS can read a GitHub Release, as with the other personal HACS add-ons. Never push, tag or edit on GitHub.

This is `kramttocs/ha-blueiris` plus the changes below, both marked `kmb-patch` in the source. `tests/test_kmb_patches.py` fails if either is lost.

1. **Cycle views are online** (`api/blue_iris_api.py`, `_is_online`). A Blue Iris cycle view (`@Name`) has no `group` list and no `isOnline` in the camlist, so upstream marks it unavailable. For `@` entries that lack `isOnline`, follow `isEnabled`.
2. **10 fps MJPEG polling** (`camera.py`, `frame_interval`). Home Assistant's default is 0.5 s (2 fps).

The fork also drops upstream's `.github/workflows/validate.yaml` (it would run on the GitHub mirror) and adds `.github/workflows/release.yml`, which turns a mirrored tag into the GitHub Release.

## Staying current

`.gitea/workflows/upstream-sync.yml` runs on the Gitea runner every Monday 05:17 (Brisbane). It merges the newest upstream **release tag** (not upstream `main`), runs the tests, pushes `main` and tags `<upstream tag>.<n>` (for example `2026.10.29.1`). The mirror carries the tag to GitHub and `release.yml` publishes the Release. A conflict or failed test leaves `main` untouched and opens an issue titled "Upstream sync needs attention".

`workflow_dispatch` with `dry_run` merges and tests, then checks push access with a throwaway branch, and publishes nothing.

Resolve a conflict by hand:

    git remote add upstream https://github.com/kramttocs/ha-blueiris.git
    git fetch upstream 'refs/tags/*:refs/upstream-tags/*'
    git checkout -b sync/manual main
    git merge refs/upstream-tags/<tag>     # fix conflicts, keep the kmb-patch behaviour
    python3 -m unittest discover tests
    # merge to main, then tag <upstream tag>.<n> on Gitea
