# BRIDGE Stability 1.0 — Phase 4 hardening (2026-11-27)

## Readiness gap
The pre-existing 08:30 live health check validated the published date, record
count, this-week page, and same-date `snapshotId`. Those metadata checks alone
cannot prove that all 400 record bodies (including per-axis provenance) have
reached the public Cloudflare site unchanged.

## New non-mutating content contract
The live verifier now checks each deployed T100 cohort independently:
- CPR, STAR/ENT, GOV, UNI: exactly 100 subjects per group;
- ordinal ranks 1..100, no duplicates;
- unique nonempty external entity IDs;
- score, trust_grade and axis_scores present;
- when GitHub and Cloudflare publish the **same observation date**, normalize
  the full 400 release rows and compare SHA-256 digests of canonical JSON.
  Row sorting is immaterial; every score, rank, trust grade, axis state and
  evidence date stays covered.

A differing score under an unchanged snapshot ID now fails verification.
A public payload with a duplicate rank or incomplete domain also fails.
Diagnostics contain error codes only; no user data or confidential evidence
is added to the incident logs.

## Existing system preserved
No scoring change, Supabase update, Cloudflare mutation, or publication
trigger. This extends the existing live verifier already called by both the
08:30 deployment health check and the 09:30 seven-day read-only monitor.

## Evaluation
Offline tests include: valid identity, row reordering, changed score with
identical snapshot ID, changed axis evidence date, duplicate rank and entity,
missing domain quota, missing trust grade, and end-to-end fail-closed
verification. Only a successful real Cloudflare test will establish live
deployment validity. The first scheduled seven-day monitoring date remains
2026-11-28; no historical successes are fabricated.
