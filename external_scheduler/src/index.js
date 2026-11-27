/**
 * BRIDGE external scheduler watchdog (Cloudflare Worker).
 * No DB, scoring, Cloudflare Pages, or public site writes.
 * The only permitted mutation is one GitHub Actions workflow_dispatch for
 * the current KST date, after read-only preflight checks.
 *
 * Disabled by default even if deployed: env.DISPATCH_ENABLED must equal "true".
 * No HTTP administration surface. No tokens, API error bodies or record data
 * are logged.
 */

const OWNER = "thefruitgrove";
const REPO = "bridgebrand";
const API = `https://api.github.com/repos/${OWNER}/${REPO}`;
const ACTIVE = new Set(["queued", "in_progress", "waiting", "requested", "pending"]);
const WORKFLOWS = ["bridge-daily.yml", "bridge-recover-publish.yml"];
const RUN_EVENTS = new Set(["schedule", "workflow_dispatch"]);
const HEADERS = {
  "Accept": "application/vnd.github+json",
  "X-GitHub-Api-Version": "2022-11-28",
  "User-Agent": "BRIDGE-External-Watchdog/1.0",
};

function kstDate(date = new Date()) {
  // en-CA yields ISO-formatted YYYY-MM-DD in Asia/Seoul.
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Seoul", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(date);
  const values = Object.fromEntries(parts.filter(p => p.type !== "literal").map(p => [p.type, p.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function kstClock(date = new Date()) {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Seoul", hour: "2-digit", minute: "2-digit", hourCycle: "h23",
  }).formatToParts(date);
  const values = Object.fromEntries(parts.filter(p => p.type !== "literal").map(p => [p.type, p.value]));
  return Number(values.hour) * 60 + Number(values.minute);
}

async function jsonGet(fetchImpl, url, token, authenticated = true) {
  const headers = authenticated ? {...HEADERS, Authorization: `Bearer ${token}`} : {
    "Accept": "application/json", "User-Agent": HEADERS["User-Agent"],
  };
  const response = await fetchImpl(url, {method:"GET",headers,cache:"no-store"});
  if (!response.ok) throw Error("READ_FAILED_" + response.status);
  return response.json();
}

function validPublication(payload, today) {
  if (!payload || typeof payload !== "object") throw Error("INVALID_PUBLICATION");
  const date = payload.asOfDate;
  if (typeof date !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(date))
    throw Error("INVALID_PUBLICATION_DATE");
  if (!Number.isInteger(payload.recordCount) || payload.recordCount !== 400)
    throw Error("INVALID_PUBLICATION_COUNT");
  if (!Array.isArray(payload.rankings) || payload.rankings.length !== 400)
    throw Error("INVALID_PUBLICATION_ROWS");
  if (payload.dataStatus !== "published") throw Error("NOT_PUBLISHED");
  if (date > today) throw Error("FUTURE_PUBLICATION");
  return date === today;
}

function recordedToday(run, today) {
  if (!run || run.head_branch !== "main" || !RUN_EVENTS.has(run.event)) return false;
  if (!["queued","in_progress","waiting","requested","pending","completed"].includes(run.status)) return false;
  const stamp = Date.parse(run.created_at || "");
  return Number.isFinite(stamp) && kstDate(new Date(stamp)) === today;
}

function decision(today, publication, dailyRuns, recoveryRuns) {
  if (validPublication(publication, today)) return "published_today";
  for (const runs of [dailyRuns, recoveryRuns]) {
    if (!Array.isArray(runs)) throw Error("INVALID_RUNS");
    if (runs.some(run => recordedToday(run,today) && ACTIVE.has(run.status)))
      return "existing_active_run";
  }
  // A retry requested by *any* operator or another fallback is already
  // a dispatch attempt. Do not repeatedly queue fresh full collection runs.
  if (dailyRuns.some(run => recordedToday(run,today) && run.event === "workflow_dispatch"))
    return "already_dispatched_today";
  // Do not discard a proven successful regular collection awaiting its
  // protected GitHub commit or Cloudflare deployment.
  if (dailyRuns.some(run => recordedToday(run,today) && run.conclusion === "success"))
    return "collection_succeeded";
  if (recoveryRuns.some(run => recordedToday(run,today) && run.conclusion === "success"))
    return "recovery_succeeded";
  return "dispatch";
}

async function runWatchdog(env, fetchImpl = fetch, now = new Date()) {
  if (env.DISPATCH_ENABLED !== "true") return {decision: "disabled"};
  // Safety bound. A late cron must NOT replay yesterday or start a new
  // collection while the regular pipeline is scheduled to begin.
  const minutes = kstClock(now);
  if (minutes < 7*60+30 || minutes >= 10*60)
    return {decision:"outside_safe_window"};
  if (!env.GH_DISPATCH_TOKEN || typeof env.GH_DISPATCH_TOKEN !== "string")
    return {decision:"configuration_error"};
  const today = kstDate(now);
  try {
    const url = `https://raw.githubusercontent.com/${OWNER}/${REPO}/main/site/data/latest.json?date=${today}&watchdog=1`;
    const publication = await jsonGet(fetchImpl,url,env.GH_DISPATCH_TOKEN,false);
    const [dailyResponse, recoveryResponse] = await Promise.all(WORKFLOWS.map(name =>
      jsonGet(fetchImpl,`${API}/actions/workflows/${name}/runs?per_page=100`,
        env.GH_DISPATCH_TOKEN)));
    if (!dailyResponse || !recoveryResponse) throw Error("MISSING_WORKFLOW_RESPONSE");
    const daily = dailyResponse.workflow_runs;
    const recovery = recoveryResponse.workflow_runs;
    const choice = decision(today,publication,daily,recovery);
    if (choice !== "dispatch") return {decision:choice, date:today};
    // Only an allowlisted main-branch workflow for *today* is dispatchable.
    const response = await fetchImpl(
      `${API}/actions/workflows/bridge-daily.yml/dispatches`,{
        method:"POST",
        headers:{...HEADERS,Authorization:`Bearer ${env.GH_DISPATCH_TOKEN}`,
                 "Content-Type":"application/json"},
        body:JSON.stringify({ref:"main",inputs:{as_of_date:today}}),
      });
    if (response.status !== 204) return {decision:"dispatch_rejected",date:today};
    return {decision:"dispatched",date:today};
  } catch (error) {
    // Fail closed on authentication errors, bad JSON, rate limit, or network.
    return {decision:"preflight_failed",date:today};
  }
}

export default {
  async fetch() {
    return new Response("Not Found", {status:404,
      headers:{"Cache-Control":"no-store","X-Robots-Tag":"noindex"}});
  },
  async scheduled(controller, env, ctx) {
    ctx.waitUntil(runWatchdog(env).then(result => {
      // Only non-sensitive decision metadata. No token or server responses.
      console.log(JSON.stringify({event:"bridge_watchdog",
        date:result.date || null, decision:result.decision}));
      // A genuine failure is visible in Worker logs, never silently green.
      if (["dispatch_rejected","preflight_failed","configuration_error"].includes(result.decision))
        throw Error("BRIDGE_WATCHDOG_" + result.decision);
    }));
  },
};
export { kstDate, kstClock, validPublication, recordedToday, decision, runWatchdog };
