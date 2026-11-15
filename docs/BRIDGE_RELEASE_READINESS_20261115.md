# BRIDGE 2.0 — Pre-release evidence and hold points (2026-11-15)

## 현재 상태
**RELEASE HOLD.** This branch is a candidate only. Do not merge, re-score, trigger publication or deploy yet.

### Verified read-only production database (2026-11-15 09:27 KST)
- Published T100 latest DB as-of **2026-11-14**. 400 ranked rows (CPR/GOV/STAR/UNI 100 each; rank range 1–100).
- Exact 11/14 DB join to scores/metrics/entity: **0 missing scores**, **0 score differences greater than 0.001**, **0 grade mismatches**, **0 domain mismatches**, **0 missing metrics**, **0 scores with fewer than two valid axes**, **0 null index scores**.
- CPR eligibility **69 eligible / 31 shadow** (existing panel rule); other three sectors **100 eligible each**. This is NOT an instruction to relabel 31 shadow entities as eligible.
- GitHub stored public `site/data/latest.json` still has **2026-11-13** as-of. Work previously verified deployed JSON normalized hash equals that old GitHub file. The production 11/14 parity test remains undone.
- Axis observation history 2026-09-01 .. 2026-11-14 for two configured versions totals **71,954 rows**, earliest 2026-09-07. Indexed-date vs global-ID query plans were inspected without ANALYZE. Full-range ID order scans primary ID index, while a single-day bounded query scans the date index then sorts a much smaller set.
- Small and bounded schema/query inspection is NOT the same as a complete PostgREST export stress test.

### 2026-11-15 automation investigation — resolved ambiguity
- `bridge-daily.yml` DID trigger at **2026-11-15 08:56 KST** (GitHub Actions `43655673565`).
- It failed in **Unit and regression tests**, specifically old `test_footer_copy` asserting legacy marker pages >= 28 while actual = 27.
- Score/collection/export/deploy steps were **skipped**. Earlier Work report said no 11/15 run had occurred at its observation time; this later log resolves the apparent contradiction.
- Candidate contains Work's revised meaningful footer contract; CI passes. No production main update yet, so automatic run is not repaired.

### Candidate code fixes
- Work: `audit_v5.py` policy fix for scored CPR shadow panels; `export_reads.py` minimal JSON projection, keyset pages, 57014 page backoff; `run.py` uses read-only projection; original Work patch preserved.
- Additional fail-closed **date-scoped fallback** added when an entire-ID scan still times out at 32 rows. Cursor floor is applied to each day to avoid repeating already yielded rows. Test covers timeout, partial-read continuation, wrong-date block, duplicate/ordering protections. **Live production PostgREST latency not yet measured**.
- Company/about/methodology/trust/data-extraction blocks now replace obsolete v1 copy rather than preserving an outdated block solely because its marker already exists. Static canonical pages updated.
- Cache key for changed briefing JS updated from `20261115-07` to `20261115-08` together with rebuild rule and test contracts.
- `tools/verify_release_candidate.py`: disposable CI build (build.py -> apply shell -> build_spa -> apply shell); checks WHAT/WHY/NEXT, branded copy, PDF DOM and that archived/public JSON hashes are unchanged.
- `tools/dry_run_public_export.py`: **NOT EXECUTED WITH PRODUCTION REST CREDENTIALS**. Can only SELECT rankings, entities, metrics, axis observations; output generated under temporary directory; validates 400 rows, identical published DB scores/grades/ranks, reference axes, fixed date/methodology and deterministic snapshot ID. Fail closed on mismatch; no live writes.
- `tests/test_read_only_export_gate.py`: test existing 11/13 fixture against a synthetic DB; blocks incorrect trust grade, changed entity set and prohibited writes.

### Verified CI
- Offline integrated CI `43659122663`: Python **177/177**, Node suites, postbuild invariant checks and diff check passed.
- Later cache-bust release commit must have its own CI PASS before final approval.
- CI does not test actual live PostgREST performance, desktop/mobile rendering or PDF page overflow.

## Remaining go/no-go steps — in order
1. Ensure latest integrated candidate CI PASSES after cache-key changes and static public copy sync.
2. Isolated Work environment with valid (not logged) Supabase secret runs:
   `python tools/dry_run_public_export.py --date 2026-11-14`
   on this exact candidate commit (not main); read-only GET and temporary local output only. Record elapsed, query count, pass/fail, 57014 traces (no key values). Do NOT invoke `bridge_pipeline.run score`, `publish-daily`, any `bootstrap` or production workflow.
3. If dry-run fails: diagnose PostgREST alias/timeouts and rank parity; patch ONLY candidate, rerun full CI/dry-run. If it succeeds: evaluate publication procedure, verify 400 T100, eligible/shadow, verified score/grade/rank/snapshot.
4. Test responsive PC/mobile and printed BASIC(18)/STANDARD(29)/English PDFs using candidate preview in an isolated deployment, including missing/reference axes, real dates and overflow.
5. Preserve original 11/13 public JSON, source code, latest 11/14 DB state, and rollback method. Cloudflare preview must NOT be confused with production.
6. Obtain explicit approval to merge main and change the live deployed UI/public data. On approval, run fixed-date recovery `2026-11-14` (never silently default to today's KST date), monitor actual DB -> GitHub JSON -> CDN snapshot match, then re-test nightly pipeline.
7. A source merge may automatically trigger a Cloudflare deploy. Review the hosting integration and deployment gating before merging main, not afterward.

**Go-live is not yet authorized.** In particular, passing offline CI does not certify the full REST export or the web frontend's actual behavior.
