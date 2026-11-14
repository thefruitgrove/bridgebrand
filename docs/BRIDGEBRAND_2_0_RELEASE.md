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
