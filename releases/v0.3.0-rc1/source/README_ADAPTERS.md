# Migrated legacy adapters

Architecture v1.0 remains frozen. These adapters reuse legacy domain assets through the Capability Gateway without importing the legacy architecture.

## Quota Rule Pack

Set `CCI_QUOTA_DATA_DIR` to the legacy `cost-agent/data/quotas` directory or a separately versioned quota rule-pack directory.

Registered capabilities:

- `p08.quota_search`
- `p08.quota_get`
- `p08.quota_stats`

The adapter is read-only and never mutates quota JSON files.

## Material price source

Set `CCI_MATERIAL_PRICE_FILE` to a normalized material-price JSON source.

Registered capability:

- `p04.material_price_search`

Only rows carrying source + month + region are treated as verified price context. Legacy hard-coded fallback prices are not promoted as market facts.

## Validation

Current local regression result after both migrations: `18 passed`.
