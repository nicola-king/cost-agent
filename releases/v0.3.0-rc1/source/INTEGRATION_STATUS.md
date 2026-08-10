# Integration status

Architecture v1.0 remains frozen. Legacy assets are being migrated one capability at a time through adapters/skills.

## Completed

### 1. Quota Rule Pack Adapter
- Read-only adapter for the legacy `data/quotas/*.json` rule pack.
- Capabilities: `p08.quota_search`, `p08.quota_get`, `p08.quota_stats`.
- Rule-pack files are never mutated.
- Regression after migration: 15/15 passed.

### 2. Material Price Adapter
- Read-only material price source adapter.
- Capability: `p04.material_price_search`.
- A price is treated as verified context only when source + month + region are present.
- Legacy hard-coded fallback prices are not promoted as market facts.
- Regression after migration: 18/18 passed.

## Next

3. Matching/Search Skills (`knowledge/matcher.py`, `knowledge/semantic_search.py`) as advisory candidate ranking only.
4. Change/Evidence templates.
5. Historical Cost Adapter.

No legacy self-evolution component is allowed into Core.
