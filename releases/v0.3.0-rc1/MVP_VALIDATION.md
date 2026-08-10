# v0.3.0-rc1 MVP Validation

Status: **PASS — 16/16 critical-path validations closed**

Architecture: **v1.0 frozen**

## Validated critical path

1. Award BOQ import — PASS
2. Construction drawing baseline — PASS
3. 0号台账 — PASS
4. 清标 SAME / SIMILAR / MISSING — PASS
5. BOQ notes + departmental Evidence responsibility — PASS
6. Cost planning — PASS
7. Drawing vs quota resource control line — PASS
8. Market-price / profit forecast — PASS
9. Change / variation workflow — PASS
10. Evidence full-type closure — PASS
11. Material test batch weekly + monthly + final reconciliation — PASS
12. Major change independent dossier — PASS
13. Monthly cost snapshot + declaration + briefing + signatures — PASS
14. Settlement pre-audit — PASS
15. Cross-department permission matrix — PASS
16. Agent workflow trace + provenance drill-down — PASS

## Permission boundary

- Commercial-confidential capabilities: project manager and cost lead only.
- Technical / production / measurement / laboratory / records / material / equipment departments may submit their Evidence but cannot read commercial-confidential results.
- Evidence submission remains candidate until human verification.
- Evidence verification is restricted to project manager / cost lead.
- Automatic Evidence verification is forbidden.

## Provenance invariant

Every authoritative project result must support drill-down through:

`Result -> Calculation / Decision -> Evidence / Rule -> Original Source`

Original Source identity includes immutable source metadata and SHA-256 where available.

If the original source cannot be reached, provenance outcome is `partial`; the result must not be presented as fully traceable/verified.

Agent workflow audit records preserve actor, capability/action, object, outcome/version details and timestamp. Human confirmation remains explicit where required.

## Release discipline

- No P09 introduced.
- No legacy `self_evolution*` introduced into Core.
- Core architecture remains frozen.
- MVP validation fixes were limited to closure, permissions, traceability and test coverage.
- GitHub Actions run #113 passed Compile, Test and Startup Smoke after provenance validation.

## Stabilization recommendation

Freeze `v0.3.0-rc1` feature scope. Next phase is stabilization only: defect correction, realistic project data dogfooding, performance/UX observation and release documentation. Do not add new Core capability families until evidence from actual project use justifies a versioned architecture change.
