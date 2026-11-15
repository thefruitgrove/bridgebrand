/** Live end-to-end visual smoke for BRIDGEBRAND Reading Room.
 * No account, payment or data modifications. Uses Chrome DevTools and the
 * actual published T100 snapshot, not hard-coded example scores.
 */
import {spawn} from 'node:child_process';
import {mkdtempSync, mkdirSync, rmSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';

const base=process.env.BRIDGE_AUDIT_ORIGIN||'https://bridgebrand.co.kr/';
const out=process.env.BRIDGE_QA_OUTPUT||'/tmp/bridge-stage0304';
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
],{stdio:['ignore','ignore','pipe']});
let chromeStartupLog='';
chrome.stderr.on('data',chunk=>{chromeStartupLog+=String(chunk).slice(0,3500);});
chrome.on('error',error=>{chromeStartupLog+=' spawn error: '+String(error);});
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
 for(let n=0;n<110;n++){
  try{
   const r=await fetch('http://127.0.0.1:'+port+'/json/list');
   target=(await r.json()).find(x=>x.type==='page'&&x.webSocketDebuggerUrl);
   if(target)break;
  }catch{}
  await delay(180);
 }
 if(!target)throw Error('Chrome failed to start. process exit='+chrome.exitCode+', signal='+chrome.signalCode+', details='+chromeStartupLog.slice(-2500));
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
  const s3nav=await evalJS("(()=>{let b=document.querySelector('#journeyTrack [data-stage=\"3\"]'); if(!b)return false;b.click();return true})()");
  if(!s3nav)throw Error('Stage 03 button missing');
  await delay(1200);
  const stage3=await evalJS("(()=>{const qs=s=>[...document.querySelectorAll(s)];const name=document.querySelector('#reportPick')?.textContent.trim();return {name,visible:document.querySelector('[data-stage-panel=\"3\"]')?.hidden===false,overview:qs('#rankChangeOverview>p').length,subject:qs('#rankChangeCopy .narrative-group-subject>p:not(.group-subtitle)').length,general:qs('#rankChangeCopy .narrative-group-general>p:not(.group-subtitle)').length,overflow:document.documentElement.scrollWidth>innerWidth+5};})()");
  console.log(JSON.stringify({stage:3,width,...stage3}));
  if(!stage3.visible||stage3.overview!==4||stage3.subject!==10||stage3.general!==9||stage3.overflow)throw Error('Stage 03 visual regression '+JSON.stringify(stage3));
  await evalJS("document.getElementById('rankChangeOverview')?.scrollIntoView({block:'start',behavior:'instant'});true");
  await delay(250);await screenshot('stage03-'+width+'.png');
  const s4nav=await evalJS("(()=>{let b=document.querySelector('#journeyTrack [data-stage=\"4\"]'); if(!b)return false;b.click();return true})()");
  if(!s4nav)throw Error('Stage 04 button missing');
  await delay(1200);
  const stage4=await evalJS("(()=>{const qs=s=>[...document.querySelectorAll(s)];const name=document.querySelector('#reportPick')?.textContent.trim();const pairs=qs('#pairGrid .pair-subject-conclusion').map(e=>e.textContent.trim());return {name,visible:document.querySelector('[data-stage-panel=\"4\"]')?.hidden===false,activitySubject:qs('#activityNarrative .narrative-group-subject>p:not(.group-subtitle)').length,activityGeneral:qs('#activityNarrative .narrative-group-general>p:not(.group-subtitle)').length,pairs:pairs.length,named:pairs.filter(x=>name&&x.includes(name)).length,ends:pairs.filter(x=>/(의미합니다|뜻입니다)\\.$/.test(x)).length,overflow:document.documentElement.scrollWidth>innerWidth+5};})()");
  console.log(JSON.stringify({stage:4,width,...stage4}));
  if(!stage4.visible||stage4.activitySubject!==5||stage4.activityGeneral!==8||stage4.pairs!==15||stage4.named!==15||stage4.ends!==15||stage4.overflow)throw Error('Stage 04 visual regression '+JSON.stringify(stage4));
  await evalJS("(()=>{let d=document.querySelector('.pair-atlas');if(d)d.open=true;let x=document.getElementById('pairGrid');if(x)x.scrollIntoView({block:'start',behavior:'instant'});return true})()");
  await delay(250);await screenshot('stage04-'+width+'.png');
 }
 console.log('PASS: production 03/04 subject-first analysis on 1440/390/320px, selected real UNI T100 subject');
}catch(e){console.error(e);process.exitCode=1}finally{
 try{socket?.close()}catch{}
 chrome.kill('SIGTERM');await delay(150);rmSync(dir,{recursive:true,force:true});
}
