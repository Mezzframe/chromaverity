# Releasing chromaverity

How a version goes from `main` to GitHub and PyPI. Written for the maintainer; useful to anyone curious how the package gets published.

## One-time setup: tell PyPI to trust our release workflow

We publish with PyPI's **Trusted Publishing**. No password or API token lives anywhere: when the release workflow runs, GitHub gives it a short-lived identity token, and PyPI accepts the upload only if that token says "Novapakt/chromaverity, workflow release.yml, environment pypi". You tell PyPI to expect that once.

1. Sign in at [pypi.org](https://pypi.org) (create an account if needed, and turn on two-factor auth: PyPI requires it to publish).
2. Go to **Your account → Publishing** and add a **pending publisher** (the project doesn't exist on PyPI until the first upload, so it's "pending"):

   | Field | Value |
   |---|---|
   | PyPI project name | `chromaverity` |
   | Owner | `Novapakt` |
   | Repository name | `chromaverity` |
   | Workflow name | `release.yml` |
   | Environment name | `pypi` |

3. On GitHub, **Settings → Environments → New environment**, name it `pypi`. Optionally add yourself as a required reviewer: then every upload waits for your click, which is a good last check before something permanent happens.

## Cutting a release

1. On a branch, set the version in `src/chromaverity/__init__.py` (the only place; `pyproject.toml` reads it) and in `CITATION.cff` (`version` and `date-released`).
2. In `CHANGELOG.md`, move the `[Unreleased]` items under a new `## [X.Y.Z] - YYYY-MM-DD` heading and update the two links at the bottom.
3. Open a PR, let CI pass, merge.
4. Create the release from `main`:

   ```bash
   gh release create vX.Y.Z --target main --title "vX.Y.Z" --notes-file notes.md
   ```

   `gh release create` makes the git tag and the GitHub release in one step. `--target main` tags the current tip of `main`. `--notes-file` is the text shown on the release page (paste that version's CHANGELOG section into it).

5. Publishing the release starts `.github/workflows/release.yml`. It refuses to continue if the tag (`v0.1.0`) and the package version (`0.1.0`) differ, builds, runs `twine check`, and uploads. Watch it with `gh run watch`.

**A version number can be uploaded to PyPI only once.** If something is wrong after upload, you can "yank" it on pypi.org (hidden from new installs, still downloadable for anyone who pinned it), but you can't replace the files. Fix forward with the next patch version.

## Checking the result

```bash
python -m venv /tmp/cv-check && /tmp/cv-check/bin/pip install chromaverity==X.Y.Z
/tmp/cv-check/bin/chromaverity --version
```

On Windows PowerShell use a folder such as `$env:TEMP\cv-check` and `\Scripts\` instead of `/bin/`.
