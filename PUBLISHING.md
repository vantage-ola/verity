# Publishing and Versioning

## Semantic versioning

verity follows [semver](https://semver.org/): `MAJOR.MINOR.PATCH`.

| Change | Version bump | Example |
|--------|-------------|---------|
| Breaking API or CLI change | MAJOR | `0.x.x → 1.0.0` |
| New feature, backward-compatible | MINOR | `0.1.0 → 0.2.0` |
| Bug fix, docs, internal refactor | PATCH | `0.1.0 → 0.1.1` |

Breaking changes for verity specifically:
- Removing a CLI command or flag
- Changing `verity.json` schema in a way that breaks existing files
- Changing the `StorageBackend` protocol method signatures
- Removing anything from `src/verity/__init__.py`

### During `0.x.x`

While the major version is `0`, minor bumps (`0.1 → 0.2`) may include breaking changes. Declare stability at `1.0.0`.

---

## One-time PyPI trusted publishing setup

You only do this once per repository.

### Step 1 — PyPI side

1. Log in to [pypi.org](https://pypi.org).
2. Go to **Account settings → Publishing → Add a new pending publisher**.
3. Fill in:
   - **PyPI project name**: `verity`
   - **Owner**: `vantage-ola`
   - **Repository name**: `verity`
   - **Workflow filename**: `publish.yml`
   - **Environment name**: `pypi`
4. Save.

This allows GitHub Actions to push to PyPI using a short-lived OIDC token — no API keys, no secrets.

### Step 2 — GitHub side

1. In the GitHub repo, go to **Settings → Environments → New environment**.
2. Name it `pypi`.
3. Optional: add yourself as a required reviewer so every release needs manual approval.

That's it. The workflow in `.github/workflows/publish.yml` handles the rest automatically.

---

## Release process

### Step 1 — Update the version

Edit `pyproject.toml`:

```toml
[project]
version = "0.2.0"
```

### Step 2 — Update CHANGELOG.md

Add a new section at the top (below `[Unreleased]`):

```markdown
## [0.2.0] — YYYY-MM-DD

### Added
- ...

### Fixed
- ...

### Changed
- ...
```

Move everything under `[Unreleased]` into the new section, then clear `[Unreleased]`.

Update the comparison links at the bottom:

```markdown
[Unreleased]: https://github.com/vantage-ola/verity/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/vantage-ola/verity/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/vantage-ola/verity/releases/tag/v0.1.0
```

### Step 3 — Update verity.json (dogfood)

verity tracks its own proof chain. If you added a new feature, record it:

```bash
verity add feature feat:new-thing "New thing"
verity add claim   clm:new-thing.t1 "New thing works" --feature feat:new-thing --tier T1 --status verified
verity add test    tst:new-thing.unit "Unit tests" --claim clm:new-thing.t1 --kind unit --path tests/test_new_thing.py --status passing
verity add evidence evd:new-thing.ci "CI run" --test tst:new-thing.unit --artifact .github/workflows/ci.yml --status passed
verity validate
verity release 0.2.0
```

### Step 4 — Commit

```bash
git add pyproject.toml CHANGELOG.md verity.json
git commit -m "release: 0.2.0"
```

### Step 5 — Tag and push

```bash
git tag v0.2.0
git push origin main --tags
```

The `publish.yml` workflow fires on the `v*` tag. It:
1. Builds the wheel and sdist with `uv build`
2. Publishes to PyPI via OIDC (no secrets needed)
3. Creates a GitHub Release with the dist artifacts attached and auto-generated release notes

### What the GitHub Release will look like

GitHub auto-generates release notes from PR titles merged since the last tag. To make these useful:
- Write PR titles in imperative: `Add MemWal backend`, `Fix canonical JSON serialisation`
- Squash-merge feature branches with a descriptive title

---

## Verifying a release

After the workflow completes:

```bash
pip install walrus-verity==0.2.0
python -c "import verity; print(verity.__version__)"
```

Wait 1–2 minutes for PyPI to propagate.

---

## Yanking a bad release

If you need to pull a broken release from PyPI:

```bash
# Via the PyPI web UI: pypi.org/manage/project/verity/releases/<version>/
# Or via twine (requires API token for this specific action):
pip install twine
twine yank verity 0.2.0 --reason "Breaking regression in push()"
```

A yanked release is hidden from `pip install walrus-verity` but still accessible via `pip install walrus-verity==0.2.0 --no-index` by users who pin it. It is not deleted.

---

## Manual publish (fallback)

If the GitHub Actions workflow fails:

```bash
uv build
pip install twine
twine upload dist/*
```

You will need an API token from pypi.org for this path. Generate one at **Account settings → API tokens**.
