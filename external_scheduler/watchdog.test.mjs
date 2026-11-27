import test from "node:test";
import assert from "node:assert/strict";
import {kstDate,kstClock,validPublication,decision,runWatchdog} from "./src/index.js";

const TODAY=new Date("2026-11-28T00:00:00+09:00");
const payload=()=>({asOfDate:"2026-11-27",recordCount:400,
  rankings:Array.from({length:400},()=>({})),dataStatus:"published"});
const run=(event="schedule",status="completed",conclusion="failure")=>({
  head_branch:"main",event,status,conclusion,created_at:"2026-11-28T00:50:00Z"
});
const config={DISPATCH_ENABLED:"true",GH_DISPATCH_TOKEN:"fake-test-token"};
const now=new Date("2026-11-28T07:35:00+09:00");
const response=(value,status=200)=>({ok:status>=200&&status<300,status,
  json:async()=>value});

function mockFetch({published=false,daily=[],recovery=[],broken=false,postStatus=204}={}) {
  const calls=[];
  const fetchMock=async (url,init={})=>{
    calls.push({url,method:init.method||"GET",body:init.body});
    if (broken) throw Error("simulated-no-network");
    if (url.includes("raw.githubusercontent.com")) return response(
      {...payload(),asOfDate:published?"2026-11-28":"2026-11-27"});
    if (url.includes("bridge-recover-publish.yml")) return response({workflow_runs:recovery});
    if (url.includes("bridge-daily.yml") && url.includes("/runs?"))
      return response({workflow_runs:daily});
    if (url.endsWith("/dispatches")) return response(null,postStatus);
    throw Error("unexpected url "+url);
  };
  return {fetchMock,calls};
}

test("KST timestamp interpretation",()=>{
  assert.equal(kstDate(new Date("2026-11-27T22:35:00Z")),"2026-11-28");
  assert.equal(kstClock(new Date("2026-11-27T22:35:00Z")),7*60+35);
});

test("never dispatch by default without explicitly enabled flag",async()=>{
  const mock=mockFetch();
  assert.equal((await runWatchdog({},mock.fetchMock,now)).decision,"disabled");
  assert.equal(mock.calls.length,0);
});

test("ignore crons before/after safe KST window",async()=>{
  const mock=mockFetch();
  const early=new Date("2026-11-28T06:30:00+09:00");
  assert.equal((await runWatchdog(config,mock.fetchMock,early)).decision,"outside_safe_window");
  const late=new Date("2026-11-28T11:30:00+09:00");
  assert.equal((await runWatchdog(config,mock.fetchMock,late)).decision,"outside_safe_window");
  assert.equal(mock.calls.length,0);
});

test("published today is not dispatched twice",async()=>{
  const mock=mockFetch({published:true});
  const result=await runWatchdog(config,mock.fetchMock,now);
  assert.equal(result.decision,"published_today");
  assert.equal(mock.calls.filter(x=>x.method==="POST").length,0);
});

test("active daily or recovery prevents new collection",async()=>{
  for (const opts of [{daily:[run("schedule","in_progress",null)]},
                      {recovery:[run("schedule","queued",null)]}]) {
    const mock=mockFetch(opts);
    assert.equal((await runWatchdog(config,mock.fetchMock,now)).decision,"existing_active_run");
    assert.equal(mock.calls.filter(x=>x.method==="POST").length,0);
  }
});

test("prior dispatch even if failed blocks further full retries",async()=>{
  const mock=mockFetch({daily:[run("workflow_dispatch","completed","failure")]});
  assert.equal((await runWatchdog(config,mock.fetchMock,now)).decision,"already_dispatched_today");
  assert.equal(mock.calls.filter(x=>x.method==="POST").length,0);
});

test("successful primary or recovery is not recollected",async()=>{
  for (const opts of [{daily:[run("schedule","completed","success")]},
                      {recovery:[run("schedule","completed","success")]}]) {
    const mock=mockFetch(opts);
    assert.notEqual((await runWatchdog(config,mock.fetchMock,now)).decision,"dispatched");
  }
});

test("failed scheduled primary with no dispatch starts exactly today's main workflow",async()=>{
  const mock=mockFetch({daily:[run("schedule","completed","failure")]});
  const result=await runWatchdog(config,mock.fetchMock,now);
  assert.equal(result.decision,"dispatched");
  const post=mock.calls.filter(x=>x.method==="POST");
  assert.equal(post.length,1);
  assert.match(post[0].url,/bridge-daily.yml\/dispatches$/);
  assert.deepEqual(JSON.parse(post[0].body),{ref:"main",inputs:{as_of_date:"2026-11-28"}});
});

test("untrusted rows, future publication, and missing credentials fail closed",async()=>{
  assert.throws(()=>validPublication({...payload(),recordCount:399},"2026-11-28"));
  assert.throws(()=>validPublication({...payload(),asOfDate:"2026-11-29"},"2026-11-28"));
  const mock=mockFetch();
  assert.equal((await runWatchdog({DISPATCH_ENABLED:"true"},mock.fetchMock,now)).decision,"configuration_error");
  assert.equal(mock.calls.length,0);
});

test("network errors and rejected dispatch fail visibly without retry storms",async()=>{
  const offline=mockFetch({broken:true});
  assert.equal((await runWatchdog(config,offline.fetchMock,now)).decision,"preflight_failed");
  assert.equal(offline.calls.filter(c=>c.method==="POST").length,0);
  const rejected=mockFetch({postStatus:403});
  assert.equal((await runWatchdog(config,rejected.fetchMock,now)).decision,"dispatch_rejected");
  assert.equal(rejected.calls.filter(c=>c.method==="POST").length,1);
});

test("QA branch, yesterday's dispatch do not mask today's missing primary",()=>{
  const rows=[{...run("workflow_dispatch"),head_branch:"stability/testing"},
              {...run("workflow_dispatch"),created_at:"2026-11-26T22:35:00Z"}];
  assert.equal(decision("2026-11-28",payload(),rows,[]),"dispatch");
});

test("no public control surface is exposed",async()=>{
  const worker=(await import("./src/index.js")).default;
  const result=await worker.fetch(new Request("https://example.invalid/anything"));
  assert.equal(result.status,404);
});
