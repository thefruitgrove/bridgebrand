# BRIDGE v5 operational rollout

Baseline: production GitHub 0ab034b9e7dcf695b4c25c328e8a54bdd0fc2cb1.
Whitepaper v5 defines the conceptual framework; engine version is separately `2026.10-v5-beta1`.

## Implemented contracts

- Normal news collection covers the 24-hour window ending 05:15 Asia/Seoul on the observation date. Recovery runs use the same cutoff. A run before 05:15 uses the previous observation date. The public JSON discloses the actual window.
- Entity-specific query completion is recorded in collection-run diagnostics. Legacy aggregate success does not prove that an individual entity had no mentions. Failed collection never invokes the AC absence rule.
- Signal expiry: news 28 days, YouTube level 2 days, regulatory signals 90 days. Annual official baselines have a separate 400-day renewal window. Unknown-source fallback is 28 days. These are explicit beta policy values, not validated universal constants. Explicit signal expiry overrides default windows.
- Prior official values carry only within their original validity anchor; carrying does not restart expiry. Baseline imports retain reference-period text and disclose whether a reference date is known. Missing reference dates are not advertised as newly published evidence.
- Reference-only axes display 50 as a visual baseline, explicitly labeled 참조. They are neither estimated target scores nor input to weighted rankings. No unvalidated imputation engine is introduced.
- A source content/axis/signal type is deduplicated; syndicated headline signatures converge. Activity Points come from accepted event units, once per event, not the sum of six axis signals. Platform level snapshots are not activity events.
- Weekly levels use daily confidence-weighted means; Activity Points shown publicly are the week-to-date sum of atomic daily event points. Cumulative levels are weekly averages. No previous week yields null WoW, not invented zero. Stability requires at least three observed weeks.
- V5 starts its own comparable metric series. Prior 2026.10-shadow-3 results remain in the archive and are labeled legacy; no automatic retroactive conversion. September reconstructed rows are marked Historical Weekly Backfill. New-method days cannot be padded with old-method ineligible entities.
- Source ownership is established through institutional homepage outbound links. Search/title matches produce review candidates only; they do not authorize scoring. Verification expires after 30 days and is refreshed automatically.
- Before publication, `audit_v5` verifies observation → signal → raw-item target/axis links and ranking → score target/version links. Internal audit output stays outside the public site.
- JSON exposes six values, status labels, reference count, dates, collection coverage and comparison status. Internal signal IDs, model coefficients, and original evidence text are not exported.
- HOME, ticker, domain pages and modals use the same live record. Live ticker alternates CPR/ENT/GOV in groups of ten through rank 50 and displays weekly index deltas; absence of a comparable prior week is displayed as comparison pending.

## Remaining data limitations

The audited production baseline on 2026-10-14 had CPR 53 eligible, GOV/UNI/ENT 100 each. This is a previous-method measurement, not a promised V5 outcome. GOV E had no observations; UNI R had one. A reference marker is not new source evidence. API/file sources for integrity and government evaluation must be validated for institution, evaluation year and construct before import. Existing civil-service evaluation data is D evidence; it must not be relabeled E merely to fill a diagram.

CPR/UNI R requires actual response evidence, not DART or admission indicators. ENT D requires genuine audience/product/advertising-contact experience, not general article exposure. Expanded response/experience keyword detectors yield low-confidence proxies; publication volume is not proof of quality. Channel engagement is a response proxy, not proof of positive sentiment.


## Dynamic target discovery and candidate ledger

Effective 2026-10-20, the active ranking roster is not treated as a closed or permanent population. T100 membership may change whenever newly observed entities satisfy identity, evidence and cohort requirements. This is especially important near ranks 80–100; a fixed roster would measure only the selected list rather than the current field.

The daily pipeline must run a separate discovery pass for CPR, GOV, UNI and STAR/ENT before scoring. Discovery output is subordinate data and does not itself change a score or a published rank. For every plausible name outside the active registry, retain the domain, proposed canonical name, observed aliases, first/last seen time, rolling mention and distinct-publisher counts, evidence references, ambiguity flags and review state in `bridge_entity_candidates`.

Candidate review follows this order:

1. confirm whether the entity already exists in `bridge_entities`;
2. test canonical name, Korean/English spellings, abbreviations, group/member and parent/sub-brand aliases;
3. verify that recent three-day raw items were collected and distinguish collection failure from no mention;
4. verify entity attribution rather than crediting only another registered subject in the same headline;
5. evaluate domain/cohort eligibility and comparable evidence coverage;
6. only after review, promote the entity to the active registry for a future scoring run.

No candidate is automatically inserted into a published T100/AN20 or used to displace an incumbent. Promotion requires identity resolution, duplicate and homonym review, domain-specific eligibility, auditable evidence and a recorded effective date. Existing published editions are never rewritten to insert a newly discovered entity.

All four domains are checked daily. Operational triage is ENT first because debut, comeback and issue cycles change fastest, followed by GOV, CPR and UNI; this ordering changes review urgency, not evidence thresholds or the obligation to inspect every domain. Candidate aging and repeated absence are retained as review history rather than silently deleted. Daily health output must report discovery completion and candidate counts by domain, including zero, so an empty candidate table cannot be mistaken for successful coverage.

## Operation

1. Bootstrap closes collector records abandoned for more than three hours and syncs registry.
2. UNI base and observations; news discovery and 24-hour target collection.
3. Homepage ownership refresh; verified GOV YouTube; regulatory and official baselines.
4. Score, metrics, lineage audit, publish, export, health gate.
5. Static build, commit only if the source head still matches, Cloudflare deployment.

Schedules stay 05:15 and 06:45 KST. GitHub schedule time is a start reservation, not an exact public completion guarantee. Deployment and frontend fetch must be verified separately. No credentials are committed.

## Acceptance

Run all unit tests, scoring regression, build and JS syntax checks. Validate a real workflow, V5 audit artifact, published methodology version and live JSON hash. Then check desktop/mobile modal status labels and absence of horizontal overflow. CI completion is not sufficient by itself to claim operational website verification.
