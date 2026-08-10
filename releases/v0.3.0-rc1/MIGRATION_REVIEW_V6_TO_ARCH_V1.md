# Migration Review: legacy Cost Agent v6 -> Construction Cost Intelligence Architecture v1.0

Status: APPROVED WITH ISOLATION

## Goal
Reuse validated domain assets from the legacy `cost-agent` repository without importing the legacy architecture into the frozen Architecture v1.0.

## Decision matrix

| Legacy asset | Decision | New home | Rule |
|---|---|---|---|
| `data/quotas/*.json` | REUSE | P08 Rule Pack data source | Treat as immutable/reference data; add source/version/region metadata before formal use |
| `calculators/quota_loader.py` | ADAPT | Rule/Quota Adapter | No direct DB writes; expose through Capability Gateway |
| `calculators/material_prices.py` | ADAPT | P04 Market Price Adapter | Market price is forecast/reference data only; preserve time/region/source |
| `calculators/historical_data.py` | ADAPT | P04 Historical Cost Adapter | Read-only input to forecast; never overwrite actual/project facts |
| `calculators/cost.py` / `quota_database.py` | DISTILL | P04 Skill / P08 Rule support | Reuse algorithms only after formula/rule trace review; no duplicate pricing authority |
| `knowledge/matcher.py` | DISTILL | P02/P08 matching Skill | Advisory candidate matching only; cannot create VERIFIED decisions |
| `knowledge/semantic_search.py` | DISTILL | Search Skill | Search/ranking only; not a fact source |
| `knowledge/knowledge_graph.py` | PARTIAL REUSE | Derived index / search projection | Do not create a second project truth graph; Core Object/Relation remains authoritative |
| `knowledge/recommendation.py` | DISTILL | Recommendation Skill | Output must remain RECOMMENDATION, never VERIFIED |
| `knowledge/incremental_update.py` | REJECT AS CORE | Optional Rule Pack maintenance tool | Updates require versioning, impact analysis and human approval |
| `cost_tracking/self_evolution*.py` | ARCHIVE | Legacy archive only | Do not import autonomous self-evolution into frozen Core |
| `change_order/SKILL.md` | DISTILL | P05 Change Skill | Map to existing Change Event workflow |
| `change_order/templates/*` | REUSE AS TEMPLATE | P05/P07 Derived Artifact templates | Templates are not evidence or fact sources |
| project-specific change-order documents | QUARANTINE | Example/private project source only | Must not become universal rules without applicability review |
| legacy `api/` | ARCHIVE / selectively adapt endpoints | Adapter layer | Current Capability Gateway/API remains authoritative |
| legacy `web/` | ARCHIVE | UI reference only | Current Local-first WebUI remains authoritative |

## Mandatory migration gates

1. **No Core import**: legacy modules cannot add new Core objects or bypass Capability Gateway.
2. **One truth source**: quota, material price, evidence and project facts are referenced once and reused; no copied shadow databases.
3. **Rule trace required**: quota/price calculations must identify source, version, region, effective time and formula.
4. **Advisory AI only**: semantic matching/recommendation produces OBSERVATION/HYPOTHESIS/RECOMMENDATION states, never VERIFIED by itself.
5. **No autonomous evolution**: legacy self-evolution components are archived unless later reintroduced as controlled, review-gated tooling outside Core.
6. **Project-specific documents stay scoped**: local project rules/templates cannot silently become national/default rules.
7. **Tests before promotion**: every migrated adapter/skill needs unit, permission, provenance and regression tests before merge.

## Migration order

1. Quota Rule Pack Adapter (`data/quotas` + `quota_loader`)
2. Material Price Adapter (`material_prices`)
3. Matching/Search Skills (`matcher`, `semantic_search`)
4. Change/Evidence templates
5. Historical cost adapter
6. Review whether any remaining legacy calculation code adds unique value

## Explicit non-goals

- Do not merge legacy autonomous self-evolution into Core.
- Do not replace the frozen P01-P08 plugin boundaries.
- Do not restore the old Web/API as a second application surface.
- Do not copy project-specific rules into global rule packs without provenance/applicability checks.

## Release recommendation

Keep PR #1 as a release-candidate integration PR. Migrate assets in the order above through separate commits/PRs or clearly isolated commits, with the Architecture v1.0 test suite green after every step.
