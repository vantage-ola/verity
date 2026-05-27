# verity — Agent System Prompt

You have access to **verity**, a proof-chain registry for AI agents backed by Walrus decentralised storage.

## What it does

verity tracks five entity types — Feature, Claim, Test, Evidence, Release — as a structured JSON registry (`verity.json`). Claims must be backed by tests; tests must be backed by evidence. Releases are fail-closed: all verified claims need passed evidence or the release is rejected. The registry can be pushed to Walrus and pulled by any other agent using a `blob_id`.

## Install

```
pip install walrus-verity
```

## CLI

```bash
verity init                                             # create verity.json
verity add feature  feat:<id> "<title>"
verity add claim    clm:<id>  "<title>" --feature feat:<id> --tier T1
verity add test     tst:<id>  "<title>" --claim   clm:<id>  --kind unit --path <path>
verity add evidence evd:<id>  "<title>" --test    tst:<id>  --artifact <path> --status passed
verity validate                                         # print errors or OK
verity release <semver>                                 # fail-closed release
verity push                                             # returns blob_id
verity pull <blob_id>                                   # restore from Walrus
verity log                                              # push history
```

## Python API

```python
from verity import VeritySession, WalrusBackend

s = VeritySession("verity.json", backend=WalrusBackend())
s.init(repo_id="repo:my-project")
s.add_feature("feat:auth", "User auth")
s.add_claim("clm:auth.t1", "Login works", feature_id="feat:auth", tier="T1", status="verified")
s.add_test("tst:auth.unit", claim_id="clm:auth.t1", kind="unit", path="tests/test_auth.py", status="passing")
s.add_evidence("evd:auth.ci", test_id="tst:auth.unit", artifact_path="reports/auth.json", status="passed")

errors = s.validate()          # [] = clean
rel    = s.release("1.0.0")   # VerityReleaseError if guards fail
blob_id = s.push()            # publish to Walrus, returns blob_id

# Another agent continues:
s2 = VeritySession("audit.json", backend=WalrusBackend())
s2.pull(blob_id)              # restore full chain
s2.release("1.1.0")
s2.push()
```

## Rules

- **Update `verity.json` after every feature, fix, or code change.** Add the relevant `feat:` / `clm:` / `tst:` / `evd:` entries. The proof chain must stay in sync with the repo.
- ID prefixes are enforced: `feat:`, `clm:`, `tst:`, `evd:`, `rel:`
- Always `validate()` before `release()`
- `release()` raises `VerityReleaseError` if any verified claim lacks a passing test with passed evidence
- `push()` raises `VerityPushError` if no backend is configured
- `blob_id` is the handoff token between agents
- After `pull()`, validate before extending the chain

## Statuses

| Entity   | Valid statuses |
|----------|---------------|
| Feature  | active, deprecated, retired |
| Claim    | open, verified, rejected |
| Test     | pending, passing, failing |
| Evidence | collected, passed, failed |

## Errors

`VerityReleaseError`, `VerityPushError`, `WalrusError`, `MemWalError` — all inherit from `VerityError`.
