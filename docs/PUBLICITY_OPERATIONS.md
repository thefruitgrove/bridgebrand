# BRIDGE PUBLICITY — operations and editorial contract

Launch: Friday 2026-10-16, 12:00 Asia/Seoul. First overall: Monday 2026-10-19, 12:00, assigned to issue 2026-W42.

## Public routes and design

- /publicity.html: weekly board, nine editorial positions per week, WED/FRI x CPR/GOV/UNI/ENT and one OVERALL.
- /publicity-article.html?id=2026-w42-wed-cpr-example: one explicitly labeled real-data example for 2026-10-14. Not a formal Wednesday release.
- Home PUBLICITY sits under the ENT column beside EXPLORE THIS WEEK, left aligned with the same underlined treatment. Existing imagery, charcoal/navy, muted gold and serif headings are retained. Article text sits on a translucent light paper surface.

## Automatic preparation and noon publication

The GitHub workflow .github/workflows/bridge-publicity.yml runs at 10:30, 11:15 and 11:45 KST Monday/Wednesday/Friday. It has 12:10 and 12:40 delayed-data recovery runs. GitHub schedules may start late; they prepare in advance rather than owning the public release clock.

The database RLS policy exposes only status=ready and scheduled_at<=now() to anonymous/authenticated readers. Prepared future articles are inaccessible even through the article URL/API. Once the server clock reaches noon, the first request can read them without waiting for GitHub or redeployment. An already open board refreshes every 60 seconds. A preparation failure can delay publication; it never creates a fake current snapshot. UI discloses a delayed preparation when needed.

Noon cloud task BRIDGE PUBLICITY 공개 점검 independently checks the expected four domain articles or one overall article and diagnoses failures. It may rerun the failed PUBLICITY job, but must not alter score engines, quotas or history. It sends no external Slack/email messages.

## Data and editorial rules

publicity/generate.py uses only PUBLIC_FIELDS from site/data/history.json. It does not have access to internal weights, coefficients or raw evidence through the article input. It is a deterministic, versioned interpretation engine, not a language-model/API dependency.

- Wednesday/Friday: Monday through the publication-date observation snapshot, four domain articles.
- Monday: previous Monday through Sunday, one ALL article assigned to the previous ISO week.
- The exact required end date must exist for every domain. Missing/duplicate/invalid/mixed-method data blocks staging. V4/historical backfills are excluded from V5 narratives.
- Rankings use the end-date Daily basis, Weekly is explicitly partial where applicable, Activity is a separate weekly amount. Coverage is the public eligible set, not the full population.
- Reference axes are neither strengths nor weaknesses. No unverified WoW, causal claim, guaranteed forecast or source-level private explanation is generated. Zero recorded activity is not proof of zero real-world activity.
- The writer selects a leading profile and a lower-ranked D/E profile where evidence supports it. If not supported, it explains the limitation instead of manufacturing a positive story.
- Current version is publicity-rules-1.0. Text variety and editorial sophistication can be extended with new verified rules; this initial service does not pretend to be unrestricted AI reporting.

## Frozen records and permissions

public.bridge_publicity_articles contains public article payloads only. bridge_publicity_private.snapshots stores immutable source inputs keyed by SHA-256; anon/authenticated cannot access it. Public clients have SELECT only and cannot execute bridge_stage_publicity. Existing scoring tables/policies are unchanged.

bridge_stage_publicity is SECURITY INVOKER, callable only by service_role. A four-domain issue is staged in a single transaction. IDs and a unique(issue_week,slot,domain,is_example) constraint prevent duplicate editions. Repeated preparation may refresh a future draft; published articles are not overwritten by this RPC. Corrections require an explicit editorial change and a correction note; do not silently rewrite a published article.

The source repository is public: do not place future drafts, private snapshots, raw evidence, API secrets or private model parameters in it. The only committed article example is intentionally public. publicity-config.js contains the existing public anonymous key, not a service key.

## Verification and recovery

- python -m unittest discover -s tests -p test_publicity.py -v
- python -m publicity.generate --date 2026-10-14 --example --dry-run --output /tmp/example.json
- python tools/verify_publicity.py (anonymous API smoke test)
- python tools/verify_live.py (live asset comparison)

Regular preparation is python -m publicity.generate; manual date uses --date YYYY-MM-DD. The existing repository secret SUPABASE_SECRET_KEY is used only in the GitHub runner. No additional provider key is required. Check the PUBLICITY workflow failure log first, then exact observation-date coverage, then the public table's scheduled_at/status and anonymous API. Never lower evidence gates to meet article count.

Deployment acceptance: sample visible, future article probe invisible and removed, anon writes and private snapshot access denied, duplicate preparation idempotent, Friday four/Monday one and ISO-week rollover tested, existing score tests pass, live assets match.
