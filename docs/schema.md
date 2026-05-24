# Schema Reference

## `verity.json`

Everything lives in a single file. Keys are always sorted; format is compact canonical JSON (deterministic, safe to hash).

```json
{
  "schema_version": "0.1.0",
  "repo_id": "repo:my-project",
  "context": [...],
  "features": [...],
  "claims": [...],
  "tests": [...],
  "evidence": [...],
  "releases": [...],
  "pushes": [...]
}
```

---

## ID prefixes

ID prefixes are enforced at the model level — wrong prefix → validation error.

| Entity | Prefix | Example |
|---|---|---|
| Feature | `feat:` | `feat:auth`, `feat:supplier.quality` |
| Claim | `clm:` | `clm:auth.t1`, `clm:auth.login` |
| Test | `tst:` | `tst:auth.unit`, `tst:auth.integration` |
| Evidence | `evd:` | `evd:auth.ci`, `evd:auth.run1` |
| Release | `rel:` | `rel:0.1.0`, `rel:1.0.0` |

Recommended convention: `<namespace>.<entity>.<qualifier>` — e.g. `clm:auth.login.t1`.

---

## Entity fields

### ContextEntry

Named narrative note attached to the registry. Context entries are free-form and travel with the proof chain. They are stored in MemWal automatically when pushing via `verity push --backend memwal`.

```json
{
  "key": "architecture",
  "value": "5-layer proof chain: feature → claim → test → evidence → release"
}
```

| Field | Type | Notes |
|---|---|---|
| `key` | string | Unique name for this entry (no prefix enforced) |
| `value` | string | Free-form narrative text |

Manage via `verity context set/list/remove` or `VeritySession.set_context()`.

---

### Feature

```json
{
  "id": "feat:auth",
  "title": "User authentication",
  "status": "active"
}
```

| Field | Type | Allowed values |
|---|---|---|
| `id` | string | must start with `feat:` |
| `title` | string | free text |
| `status` | string | `active`, `deprecated`, `retired` |

---

### Claim

```json
{
  "id": "clm:auth.t1",
  "feature_id": "feat:auth",
  "title": "Login succeeds",
  "tier": "T1",
  "status": "open"
}
```

| Field | Type | Allowed values |
|---|---|---|
| `id` | string | must start with `clm:` |
| `feature_id` | string | must reference an existing `feat:` ID |
| `title` | string | free text |
| `tier` | string | `T1`, `T2`, `T3` |
| `status` | string | `open`, `verified`, `rejected` |

---

### Test

```json
{
  "id": "tst:auth.unit",
  "claim_id": "clm:auth.t1",
  "kind": "unit",
  "path": "tests/test_auth.py",
  "status": "pending"
}
```

| Field | Type | Allowed values |
|---|---|---|
| `id` | string | must start with `tst:` |
| `claim_id` | string | must reference an existing `clm:` ID |
| `kind` | string | `unit`, `integration` |
| `path` | string | path to the test file |
| `status` | string | `pending`, `passing`, `failing` |

---

### Evidence

```json
{
  "id": "evd:auth.run1",
  "test_id": "tst:auth.unit",
  "kind": "test_run",
  "artifact_path": "artifacts/run1.json",
  "status": "collected"
}
```

| Field | Type | Allowed values |
|---|---|---|
| `id` | string | must start with `evd:` |
| `test_id` | string | must reference an existing `tst:` ID |
| `kind` | string | `test_run` |
| `artifact_path` | string | path to the artifact |
| `status` | string | `collected`, `passed`, `failed` |

---

### Release

```json
{
  "id": "rel:1.0.0",
  "version": "1.0.0",
  "timestamp": "2025-01-15T10:30:00Z",
  "walrus_blob_id": "AbCdEfGhIjKlMnOpQrStUvWxYz...",
  "claim_ids": ["clm:auth.t1", "clm:auth.t2"]
}
```

| Field | Type | Notes |
|---|---|---|
| `id` | string | must start with `rel:` |
| `version` | string | semver recommended |
| `timestamp` | string | ISO 8601 UTC |
| `walrus_blob_id` | string \| null | null until `verity push` |
| `claim_ids` | list[string] | all verified claims included at release time |

---

### PushRecord

Appended to the `pushes` list on every `verity push`.

```json
{
  "blob_id": "AbCdEfGhIjKlMnOpQrStUvWxYz...",
  "timestamp": "2025-01-15T10:30:00Z",
  "backend": "walrus"
}
```

| Field | Type | Allowed values |
|---|---|---|
| `blob_id` | string | Walrus blob ID |
| `timestamp` | string | ISO 8601 UTC |
| `backend` | string | `walrus`, `memwal` |

---

## Claim tiers

| Tier | Meaning |
|---|---|
| `T1` | Direct verification — unit tests, direct assertions |
| `T2` | Indirect verification — integration tests, logs |
| `T3` | Circumstantial — documentation, review sign-offs |

---

## Validation rules

`verity validate` (and `VeritySession.validate()`) enforces:

1. No duplicate IDs within any entity family
2. Every `claim.feature_id` references an existing feature
3. Every `test.claim_id` references an existing claim
4. Every `evidence.test_id` references an existing test
5. Every `release.claim_id` references an existing claim
6. Every claim with `status="verified"` has at least one linked test
7. Every test with `status="passing"` has at least one linked evidence

## Release guards

`verity release` is fail-closed and additionally requires:

- At least one `verified` claim exists
- Every `verified` claim has a linked test with `status="passing"`
- Every such `passing` test has at least one linked evidence with `status="passed"`

If any of these fail, the release is aborted entirely — no partial state is written.
