# Contributing to verity

## Development setup

You need Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/vantage-ola/verity
cd verity
uv venv
uv pip install -e ".[dev]"
```

Verify the install:

```bash
uv run verity --help
```

## Running tests

```bash
uv run pytest
```

With coverage:

```bash
uv run pytest --cov=src/verity --cov-report=term-missing
```

The project requires **85% branch coverage** minimum. The CI gate will fail below that threshold. If you add a new module, add tests for it in the same PR.

Coverage by file:

```bash
uv run pytest --cov=src/verity --cov-report=html
open htmlcov/index.html
```

## Project layout

```
src/verity/
  models.py       — pydantic models (Feature, Claim, Test, Evidence, Release, Registry)
  registry.py     — load / save / canonical JSON
  validate.py     — guards: broken links, duplicates, status consistency
  release.py      — fail-closed release creation
  backends.py     — StorageBackend protocol
  walrus.py       — Walrus HTTP backend
  memwal.py       — MemWal SDK backend
  session.py      — VeritySession high-level API
  cli/main.py     — typer CLI entry point

tests/
  conftest.py     — shared fixtures
  test_models.py  — pydantic model validation
  test_validate.py — guard tests
  test_release.py  — release logic
  test_registry.py — load/save/canonical JSON
  test_session.py  — VeritySession API
  test_walrus.py   — WalrusBackend (mocked httpx)
  test_memwal.py   — MemWalBackend (mocked SDK)
  test_cli.py      — CLI end-to-end (typer CliRunner)
```

## Making changes

### Changing models

All five entity types live in `src/verity/models.py`. ID prefix constraints are enforced at the model level via `@field_validator`. If you add a new entity:

1. Add the model with `ConfigDict(extra="forbid")` and a prefix validator.
2. Add it to `Registry`.
3. Add duplicate-ID and broken-link checks in `validate.py`.
4. Export it from `src/verity/__init__.py`.
5. Add tests in `test_models.py` and `test_validate.py`.

### Changing the CLI

The CLI lives in `src/verity/cli/main.py`. Mutating commands follow this pattern:

```python
registry = load_registry(directory)
# mutate registry
errors = validate(registry)
if errors:
    for e in errors:
        typer.echo(e, err=True)
    raise typer.Exit(1)
save_registry(registry, directory)
```

Test changes with `typer.testing.CliRunner`:

```python
from typer.testing import CliRunner
from verity.cli.main import app

runner = CliRunner()
result = runner.invoke(app, ["init"])
assert result.exit_code == 0
```

### Adding a storage backend

Implement the `StorageBackend` protocol in `src/verity/backends.py`:

```python
class StorageBackend(Protocol):
    def store(self, content: bytes) -> str: ...
    def fetch(self, key: str) -> bytes: ...
```

Add the backend under `src/verity/`. Update:
- `src/verity/__init__.py` — export it
- `src/verity/cli/main.py` — add to the `BackendChoice` enum and `_get_backend()`
- `tests/` — add a test file for it

### Canonical JSON

The wire format for all push/pull is canonical JSON:

```python
json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
```

No trailing newline. This ensures identical content produces identical Walrus blob IDs. Never use `json.dumps` with default settings anywhere in the storage path.

## Code style

- No type: ignore comments unless genuinely unavoidable.
- No default comments that describe *what* code does — only *why* when it would surprise a reader.
- Pydantic models use `ConfigDict(extra="forbid")`.
- Errors raised from library code use `VerityError` subclasses. CLI commands use `typer.Exit`.

## Release process

1. **Bump the version** in `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```

2. **Update CHANGELOG.md** — add a new `## [0.2.0]` section with the date and a bulleted list of changes.

3. **Commit**:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "release: 0.2.0"
   ```

4. **Tag and push**:
   ```bash
   git tag v0.2.0
   git push origin main --tags
   ```

5. The `publish.yml` workflow triggers automatically on the `v*` tag. It builds the distribution, publishes to PyPI via OIDC trusted publishing, and creates a GitHub release with the dist artifacts attached.

### First-time PyPI setup (one-time)

You need to configure PyPI trusted publishing before the workflow can push packages:

1. Go to [pypi.org/manage/account/publishing](https://pypi.org/manage/account/publishing/).
2. Add a new trusted publisher:
   - **Owner**: `vantage-ola`
   - **Repository**: `verity`
   - **Workflow**: `publish.yml`
   - **Environment**: `pypi`
3. Create an environment named `pypi` in the GitHub repo settings with no extra protection rules (or add required reviewers if you want manual approval).

No API tokens needed — GitHub Actions authenticates via OIDC.

## CI

Every push to `main` and every PR runs:
- Python 3.11, 3.12, and 3.13
- `uv run pytest --cov=src/verity --cov-report=xml --cov-report=term-missing`
- Coverage upload to Codecov (3.12 only)

The test run fails if coverage drops below 85%. Fix coverage before merging.
