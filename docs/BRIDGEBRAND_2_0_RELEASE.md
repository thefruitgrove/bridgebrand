# BRIDGEBRAND 2.0 — Release and Brand Design Baseline
Date: 2026-11-14 (Asia/Seoul) | Status: rolling UX release, **not** a scoring/methodology change.

## Purpose
The product is one reputation-index engine with two experiences:
- **Discover** — public discovery, live search, weekly movements and domain exploration. The home page is its initial entry point; an independent /discover route is not yet released.
- **Intelligence** — existing six-stage professional interpretation, MY PICK + two comparisons, reports and subscription configuration. Preserve the existing analytical and PDF logic.

Do not split the data warehouse or run duplicate collection pipelines for the two audiences.

## Brand visual rules
- Signal Blue: `#2458F5` — brand action and intelligence
- Signal Yellow: `#FFD633` — discovery, visual accent, and selection
- Warm White: `#FFFDF7` — editorial background
- Ink: `#17191D` — legible body text
- Ice Blue: `#E9F0FF` — secondary data UI
- On yellow backgrounds use dark text. Yellow **must not** signify a higher score, favourable public sentiment, or evidence grade.
- The hero's loop visual is an original geometric SVG metaphor, not evidence, not a photo of a real rated subject.
- Typography: Noto Sans KR for functional UI and large editorial headlines, restrained serifs for report/editorial passages.
- Prefer real measured values and plainly visible dates; never design fictional leaderboard numbers into live UI.
- Desktop and mobile have one semantic source with responsive styles at 1050, 760 and 380px breakpoints; always provide accessible reduced-motion and keyboard navigation.

## Important source-of-truth files
- `site/bridge-v2.html`: full V2 public home template and original signal illustration
- `site/bridge-v2.css`: desktop/mobile layout tokens and components
- `site/bridge-v2.js`: safe client-side read of `site/data/latest.json`, subject search and live weekly cards
- `site/bridge-v2-intelligence.css`: visual-only styling scoped to `body.intel-page`
- `site/intelligence.js`: passes a preselected `pick` ID to the existing three-subject briefing selection
- `tools/publish_v2_home.py`: protects legacy homepage; publishes V2 home only after checking the 400-subject published snapshot
- `tools/apply_brand_shell.py`: idempotent post-build hook; preserves the new home on daily and direct Cloudflare builds
- `tests/test_v2_home.py`: offline HTML, routing, mobile CSS and safe-data tests
- `.github/workflows/bridge-v2-release.yml`: presentation-only release test and commit, no recollection/rescoring

## Immutable project boundaries
1. Do not modify source collection, BRIDGE scoring, 6-axis methodology, historical archive, entity IDs, evidence lineage, trust grades or existing 6-stage report/PDF engine in a design release.
2. Read-only public search consumes the same T100 published snapshot as existing ranking pages; searches never change rankings or scores.
3. Do not invent explanations for score movement: the homepage describes measured point differences as changes, not causal findings.
4. Do not apply new price claims: existing fee display is prototype/test configuration, not approved commercial policy.
5. Photos, logos and images of companies, universities or public figures require rights verification and clear source labels.

## Release verification and limitations
GitHub Actions Release checks node syntax, three regression cases, source validity, deterministic site rebuild and old-home backup before publishing. Successful GitHub publication does not by itself prove Cloudflare's public edge has deployed. Independently verify the public domain and actual PC/mobile appearance, including screenshot QA and browser checks. During this phase, only the home gateway and Intelligence visual skin are 2.0; rankings and briefing pages retain their existing layouts pending dedicated visual and accessibility QA.

## Rollback
- The previously published home is stored in `site/legacy-home.html` and is marked noindex.
- If the V2 home causes an operational issue, disable the `publish_v2_home()` call in `tools/apply_brand_shell.py`, restore `site/legacy-home.html` to `site/index.html` and `site/site_fix/index.html`, and rebuild/redeploy.
- Never roll back or delete index data as part of a design rollback.
- To roll back the Intelligence skin, remove the optional `bridge-v2-intelligence.css` link (and its automatic insertion) without changing the existing analysis engine.

## Next QA gates
1. Live Cloudflare asset propagation and 400-entity search.
2. PC 1440/1280 width and mobile 390/360/320 layouts (navigation, search, focus, overflow).
3. BRIDGE home -> Intelligence with preselected MY PICK -> COMPARE A/B -> briefing -> PDF workflow.
4. Preserve existing Korean/English access throughout the site; validate and implement a native V2 home language switch if needed.
5. Extend common blue/yellow visual system to THIS WEEK and rank/report pages only after UX testing; keep scientific meaning of chart colors independent.
6. Finalize monetization service catalogue separately and then issue official Brand Book PDF + design tokens after visual QA.

## Editorial revision II — visual decision (2026-11-14)
The initial version showed too many competing cobalt/yellow blocks and looked like a presentation dashboard, not a visual research magazine. The user rejected the initial visual quality and inconsistent internal-page styling.

