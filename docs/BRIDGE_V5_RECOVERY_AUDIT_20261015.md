# BRIDGE v5 recovery audit — 2026-10-15 KST

Scope: thefruitgrove/bridgebrand, bridgebrand.co.kr and bridgebrand-production only.
Authority: BRIDGE_whitepaper_v5, dated 2026-10-14. Document version and engine version are distinct.

## Verified evidence

- Supabase read-only queries: current methodology 2026.10-v5-beta1, 2026-10-15.
- CPR 44 eligible, 55 shadow (trust D, confidence 15.50–54.68), 1 withheld (N/R). GOV, UNI and ENT each 100 eligible. Published T100 rows: 344.
- Published ranking-to-score mismatches: 0. Raw items without collection_run_id: 0. Collection runs stuck running for more than three hours: 0.
- Latest successful collection run: 38645651352, completed 07:20 KST. Source commit 93deff218784b6826107c58426743f9d0b81e855; generated export commit a8067199a380982635130ec3db9e522533583651.
- That run completed lineage audit, score, publish, export, health gate, static build and Git push. Deployment hook was skipped because its value was empty; this alone does not prove deployment failure.
- Live JSON SHA-256 ae26b3e2f959c6d8358b2a7958d4567d5a571cbada90fd66f9c7cbe3a81a999d matched the exported JSON; live script also matched. HTML differed only in its runtime Seoul clock fallback date.
- Independent live verification run 38700558546 passed after commit ba7063fa7d3393f8d2fed9e3952bec731e992028.

## Recovery changes

1. Separate, read-only live deployment verification with bounded retries, 12-minute timeout, an artifact and a summary. Data collection success is not deployment verification.
2. Historical modal selection keyed by domain, target and date. Missing historical detail never substitutes today's record. Empty periods show no ranked records.
3. Scope/methodology changes block unconditional improvement language in lists, ticker, THIS WEEK and modal deltas.
4. Radar reference edges use dashes and hollow points; reference values stay excluded from ranking inputs. The display reference 50 remains a beta presentation convention, not measured neutral reputation or a validated estimate.
5. Fetch/contract failure keeps deployed fallback data and explicitly identifies it as unverified current data.
6. Cohort re-ranking never reuses T100 rank movement. Missing prior ranks are shown as comparison pending. THIS WEEK identifies its daily ranking basis.
7. Static TOP5 ties use a stable name tie-break instead of set iteration order; two builds with different PYTHONHASHSEED values produce identical index hashes.
8. Static masthead generation uses Asia/Seoul rather than the build host timezone. Script cache version updated.

## Whitepaper acceptance status

| Contract | Status | Remaining condition |
| --- | --- | --- |
| raw → score → export → served assets | verified for current snapshot | repeat after each production data run |
| observed/maintained/reference state | implemented; reference styling corrected | reference convention remains a beta policy choice |
| six numbers for all 400 public profiles | partial | noneligible profiles are not all public; no validated imputation model |
| target-level collection success vs absence | implemented; tested | full required-source coverage and independent source-family quality require further validation |
| event-based activity and deduplication | implemented; regression-tested | identical-title clustering does not establish semantic independence of every event |
| validity policy | beta implementation | source defaults exist; full domain × axis × material registry and empirical sensitivity validation remain incomplete |
| weekly confidence and observation coverage | partial | coverage diagnostics exist; calibration of confidence against observation days, freshness and dependence is not complete |
| comparability | partial | axis/method status exists and limits presentation; source-composition changes and common-axis delta need fuller validation |
| official channel expansion | partial | 13 configured mappings; latest run fetched 11 channels and accepted 41 signals, not 41 channels |
| missing axes | unresolved data coverage | GOV E 0/100; UNI R 1/100; CPR R 21/100; ENT D 35/100 in saved audit; do not relabel other constructs to fill gaps |
| independent live verification | implemented and executed | check each future run; does not prove visual layout or model validity |
| internal conversation freeze | unknown | internal conversation/session telemetry inaccessible |
| earlier approval rejection | unknown original record | reported text is a search lead, not an independently audited approval log |

## Safe next work

Keep current evidence and historical versions. Review source suitability and ownership before adding any dataset. For UNI, inspect the separate daily files and match canonical entity IDs in a staging report before import. For GOV E, validate institution, evaluation year, construct and revision status of integrity/responsibility sources. CPR/UNI R need actual public response, and ENT D needs experience evidence. Do not loosen publication thresholds to obtain 100 ranked targets. Validate estimation with temporal holdouts before using estimates as scores.

This recovery is a repair of known operational and presentation defects, not a claim that all v5 research and source coverage are complete. No new collection, database mutation, score recomputation or threshold changes are part of this repair.
