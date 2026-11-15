# BRIDGE patch handoff and regression resolution — 2026-11-15

The operational source patch originated at local commit `4b2e9d1c735615bb2a4ef1c79be26e208a3bec84`, parent `7b5e644e0c943f8da7cb2d66d02eb09b4645591f`.

A direct Git push failed because the execution host has no GitHub Git authentication. The connected GitHub API registered the identical tree as commit `c7594897b28586f674791975b65a732eb86327b7` on `bridge-operational-integrity-20261115`. Both trees are `63847bd933e021303ffa96792ccd6be3e0c5b62e`. The remote commit has different commit metadata and therefore a different SHA; it is not the original SHA in remote ancestry. The exact original commit is retained in `original-4b2e9d1.bundle`, with its base commit prerequisite, and its diff is in `operational.patch`.

## Operational patch

Changed files: `bridge_pipeline/audit_v5.py`, `bridge_pipeline/export_reads.py`, `bridge_pipeline/run.py`, `tests/test_operational_integrity.py`, `tests/test_export_reads.py`.

Eight lineage tests and six export tests passed; output is preserved in `operational_tests_14.txt`. Scoring formulas, weights, grade thresholds and publication policy did not change. Live DB performance and full production export remain unverified.

## Four pre-existing regression failures

| Test | Original error | Cause | Minimal resolution |
|---|---|---|---|
| `test_footer_copy.FooterCopyContractTests.test_all_public_pages_use_the_fixed_footer_copy` | `AssertionError: 27 not greater than or equal to 28` | A legacy footer marker count was treated as full page coverage after V2 home adopted a different footer. | Keep canonical copy checks for all matched legacy footers; require specific sector/trust/methodology/service surfaces; additionally verify operator, legal notice, contact route and V2 footer on all three home variants. No count threshold reduction. |
| `node tests/test_presentation.js`, mobile visual contract | `index must request the current mobile visual layer` | Expected `style.css?v=20261102-mobile5` on a home that now loads V2 stylesheets. | Preserve legacy CSS checks; require V2 home assets to be versioned and exist; check V2 mobile breakpoint, menu and stacked hero. |
| `node tests/test_intelligence.js`, service-builder contract | `missing subscription overview: briefing` | Retired four-tab/six-step markup was checked against the shipped two-entry/four-step builder. The old language-array and `showOverview` checks were also obsolete. | Require BASIC/comparison entry routes, mount points and all four steps. Execute the shipped builder functions to verify BASIC=1, comparison=3, duplicate and partial selection rejection, delivery modes and Korean/English controls. No product flow changes. |
| `node tests/test_briefing.js`, briefing cache assertion | `briefing sample cache must be current` | Expected old `20261103-fixed-samples1`, while current HTML and `tools/apply_brand_shell.py` use `20261115-07`. | Align only the stale test cache key with the existing release. Retain PDF, stage, date, ID and score integrity assertions. |

## Validation

- Python `unittest discover -s tests -p 'test_*.py'`: 162/162 passed.
- Existing Node suites: presentation, intelligence and briefing passed.
- Added service-builder runtime suite: passed.
- Legacy engine3 suite: 7/7 passed.
- Negative mutation checks: removing the V2 stylesheet, making the briefing cache stale, deleting the BASIC entry and disabling duplicate rejection each made the appropriate test fail (4/4 detected). Mutations were made only in temporary copies.
- `git diff --check`: passed.

These are offline integration/regression checks, including shipped JavaScript execution and existing repeated-build composition tests. They do not assert production REST performance, browser/device coverage or a successful live publication.

## Protected scope and integration approvals

No DB writes, rescoring, publication, main merge, Cloudflare deployment or manual workflow dispatch was performed. No file on `bridge-positioning-20261115` was edited. The regression branch changes only tests and these handoff records; production site code and data are unchanged relative to the operational patch.

Before integration: review the two branches against the positioning branch, confirm the expected UI contract, run a production-read-only dry-run export on fixed input, and verify the candidate publication revision. Main integration, any DB publication state change and actual deployment still require separate approval. Do not treat passing offline tests as deployment authorization.

For code rollback after a future merge, revert the corresponding integration commit. That does not restore DB publication state; no DB mutation occurred in this handoff.
