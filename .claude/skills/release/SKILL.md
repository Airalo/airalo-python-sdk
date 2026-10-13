---
name: release
description: Cut a new version of the Airalo Python SDK by bumping the version via PR, tagging, creating the GitHub release, and walking through the PyPI publish steps.
disable-model-invocation: true
argument-hint: "[patch|minor|major|X.Y.Z]"
---

# Release the SDK

This skill publishes a version that partners will install, so **every step with an external effect (push, PR, tag, GitHub release, PyPI upload) needs the developer's explicit confirmation first.** Stop at any failed check.

Version facts:
- The version lives in **three** places that must stay identical: `airalo/__init__.py` (`__version__`), `setup.py` (`version=`), and `pyproject.toml` (`version =`).
- Tags are plain semver **without** a `v` prefix (`1.0.3`, not `v1.0.3`).
- The package is published to PyPI as `airalo-sdk`. There is no CI publish workflow; the upload is done by hand with `twine`.

## 1. Pre-checks

1. `git fetch --tags origin`, then confirm you're on `main`, it's up to date with `origin/main`, and the tree is clean.
2. Run the quality gates: `black --check airalo tests`, `pylint --fail-under=8 airalo`, `pytest -q tests`. All must pass.
3. Show the last tag (`git describe --tags --abbrev=0`) and confirm it equals the version in all three files above. If any differ, stop and ask.

## 2. Choose the version

1. List the commits since the last tag: `git log <last-tag>..HEAD --oneline`.
2. Propose a bump. `$ARGUMENTS` overrides the proposal if given.
   - **major:** any breaking change to a public method signature or response shape.
   - **minor:** any `feat:` commit.
   - **patch:** only `fix:` / `chore:` commits.
3. Show the proposed version with the commit list and wait for confirmation.

## 3. Bump via PR

1. Ask for the ticket key for this release.
2. Create branch `chore/release-X.Y.Z`, set the new version in **all three** files (`airalo/__init__.py`, `setup.py`, `pyproject.toml`), and commit `chore: release X.Y.Z (<TICKET>)`.
3. **Confirm**, then push and open the PR: `gh pr create --base main --title "chore: release X.Y.Z (<TICKET>)"`, with the commit list as the body.
4. Stop here and tell the developer to merge the PR once CI is green. Continue with step 4 after they say it's merged.

## 4. Tag and GitHub release

1. `git checkout main && git pull`, then confirm the version is `X.Y.Z` in all three files on `main`.
2. **Confirm**, then:
   ```
   git tag X.Y.Z
   git push origin X.Y.Z
   gh release create X.Y.Z --title "X.Y.Z" --generate-notes --verify-tag
   ```
3. Show the release URL.

## 5. Publish to PyPI (manual)

Print this checklist for the developer, and only run the build/upload steps on explicit confirmation.

- [ ] Build the artifacts: `python -m build` (produces `dist/airalo_sdk-X.Y.Z*`). Delete any stale `dist/` first.
- [ ] Check them: `twine check dist/*`.
- [ ] Upload: `twine upload dist/*` (needs a PyPI API token). Consider TestPyPI first with `twine upload --repository testpypi dist/*`.
- [ ] Confirm `X.Y.Z` shows as the latest release on the `airalo-sdk` PyPI page and `pip install airalo-sdk==X.Y.Z` resolves.
- [ ] **Never delete released versions.** Partners may pin them.

## 6. Wrap up

Summarise what was done (PR, tag, release URL) and what's left on the PyPI checklist.
