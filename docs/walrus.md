# Walrus Setup

verity uses the [Walrus HTTP API](https://docs.walrus.site) directly. No Sui wallet or SDK required.

## Testnet (default)

Works out of the box — no configuration needed:

```bash
verity push    # uses Walrus testnet
```

Default endpoints:
- Publisher: `https://publisher.walrus-testnet.walrus.space`
- Aggregator: `https://aggregator.walrus-testnet.walrus.space`

## Custom / mainnet

Set environment variables:

```bash
export WALRUS_PUBLISHER_URL=https://publisher.walrus.space
export WALRUS_AGGREGATOR_URL=https://aggregator.walrus.space
```

Or use `WalrusBackend` directly in Python:

```python
from verity import VeritySession, WalrusBackend

backend = WalrusBackend(
    publisher_url="https://publisher.walrus.space",
    aggregator_url="https://aggregator.walrus.space",
    epochs=10,
)
s = VeritySession("verity.json", backend=backend)
```

## Storage epochs

Walrus stores blobs for a configurable number of epochs. Default is 5.

```bash
verity push --epochs 20    # store for longer
```

One epoch on the Walrus testnet is roughly one day.

## How it works

`verity push` serialises `verity.json` to canonical JSON (sorted keys, no whitespace, no trailing newline) and sends it to the Walrus publisher via `PUT /v1/blobs?epochs=N`. The publisher returns a blob ID — a content-addressed, immutable identifier.

`verity pull <blob_id>` fetches the bytes from the aggregator via `GET /v1/blobs/<blob_id>` and deserialises them back into a `Registry`.

The same blob ID always returns the same bytes. This makes every `verity push` a tamper-evident, point-in-time snapshot.
