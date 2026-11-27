# BRIDGE Stability 1.0 — Phase 1: Prepublication integrity
**Date:** 2026-11-27  
**Status:** change proposal; production rollout requires tests and successful merge.

## Problem and incident
On 2026-11-26/27, four-domain DB rankings were marked published before the
public export rejected duplicate UNI T100 ranks. Consequently the previous
2026-11-25 public JSON stayed visible even though newer stored data existed.
Separately, Google News RSS returned HTTP 429/503 and interrupted collection.
A later evidence-only recovery produced 2026-11-27 JSON (400 rows), and PR #15
removed the competition-rank collision.

## Phase 1 contract
- Before **any** daily `published_at` writes, independently read and verify
  the entire current-date T100 cohort for CPR / STAR(ENT) / GOV / UNI.
- Require exactly 100 per domain, 400 total, unique 1..100 ranks, distinct
  entity IDs, legal finite scores, descending score order, and exact
  authoritative score/trust-grade matches from `bridge_scores`.
- Require exactly 400 current-date `bridge_index_metrics` entities.
- All reads are date- and methodology-scoped; no invented scores or values.
- Failed precheck blocks publication before mutations, retaining the previous
  exported file. Errors are visible in GitHub Actions rather than hidden.
- Regression tests include same-score UNI rank collision, missing rows,
  mismatched trust grade, missing metrics, and rank/score inversion.
- The daily production preflight and PR QA include the new tests.

## Boundaries and unresolved work
This phase does NOT alter the six-axis scoring formula, evidence ledger,
previously published JSON, UI, or report generation. It does NOT yet make the
two DB UPDATE operations atomic, introduce per-domain partial publication,
guarantee Google News RSS availability, or prove Cloudflare live deployment.
External source HTTP 503 remains an independent error requiring Stage 2
collector isolation/circuit-breaker work without treating failures as zero
evidence.

## Rollout and verification
1. Run offline GitHub Actions QA (no production credentials).
2. Merge to main only if checks pass.
3. On the next scheduled daily run, require prepublication PASS, export 400,
   source/date/axis/trust verification, and Cloudflare live verification.
4. If any gate fails, keep the last valid file and investigate the blocking
   diagnostic; never edit the public date or fabricate missing observations.

## Stage 2 and Stage 3
- Stage 2: isolate provider retries / collection checkpoints and review
  rate-limit policy while preserving failed-source status.
- Stage 3: transactional snapshot promotion, independently verified release
  units, 7-day observation period, 30-day SLO measurements and alert routing.

## Reference
GitHub repository: thefruitgrove/bridgebrand; production data contract
`docs/BRIDGE_BRIEFING_STANDARD.md` and prior incident evidence in
`docs/BRIDGE_20261117_COLLECTOR_INCIDENT_AND_RECOVERY.md`.