**Superseding design direction:** BRIDGE is a *premium editorial research magazine connected to a working analysis product*, not a four-color pitch deck. Warm white occupies the majority of every ordinary reading page; Signal Blue is typographic/navigation ink, and Signal Yellow is reserved for rare visual punctuation. Avoid alternating full-width white/yellow/blue backgrounds and repeated rounded stat cards. Photo-led covers, ample whitespace, elegant editorial serif titles, restrained captions, hairline rules, real data and source dates define the layout.

**Canonical edition files:**
- `site/bridge-v2.html` and `site/bridge-v2-magazine.css`: photo-led cover, weekly-photo essay, restrained editorial sector navigation, Intelligence reading-room feature
- `site/bridge-v2-editorial.css`: shared warm-white/blue magazine visual system for sector ranking, THIS WEEK, PUBLICITY, methodology, evidence grade, Intelligence, subscription and six-stage briefing
- `tools/apply_brand_shell.py`: deterministic, idempotent styling/link and wordmark application for the same internal pages on future daily rebuilds
- `tests/test_v2_editorial.py`: test page invariants and editorial style injection
- `.github/workflows/bridge-v2-magazine-release.yml`: static-only full-site visual synchronization, immutable 400-rankings snapshot assertion, public-edge integration test
- Screenshot QA workflow captures homepage, CPR, THIS WEEK and Intelligence in desktop/mobile viewport sizes.

Existing image assets (hero_home, hero_this_week, hero_data and category hero photos) are reused. They are illustrative editorial photos; they do not assert particular reputational events or evidence. The existing older blue/yellow color-block Intelligence stylesheet is retired.

**Unchanged scientific/functional invariants:** collection runs, scoring, trust grading, evidence provenance, baseline snapshots, the 3-subject comparison, 6-stage briefing content, PDF engine, subscriptions and source-history archive.

**Human verification still required:** sample real PC and mobile visual screenshots at 1440px/390px/320px, typography/contrast/overflow, exact cross-page experience, native Korean-English switching on the new home, product conversion events and accessibility checks. Automated deploy checks are necessary but not sufficient for design quality.

## Reading Room edition — Structural implementation (2026-11-14)
The latest revision moves beyond palette fixes: the **actual briefing HTML grid** for stage 02 is composed into an editorial report spread on each deterministic rebuild. No BRIDGE index, data provenance, rank, trust or PDF-generation code was modified.

### Current rollout boundaries
- `site/bridge-v2-reading-room.css`: the last, self-contained screen-only reading-room composition. Editorial headings, full-width page rhythm, large field photograph, accessible paper-based T20 table and bar chart, 320px/390px mobile version.
- `site/bridge-v2-reading-room.js`: chooses the existing field-appropriate **illustrative** photo on CPR/GOV/UNI/ENT from the URL. It is not evidence.
- `tools/apply_brand_shell.py`: applies a new semantic `#fp-current.bridge-pulse-feature` with the same `fieldPulseLead` etc. IDs and adds the lightweight 5-step `data-bridge-journey="v2"` on the Intelligence gateway. It does not change the full six-step JS analysis.
- `site/intelligence.html`: presents genuine current acquisition steps. The two comparisons are **manually selected** (no promise of automatic competitor identification); payment/account activation still needs a separate approved implementation.
- `tests/test_v2_editorial.py`: asserts actual structural markup, stable JS IDs, no duplicate injection, no PDF print CSS selector leakage.
- `.github/workflows/bridge-v2-reading-room-qa.yml` and `tools/verify_v2_reading_room.mjs`: real public data end-to-end checks of UNI 20-row chart, image loading, no horizontal overflow at desktop 1440 and mobile 390/320, six retained screenshots.

### Design acceptance checklist
- The page should be judged as a *single editorial research publication* from cover through report, not by whether it contains nice cards.
- Images support reading rhythm and subject matter, not factual evidence for measured reputation.
- Each chart must have meaningful labels and real figures, based on the existing 400-subject published snapshot and original six-axis scoring.
- Every paragraph must remain legible against its own background. Use computed-style contrast auditing and human screenshot review (including inactive/active stages), not merely successful builds.
- Navigation from MY PICK to the six-stage report, and onward to report preservation and one-off/subscription consultation should remain explicit and error-free.
- Do not place price or checkout promises until pricing and payment capabilities are approved.

### Next milestones, in order
1. Extend genuine *structural* layout to all remaining briefing stages (01,03,04,05,06); preserve the 15 existing axis-pair analyses and PDF rendering.
2. Apply one semantic editorial data-story pattern to four sector rankings and weekly PUBLICITY, not merely an inherited CSS color override.
3. QA user selection errors, full BRIDGE report, laptop/tablet/mobile view, accessibility (text contrast/keyboard), Korean/English, screenshots and one-page evidence lineage.
4. Validate real customer task completion: find subject, finish 3-way comparison, understand why, generate/share report, seek a paid service.
5. Publish the approved identity and implementation rules in the BRIDGEBRAND brandbook only after visual QA confirms parity across pages.
