# Construction Cost Intelligence v0.3.0-rc1

## Status
Release Candidate — MVP critical-path validation complete (16/16).

## Architecture
Architecture v1.0 remains frozen. No P09 was introduced and legacy `self_evolution*` code was not brought into Core.

## Validated business closure

- Award BOQ import and construction-drawing quantity baseline
- 0号台账 with drawing quantity as baseline and award BOQ quantity as reference
- BOQ clearing: SAME / SIMILAR / MISSING
- BOQ Evidence plans with department, individual responsibility and deadlines
- Cost planning: labor / material / equipment / measures / management / fees / tax
- Drawing-demand vs quota-consumption lower-value resource control line
- Market-price context requiring source + region + month before profit forecasting
- Change / variation / claim workflow with human pricing approval
- Evidence closure for photo, video, measurement, laboratory, hidden works, material and machinery records
- Weekly + monthly material test-batch checks and final as-built reconciliation (coverage >= final quantity and <= 105%)
- Major-change independent dossier gate
- Monthly cost snapshot, declaration, cost briefing and individual signatures
- Settlement pre-audit gate
- Cross-department permission matrix
- Agent workflow audit and provenance drill-down

## Security / governance boundaries

Commercial-confidential capabilities are backend-gated to project manager and cost lead. Operational departments may submit Evidence but cannot access project cost/profit outputs. Evidence remains candidate until explicitly verified by project manager or cost lead; automatic verification is disabled.

## Provenance

Authoritative results are expected to support:

`Result -> Calculation / Decision -> Evidence / Rule -> Original Source`

Original Source records preserve immutable identity and SHA-256 where available. Missing original-source lineage produces `partial`, not a false fully-verified trace.

## Validation evidence

GitHub Actions run #113 passed Compile, Test and Startup Smoke after the final provenance tests. The detailed baseline is in `MVP_VALIDATION.md` and GitHub Issue #2.

## Next phase

Feature scope is frozen for RC1. Proceed with stabilization and realistic-project dogfooding only: defect fixes, performance/UX observation, documentation and release packaging. Core expansion requires evidence from actual project use and a versioned architecture decision.
