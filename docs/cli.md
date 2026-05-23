# CLI Reference

## `verity init`

Create `verity.json` in the current directory (or a target directory). Fails if the file already exists.

```bash
verity init
verity init /path/to/project --repo-id repo:my-app
```

| Argument / Option | Default | Description |
|---|---|---|
| `DIRECTORY` | `.` | Where to create `verity.json` |
| `--repo-id` | `repo:default` | Registry identifier |

---

## `verity add`

Add an entity to the registry. All IDs must carry the correct prefix.

### `verity add feature`

```bash
verity add feature ID TITLE [--status active|deprecated|retired]
```

```bash
verity add feature feat:auth "User authentication"
```

### `verity add claim`

```bash
verity add claim ID TITLE --feature FEAT_ID [--tier T1|T2|T3] [--status open|verified|rejected]
```

```bash
verity add claim clm:auth.t1 "Login succeeds" --feature feat:auth
verity add claim clm:auth.t2 "Session expires" --feature feat:auth --tier T2
```

### `verity add test`

```bash
verity add test ID TITLE --claim CLM_ID [--kind unit|integration] [--path PATH] [--status pending|passing|failing]
```

```bash
verity add test tst:auth.unit "Login unit test" --claim clm:auth.t1 --kind unit --path tests/test_auth.py
```

### `verity add evidence`

```bash
verity add evidence ID TITLE --test TST_ID [--artifact PATH] [--status passed|failed|collected]
```

```bash
verity add evidence evd:auth.run1 "CI run #1" --test tst:auth.unit --artifact artifacts/run1.json --status passed
```

---

## `verity validate`

Check all links, required fields, and status consistency. Exits non-zero if any error is found.

```bash
verity validate
# OK
# or:
#   clm:auth.t1 references unknown feature feat:missing
#   1 error(s) found.
```

Checks performed:
- Broken links (claim→feature, test→claim, evidence→test, release→claim)
- Duplicate IDs within each entity type
- Verified claims must have at least one linked test
- Passing tests must have at least one linked evidence

---

## `verity release`

Create a named release snapshot. **Fail-closed**: every verified claim must have a passing test with passed evidence, or the command aborts.

```bash
verity release VERSION [--dir DIRECTORY]
```

```bash
verity release 1.0.0
# Released rel:1.0.0 — 3 claim(s)
```

---

## `verity push`

Serialize the registry to canonical JSON and upload to Walrus (or MemWal). Records the blob ID in the push log.

```bash
verity push [--epochs N] [--backend walrus|memwal] [--dir DIRECTORY]
```

| Option | Default | Description |
|---|---|---|
| `--epochs` | `5` | Walrus storage duration in epochs |
| `--backend` | `walrus` | Storage backend |

```bash
verity push
# blob: AbCdEfGhIjKlMnOpQrStUvWxYz…

verity push --epochs 10
verity push --backend memwal
```

---

## `verity pull`

Fetch a registry blob by ID and write it to `verity.json`.

```bash
verity pull BLOB_ID [--backend walrus|memwal] [--dir DIRECTORY]
```

```bash
verity pull AbCdEfGhIjKlMnOpQrStUvWxYz…
# Restored registry from AbCdEfGhIjKlMnOpQrStUvWxYz…
#   3 feature(s), 5 claim(s), 1 release(s)
```

---

## `verity log`

Print all push operations recorded in the registry.

```bash
verity log [--dir DIRECTORY]
# 1.  [walrus]  2025-01-15T10:30:00Z  AbCdEfGhIjKlMnOpQrStUvWxYz…
# 2.  [walrus]  2025-01-16T09:15:00Z  XyZaBcDeFgHiJkLmNoPqRsTuVw…
```
