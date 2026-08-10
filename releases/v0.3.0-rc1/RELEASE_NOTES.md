# Construction Cost Intelligence v0.3.0-rc1

Release candidate implementing the frozen Architecture v1.0 as a Local-first WebUI.

## WebUI

- Project lifecycle dashboard with 16 frozen cost-control stages.
- 0号台账 workbench: construction drawing quantity is the baseline quantity; award BOQ quantity is reference; award BOQ unit price is the baseline price.
- BOQ / drawing / quantity workspace.
- Internal commercial workspace protected by backend role checks.
- Change / claim, process control, settlement / pre-audit, Evidence, Rules and Tasks views.
- Right-side Agent Workflow projection showing execution results and Audit Trail, not hidden model reasoning.
- Mobile evidence intake remains available at `/mobile`.

## Architecture boundaries

- Architecture v1.0 remains frozen.
- No P09 was added.
- WebUI is a projection over the same Capability Gateway and Core data.
- Plugins do not write directly around Core governance.
- Immutable Source + SHA-256 provenance remains the evidence foundation.

## Validation

- pytest: 12/12 passed.
- Python compile: passed.
- `/api/health`: passed.
- `/`: WebUI startup: passed.
- `/docs`: Swagger startup: passed.

## Artifact

`construction-cost-intelligence-v0.3.0-rc1-webui.zip`

SHA-256: `ff0ad6e319d2005fe6dff250739717596f29bac27fb7a233cab054950c1e429a`

The archive excludes runtime databases, uploaded evidence and Python caches.
