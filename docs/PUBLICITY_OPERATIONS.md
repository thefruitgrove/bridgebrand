# BRIDGE PUBLICITY — operations and editorial contract

Launch: Friday 2026-10-16, 12:00 Asia/Seoul. First overall: Monday 2026-10-19, 12:00, assigned to issue 2026-W42.

## Public routes and design

- /publicity.html: weekly board, nine editorial positions per week, WED/FRI x CPR/GOV/UNI/ENT and one OVERALL.
- /publicity-article.html?id=2026-w42-wed-cpr: the formal Wednesday 2026-10-14 CPR article. The launch week contains four Wednesday and four Friday domain articles; legacy samples were removed in the 2.0 editorial correction.
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

public.bridge_publicity_articles contains public article payloads only. bridge_publicity_private.snapshots stores immutable source inputs keyed by SHA-256; anon/authenticated cannot access it. Public clients have column-limited SELECT access and cannot read `snapshot_hash` or execute bridge_stage_publicity. Existing scoring tables/policies are unchanged.

bridge_stage_publicity is SECURITY INVOKER, callable only by service_role. A four-domain issue is staged in a single transaction. IDs and a unique(issue_week,slot,domain,is_example) constraint prevent duplicate editions. Repeated preparation may refresh a future draft; published articles are not overwritten by this RPC. Corrections require an explicit editorial change and a correction note; do not silently rewrite a published article.

The source repository is public: do not place future drafts, private snapshots, raw evidence, API secrets or private model parameters in it. The only committed article example is intentionally public. publicity-config.js contains the existing public anonymous key, not a service key.

## Verification and recovery

- python -m unittest discover -s tests -p test_publicity.py -v
- python -m publicity.generate --date 2026-10-14 --example --dry-run --output /tmp/example.json
- python tools/verify_publicity.py (anonymous API smoke test)
- python tools/verify_live.py (live asset comparison)

Regular preparation is python -m publicity.generate; manual date uses --date YYYY-MM-DD. The existing repository secret SUPABASE_SECRET_KEY is used only in the GitHub runner. No additional provider key is required. Check the PUBLICITY workflow failure log first, then exact observation-date coverage, then the public table's scheduled_at/status and anonymous API. Never lower evidence gates to meet article count.

Deployment acceptance: sample visible, future article probe invisible and removed, anon writes and private snapshot access denied, duplicate preparation idempotent, Friday four/Monday one and ISO-week rollover tested, existing score tests pass, live assets match.

## 2026-10-15 editorial and public-copy revision

- Rule writer 1.1 now uses a news lead, named profile contrasts, activity findings and qualified follow-up questions. Attribution names SIGNALBRIDGE BRIDGE 브랜드평판지수 INDEX once per domain article.
- CPR and ENT examples were an interim launch-stage presentation. They were removed when the four formal 2026-10-14 Wednesday articles were issued under editorial standard 2.0. Formal published articles remain protected from automatic overwrite.
- Input hash and snapshot-storage explanation are retained internally, removed from visible article copy. Private input remains outside public article data.
- Public explanations are centralized in `presentation/public_copy.py`, including the shared footer. Thresholds, coefficients and collection strategies are not disclosed. Unverified claims of statistical independence, perfect bias removal and fully established organizational separation are removed.
- LIVE ticker uses a valid same-scope weekly comparison when available; otherwise the highest valid axis and valid-axis count. Reference axes never become observed findings. No comparison history is invented.
- Legacy `bridge_full_site.html` entry routes to canonical pages, preserving recognized view hashes. This prevents an independent stale copy from reappearing in the daily build. `site_fix` mirrors share the new footer.
- Responsive QA page offers 360/390/430px frames. Embedded checks assess responsive CSS; these do not replace real iOS/Android device testing.
- Live inspection also found that the initial HTML still showed legacy pilot values before JavaScript loaded. The home TOP5 and initial ticker now read the same published `latest.json`; unavailable input produces a connection notice rather than pilot results.

## Editorial standard 2.0 — seven-paragraph PUBLICITY article

From 2026-10-16, every CPR, GOV, UNI and ENT article follows the same verified narrative contract. The structure is fixed, while names, figures, coverage and wording are selected from the frozen issue input. The writer must not reuse a sentence whose facts do not match the current domain.

1. **Headline and standfirst:** `[leader] [daily score]… [domain], 선두의 수치 뒤에 남은 연결 과제`. The standfirst states the eligible count and that the article reads position, relationship profile and observation range together.
2. **Paragraph 1 — fact lead and statistical boundary:** date, domain scope, leader, daily index, eligible count and eligible-set mean. It must state that the mean does not represent the whole field.
3. **Paragraph 2 — composition behind the rank:** compare the leader's highest and lowest usable axes. Reference-only axes are excluded. A leading rank never proves that all relationships are equally strong.
4. **Paragraph 3 — profile beyond the leader:** use a lower-ranked D/E profile only when both axes have valid evidence. Otherwise disclose that no defensible contrast is available. Do not manufacture a strength.
5. **Paragraph 4 — interpretation boundary:** explain why multidimensional reading adds context, and prohibit causal inference or a forecast from one axis.
6. **Paragraph 5 — activity versus reputation:** identify the largest verified activity amount and state that volume is not direction or favourability. Zero means no qualifying recorded activity, not no real-world activity.
7. **Paragraph 6 — observation coverage:** compare the most and least covered axes and distinguish missing evidence from a negative state.
8. **Paragraph 7 — time and purpose:** state the actual observation dates, prohibit converting the daily position into a confirmed weekly result, and close with the next relationship question.

The table and relationship diagrams appear after paragraphs 1–2. Paragraphs 3–7 follow the visuals under three descriptive subheads. Every domain article therefore contains exactly seven prose paragraphs in a `2 + 2 + 3` section pattern. Korean dates and subject/topic particles are generated through tested helpers to prevent recurring errors such as `디어유이`, `진주시이` and `고려대학교은`.

### Language and evidence rules

- Name `시그널브릿지(SignalBridge) BRIDGE 브랜드평판지수 INDEX` once in the first paragraph.
- Prefer concrete nouns, verified figures and short causal boundaries over promotional adjectives.
- Do not call missing evidence weak, poor or negative. Do not call activity favourable. Do not call a score a moral, ethical or comprehensive real-world judgment.
- Use a domain-appropriate scope: CPR 기업, GOV 공공기관·지자체, UNI 대학, ENT 대중문화·인물.
- Keep the headline useful, but vary the body only where the data supports a distinct profile. Stylistic variety cannot override the factual contract.
- The current rule identifier is `publicity-rules-2.0`. Tests require exactly seven paragraphs, the attribution, the statistical boundary, the forecast prohibition and valid Korean particles.

### Explicit correction and recovery

Published articles remain immutable to the scheduled generator. A full rewrite requires an explicit editorial decision, keeps the original article ID and scheduled time, uses the original frozen snapshot, and adds a visible revision note. The correction bundle must be prepared in a controlled private workspace and must not be committed to the public repository. Database replacement is a separate privileged operation and must be limited to the named article IDs in one transaction. After a correction, run the complete test suite and `tools/verify_publicity.py` as an anonymous reader.

For the 2026-W42 launch correction, the two sample rows were removed and replaced by four formal Wednesday articles dated 2026-10-14. The four Friday articles dated 2026-10-16 retained their IDs and frozen facts and received the 2.0 editorial rewrite. This is a one-time editorial correction, not permission for scheduled jobs to overwrite published copy.
