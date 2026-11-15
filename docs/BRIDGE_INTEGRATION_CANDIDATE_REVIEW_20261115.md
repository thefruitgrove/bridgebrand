# BRIDGE Integrated Review Candidate — 2026-11-15

## Changes combined without touching main
Base: `bridge-regression-resolution-20261115` (includes operational patch and test corrections).
Overlay: `bridge-positioning-20261115` (positioning, public methodology, WHAT/WHY/WHAT NEXT, briefing evidence UI, source documentation and tests).
Candidate: `bridge-integration-candidate-20261115`.

## Source comparison and conflicts
- Operations branch vs main: `bridge_pipeline/audit_v5.py`, `bridge_pipeline/export_reads.py`, `bridge_pipeline/run.py` + two tests.
- Regression branch adds changes only to legacy test expectations and handoff artifacts, not production site/scoring data.
- Positioning branch modifies public presentation, generated copy, briefing.js/html, SEO, and its own tests.
- **No overlapping paths** between regression/operations changed files and positioning changes. Both change sets are carried into candidate.
- One **semantic test conflict** found in `tests/test_briefing.js`: old string literal `e.axis_status[a]!=='reference'` no longer exists because valid axis now requires both status `observed/maintained` and numeric score. Updated the guard to assert the stronger current contract and preserve exclusion of reference/null values.

## Static checks completed
- All key positioning, evidence UI and protected trust strings checked in candidate.
- Candidate includes both sets of test files and operational read-only projection helper.
- Original Work regression test results (Python 162/162, Node three suites, engine 7/7, 14 operational, mutation 4/4) were executed on the **regression branch**, not the newly combined candidate.
- Candidate full tests, Python compile, browser/PDF rendering, performance and production dry-run **not yet executed**.

## High-risk unresolved gates
1. Production-read-only dry-run for `bridge_pipeline/export_reads.public_observations`, including PostgREST alias projection syntax, 57014 retry path, temporal version filtering and complete 400-row projection.
2. Verify `bridge_pipeline/audit_v5.audit` preserves existing CPR shadow panel policy while not admitting other-domain shadow, withheld or unpublishable data.
3. Confirm pipeline re-publish uses one immutable as_of_date/snapshot/methodology version; compare DB→history.json→latest.json→deployed JSON by normalized hashes before and after. Do not accept stale output.
4. Full candidate QA: Python unittest discover, `node tests/test_briefing.js`, `node tests/test_intelligence.js`, `node tests/test_presentation.js`, `node tests/test_service_builder_runtime.js`, `node tests/test_evidence_action_rules.js`, engine tests, JS syntax, all configured CI checks.
5. Verify generating the site (build.py + apply_brand_shell.py + build_spa.py + apply_brand_shell.py) does not erase positioning strings, evidence UI, V2 script cache keys, or data lineage.
6. Visual smoke on desktop/mobile and PDF BASIC / STANDARD / English; watch for PDF overflow and valid evidence dates.
7. Check 2026-11-15 missing automatic run cause independently. Main not ready until trigger history understood.
8. Review security, source rights and publication eligibility, especially CPR 31 shadow.

## Deployment lock
**Candidate is for review only.** No main merge, DB writes, re-ranking, forced publication, workflow dispatch, Cloudflare deploy or production file overwrite without explicit approval after complete proof.
Rollback after future merge cannot restore DB state by itself. Preserve original 11/13 public JSON and 11/14 DB snapshots in separate backup.

## Verified historical facts
- 11/14 DB 400 T100 with CPR 69 eligible/31 shadow per Work audit.
- Work report identifies 57014 timeout in history export and shadow lineage policy mismatch; published 11/13 frontend matches GitHub JSON.
- Both Work fixes and positioning work now appear in this isolated candidate branch.
