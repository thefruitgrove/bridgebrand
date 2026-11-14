/** Live end-to-end visual smoke for BRIDGEBRAND Reading Room.
 * No account, payment or data modifications. Uses Chrome DevTools and the
 * actual published T100 snapshot, not hard-coded example scores.
 */
import {spawn} from 'node:child_process';
import {mkdtempSync, mkdirSync, rmSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';

const base=process.env.BRIDGE_AUDIT_ORIGIN||'https://bridgebrand.co.kr/';
const out=process.env.BRIDGE_QA_OUTPUT||'/tmp/bridge-reading-room';
mkdirSync(out,{recursive:true});
const snapshot=await (await fetch(new URL('data/latest.json',base),{cache:'no-store'})).json();
const list=(snapshot.rankings||[]).filter(r=>r.domain==='UNI'&&r.ranking_type==='T100'&&r.external_id).sort((a,b)=>a.rank-b.rank);
if(snapshot.dataStatus!=='published'||snapshot.recordCount!==400||list.length<3)throw Error('Cannot QA without published UNI T100 data');
const id=x=>String(x.external_id);
const params=new URLSearchParams({field:'UNI',pick:id(list[2]),compareA:id(list[1]),compareB:id(list[0]),language:'한국어',trial:'free'});
const url=new URL('briefing.html?'+params,base).toString();
const dir=mkdtempSync(join(tmpdir(),'bridge-reading-'));
const port=19527+Math.floor(Math.random()*1000);
const chrome=spawn(process.env.CHROME_BIN||'/usr/bin/google-chrome',[
 '--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--no-first-run',
 '--remote-allow-origins=*','--user-data-dir='+dir,'--remote-debugging-port='+port,'about:blank'
],{stdio:'ignore'});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
let socket,seq=0;const waiters=new Map();
async function call(method,params={}){
 const n=++seq;
 return new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>{waiters.delete(n);reject(new Error('Chrome: '+method+' timed out'));},20000);
  waiters.set(n,{resolve,reject,timer});
  socket.send(JSON.stringify({id:n,method,params}));
 });
}
async function evalJS(code){
 const value=await call('Runtime.evaluate',{expression:code,returnByValue:true,awaitPromise:true});
 if(value.exceptionDetails)throw Error('Page JS evaluation error: '+String(value.exceptionDetails.text));
 return value.result.value;
}
async function screenshot(name){
 const shot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false,fromSurface:true});
 writeFileSync(join(out,name),Buffer.from(shot.data,'base64'));
}
try{
 let target;
 for(let n=0;n<65;n++){
  try{
   const r=await fetch('http://127.0.0.1:'+port+'/json/list');
   target=(await r.json()).find(x=>x.type==='page'&&x.webSocketDebuggerUrl);
   if(target)break;
  }catch{}
  await delay(180);
 }
 if(!target)throw Error('Chrome failed to start');
 socket=new WebSocket(target.webSocketDebuggerUrl);
 await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject});
 socket.onmessage=event=>{
  const packet=JSON.parse(event.data);if(!packet.id)return;
  const q=waiters.get(packet.id);if(!q)return;
  clearTimeout(q.timer);waiters.delete(packet.id);
  packet.error?q.reject(new Error(packet.error.message)):q.resolve(packet.result);
 };
 await call('Page.enable');await call('Runtime.enable');
 for(const width of [1440,390,320]){
  await call('Emulation.setDeviceMetricsOverride',{width,height:960,deviceScaleFactor:1,mobile:false});
  await call('Page.navigate',{url});
  await delay(3200);
  const visible=await evalJS(`(()=>{
   const b=document.querySelector('#journeyTrack [data-stage="2"]');
   if(!b)return false;b.click();return true;
  })()`);
  if(!visible)throw Error('Stage-2 navigation missing');
  await delay(1700);
  const facts=await evalJS(`(()=>{
   const q=s=>document.querySelector(s);
   return {
    panel:q('[data-stage-panel="2"]')?.hidden===false,
    photo:!!q('#bridgePulsePhoto')&&q('#bridgePulsePhoto').naturalWidth>0,
    photoId:q('#bridgePulsePhoto')?.getAttribute('src'),
    count:q('#fieldPulseList')?.querySelectorAll('li').length,
    bars:q('#fieldPulseBars')?.querySelectorAll('.pulse-bar').length,
    lead:q('#fieldPulseLead')?.textContent?.trim(),
    leadColor:q('#fieldPulseLead')?getComputedStyle(q('#fieldPulseLead')).color:null,
    chartBg:q('.field-pulse-visual')?getComputedStyle(q('.field-pulse-visual')).backgroundColor:null,
    pagerBg:q('.stage-pager')?getComputedStyle(q('.stage-pager')).backgroundColor:null,
    missingHorizontalSpace:document.documentElement.scrollWidth>innerWidth+5
   };
  })()`);
  console.log(JSON.stringify({width,...facts}));
  if(!facts.panel||!facts.photo||facts.count!==20||facts.bars!==20||!facts.lead||facts.lead.includes('불러오고 있습니다')||facts.missingHorizontalSpace){
    throw Error('Reading Room regression at '+width+': '+JSON.stringify(facts));
  }
  await evalJS("document.getElementById('fp-current').scrollIntoView({block:'center',behavior:'instant'})");
  await delay(250);await screenshot('reading-room-'+width+'-lead.png');
  await evalJS("document.getElementById('fp-top20').scrollIntoView({block:'start',behavior:'instant'})");
  await delay(250);await screenshot('reading-room-'+width+'-data.png');
 }
 console.log('PASS: latest UNI T100, selected actual competitors, stage 02, 20 rows, 20 bars, photo, no horizontal overflow on 3 widths');
}catch(e){console.error(e);process.exitCode=1}finally{
 try{socket?.close()}catch{}
 chrome.kill('SIGTERM');await delay(150);rmSync(dir,{recursive:true,force:true});
}
