# BRIDGE Stability 1.0 — Phase 4: Evidence-based seven-day operating audit
**Issued:** 2026-11-27  
**Monitoring start (KST):** 2026-11-28  
**Initial seven-day window:** 2026-11-28–2026-12-04

## Scope and why
Phase 1 blocked invalid daily publication before DB mutations. Phase 2 isolated
provider errors and implemented scope-verified resume of successful news target
scans. Phase 3 introduced a single-transaction daily DB publication RPC and
GitHub live-verification incident alerts.

The next requirement is not merely another successful unit test. BRIDGE must
prove seven different **real** operating dates, without relabeling old releases
or treating a recovery as a clean initial collector run.

## Actual automated work (read-only)
A new workflow `.github/workflows/bridge-7day-reliability.yml` runs at
**09:30 KST daily** (after scheduled source collection, evidence-only recovery,
fallback and the 08:30 live verification). A manual `workflow_dispatch` is
also available for immediate diagnostic checks; manual test runs do not
fabricate other dates' observation records.

The monitor reads:
- GitHub checked-out `site/data/latest.json`: KST observation date, 400
  records and publication metadata;
- live Cloudflare `https://bridgebrand.co.kr/data/latest.json` and
  `this-week.html`: official deployed date, published status, 400 records,
  matching snapshot ID and visible date;
- production Supabase DB **read-only** through existing
  `tools.verify_export_file` and the established service secret;
- GitHub Actions runs of daily pipeline, recovery and this reliability monitor.
  Only completed main-branch `schedule`/`workflow_dispatch` runs count.

A per-run JSON report is uploaded as a GitHub Actions artifact, retained for
30 days, and summarized in the workflow's job summary. It does not contain
private DB rows, secret values or raw source material.

## Date classification
| State | Definition |
|---|---|
| healthy | Today's GitHub+live+DB verification passes, and primary daily pipeline has a completed success with no recorded failed run that day |
| degraded | Today's 400-record publication is verified, but normal daily collection did not produce an unbroken clean production record (e.g. required recovery after a failure) |
| failure | Missing/stale live data, DB mismatch, wrong date, failed monitoring or no verifiable public release |
| not_observed | Historical day has no successful/failing monitor-run evidence; never impute success |
| not_started | Before 2026-11-28 |

A historical day may be credited ONLY after a completed monitor job from that
**same day**; current live status cannot retrospectively prove historical
Cloudflare health. Historical primary failures remain visible even when
delivery was recovered.

Two distinct metrics are reported:
- **Delivered days:** healthy + degraded; real availability outcome.
- **Clean days:** healthy only; normal collection and publication performance.

**7/7 delivered** and **7/7 clean** are independent gates. The complete seven
days must be observed; six successes plus one missing day are not 7/7.

## Incident detection and response
The 09:30 monitor creates/updates one GitHub Issue for a failed or degraded day.
The Issue links to the particular workflow and the diagnostic artifact and
contains no raw internal evidence. On a later **clean** day the issue is
closed after a recovery comment. GitHub Issue notification delivery depends on
the user's own GitHub notification/subscription settings; this is not an SMS,
email or chat push guarantee.

On failure, determine the stage first: external RSS, DART/official,
`healthcheck`, atomic promotion, versioned JSON export, Cloudflare, or
GitHub Actions schedule/permissions. A normal release cannot be marked success
until `asOfDate`, 400 rows, rank/score/trust, and live publication agree.

## Constraints
- No production score reprocessing, database schema change, Cloudflare config
  change, manual publication or fake dates in Phase 4.
- The monitor uses the existing read-only source checks and a service secret
  securely injected by GitHub; never log secrets.
- A missing scheduled monitoring workflow stays `not_observed`: no hidden
  gap-filling. GitHub Actions scheduling can be delayed.
- 30-day reliability/SLO rates need 30 real monitored dates. The first seven-day
  result cannot be known on 2026-11-27 and is not claimed.
- Monitoring is independent of GitHub's pipeline status: a successful CI/QA
  workflow on a feature branch does not establish successful daily operation.

## Verification and next gating decision
1. Offline tests must pass in GitHub Actions before merge.
2. Confirm the scheduled workflow appears on main; make no changes to existing
   05:15/06:45/07:15/08:30 workflows.
3. From 2026-11-28, inspect the archived report and deduplicated Issue daily.
4. The initial 7-day certificate is eligible no earlier than **2026-12-04**,
   and only if each of the seven dated reports exists and passes.
5. Review observed collector rate limits, errors, stage runtimes and
   recovered-versus-clean days before revising alert thresholds or targets.
