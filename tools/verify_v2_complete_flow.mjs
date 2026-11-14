/** BRIDGEBRAND 2.0 public-site full journey test.
 * Chrome DevTools. Checks only real published T100 entities, never mocks scores,
 * never mutates production, never claims an unconfigured checkout is active.
 */
import {spawn} from 'node:child_process';
import {mkdtempSync,mkdirSync,rmSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';

const base=process.env.BRIDGE_AUDIT_ORIGIN||'https://bridgebrand.co.kr/';
const out=process.env.BRIDGE_QA_OUTPUT||'/tmp/bridge-full-journey';
mkdirSync(out,{recursive:true});
const resp=await fetch(new URL('data/latest.json',base),{cache:'no-store'});
if(!resp.ok)throw Error('Published snapshot unavailable: '+resp.status);
const snapshot=await resp.json();
if(snapshot.dataStatus!=='published'||snapshot.recordCount!==400||(snapshot.rankings||[]).length!==400)throw Error('Unpublished/incomplete 400-subject data');
const uni=snapshot.rankings.filter(x=>x.domain==='UNI'&&x.ranking_type==='T100'&&x.external_id).sort((a,b)=>a.rank-b.rank);
if(uni.length!==100)throw Error('UNI T100 snapshot incomplete');
const qs=new URLSearchParams({field:'UNI',pick:String(uni[2].external_id)});
const dir=mkdtempSync(join(tmpdir(),'bridge-full-'));
const port=19590+Math.floor(Math.random()*900);
const chrome=spawn(process.env.CHROME_BIN||'/usr/bin/google-chrome',[
 '--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--no-first-run',
 '--remote-allow-origins=*','--user-data-dir='+dir,'--remote-debugging-port='+port,'about:blank'
],{stdio:'ignore'});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
let socket,seq=0;const waiters=new Map();
async function call(method,params={}){
 const id=++seq;
 return new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>{waiters.delete(id);reject(Error('CDP timeout '+method));},25000);
  waiters.set(id,{resolve,reject,timer});
  socket.send(JSON.stringify({id,method,params}));
 });
}
async function evalJS(expression){
 const reply=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
 if(reply.exceptionDetails)throw Error('Page evaluation failed: '+JSON.stringify(reply.exceptionDetails).slice(0,400));
 return reply.result.value;
}
async function shot(name,selector){
 if(selector){
  await evalJS(`(()=>{
    const el=document.querySelector(${JSON.stringify(selector)});
    if(el)el.scrollIntoView({block:'start',behavior:'instant'});
    return !!el;
  })()`);
  await delay(150);
 }
 const res=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false,fromSurface:true});
 writeFileSync(join(out,name),Buffer.from(res.data,'base64'));
}
async function navigate(path,ms=2400){
 await call('Page.navigate',{url:new URL(path,base).toString()});
 await delay(ms);
}
async function size(width,height=940){
 await call('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});
}
async function checkPage(width,kind,stage=0){
 const state=await evalJS(`(()=>{
  const $=q=>document.querySelector(q);
  const sel=q=>$(q);
  const photoLoaded=q=>!!sel(q)&&sel(q).complete&&sel(q).naturalWidth>0;
  const out={
    url:location.pathname,
    width:innerWidth,
    overflow:document.documentElement.scrollWidth>innerWidth+5,
    heading:sel('h1')?.innerText?.slice(0,90)||'',
  };
  if(${JSON.stringify(kind)}==='brief'){
    const stage=${stage};
    out.stage=stage;
    out.active=sel('[data-stage-panel="'+stage+'"]')?.hidden===false;
    out.stageCount=document.querySelectorAll('[data-stage-panel]').length;
    out.pager=!!sel('#nextStage')&&!!sel('#prevStage');
    if(stage===1){
      out.photo=photoLoaded('.bridge-guide-photo img');
      out.note=!!sel('.bridge-example-note');
      out.axes=sel('#sg-axes')?.querySelectorAll('.axis-definitions article').length;
    }else if(stage===2){
      out.photo=photoLoaded('#bridgePulsePhoto');
      out.rows=sel('#fieldPulseList')?.children.length;
      out.bars=sel('#fieldPulseBars')?.querySelectorAll('.pulse-bar').length;
    }else if(stage===3){
      out.photo=photoLoaded('.bridge-chapter-position img');
      out.rows=sel('#positionRows')?.querySelectorAll('tr').length;
    }else if(stage===4){
      out.radar=sel('#briefingRadar')?.childElementCount||0;
      out.pairs=sel('#pairGrid')?.children.length;
      out.axes=sel('#resceneBars')?.children.length;
    }else if(stage===5){
      out.photo=photoLoaded('.bridge-publicity-photo img');
      out.title=sel('#publicityHeadline')?.textContent?.trim()||'';
      out.storyLength=sel('#publicityBody')?.innerText?.trim().length||0;
    }else if(stage===6){
      out.id=sel('#reportId')?.textContent?.trim()||'';
      out.pick=sel('#reportPick')?.textContent?.trim()||'';
      out.pdf=!!sel('#savePdf')&&!!sel('#previewPdf')&&!!sel('#printReport');
      out.conversion=sel('#trialConversion')?.hidden===false;
    }
  }else if(${JSON.stringify(kind)}==='sector'){
    out.guide=!!sel('.bridge-sector-guide');
    out.photo=photoLoaded('.bridge-sector-spread img');
    out.ranking=!!sel('.ranking-workspace');
    out.period=!!sel('.period-selector');
    out.manualAnalysis=!!sel('.bridge-sector-spread-copy a[href*="intelligence.html"]');
  }else if(${JSON.stringify(kind)}==='weekly'){
    out.photo=photoLoaded('.bridge-weekly-feature img');
    out.feature=!!sel('.bridge-weekly-feature');
    out.read=!!sel('.tw-read');
  }
  return out;
 })()`);
 if(state.overflow)throw Error('Horizontal overflow: '+JSON.stringify(state));
 if(kind==='brief'){
  if(!state.active||state.stageCount!==6||!state.pager)throw Error('Broken stage nav: '+JSON.stringify(state));
  if([1,2,3,5].includes(stage)&&!state.photo)throw Error('Missing chapter illustration: '+JSON.stringify(state));
  if(stage===1&&(!state.note||state.axes!==6))throw Error('Invalid guide stage: '+JSON.stringify(state));
  if(stage===2&&(state.rows!==20||state.bars!==20))throw Error('Invalid actual published TOP20: '+JSON.stringify(state));
  if(stage===3&&state.rows!==3)throw Error('Invalid 3-way actual ranking comparison: '+JSON.stringify(state));
  if(stage===4&&(!state.radar||state.pairs!==15||state.axes<6))throw Error('Invalid 6 axes / 15 pairs: '+JSON.stringify(state));
  if(stage===5&&(state.title.length<10||state.storyLength<100))throw Error('Incomplete PUBLICITY stage: '+JSON.stringify(state));
  if(stage===6&&(!state.pdf||!state.conversion||state.id==='BR-REPORT'||!state.pick||state.pick==='—'))throw Error('Invalid report output stage: '+JSON.stringify(state));
 }else if(kind==='sector'&&(!state.guide||!state.photo||!state.ranking||!state.period||!state.manualAnalysis)){
  throw Error('Broken sector data journal: '+JSON.stringify(state));
 }else if(kind==='weekly'&&(!state.photo||!state.feature||!state.read))throw Error('Broken weekly editorial: '+JSON.stringify(state));
 console.log(JSON.stringify({kind,...state}));
}
try{
 let target;
 for(let i=0;i<70;i++){
  try{
   const r=await fetch('http://127.0.0.1:'+port+'/json/list');
   target=(await r.json()).find(x=>x.type==='page'&&x.webSocketDebuggerUrl);
   if(target)break;
  }catch{}
  await delay(180);
 }
 if(!target)throw Error('Chrome startup failed');
 socket=new WebSocket(target.webSocketDebuggerUrl);
 await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject});
 socket.onmessage=event=>{
  const packet=JSON.parse(event.data);if(!packet.id)return;
  const q=waiters.get(packet.id);if(!q)return;
  clearTimeout(q.timer);waiters.delete(packet.id);
  packet.error?q.reject(Error(packet.error.message)):q.resolve(packet.result);
 };
 await call('Page.enable');await call('Runtime.enable');

 // Test real homepage subject handoff indirectly through its existing URL
 // contract. Intelligence must preserve MY PICK, and optional suggestions
 // are explicitly accepted by the user.
 await size(1440);
 await navigate('intelligence.html?'+qs.toString()+'#trioBeta');
 let selection=await evalJS(`(()=>{
    const $=id=>document.getElementById(id);
    if(!$('trioPick1')||!$('bridgePeerSuggest'))return {ready:false};
    $('bridgePeerSuggest').click();
    return {ready:true,pick:$('trioPick1').value,
      a:$('trioPick2').value,b:$('trioPick3').value,
      runEnabled:!$('trioRun').disabled,
      helperText:$('bridgePeerStatus').textContent,
      journey:!!document.querySelector('[data-bridge-journey="v2"]')};
 })()`);
 console.log(JSON.stringify({kind:'intelligence-handoff',...selection}));
 if(!selection.ready||selection.pick!==uni[2].external_id||
    !selection.a||!selection.b||!selection.runEnabled||!selection.journey||
    new Set([selection.pick,selection.a,selection.b]).size!==3){
     throw Error('Intelligence selection handoff failed: '+JSON.stringify(selection));
 }
 await shot('00-intelligence-desktop.png','.bridge-peer-help');
 await evalJS("document.getElementById('trioRun').click();true");
 await delay(2400);
 const actualHref=await evalJS('location.href');
 if(!actualHref.includes('briefing')||!actualHref.includes('field=UNI'))throw Error('Briefing did not start after confirmed selection: '+actualHref);

 const stages={
  1:'#sg-definition',2:'#fp-current',3:'.bridge-chapter-position',
  4:'#ri-structure',5:'#pb-headline',6:'.bridge-report-folio'
 };
 for(const width of [1440,390,320]){
  await size(width);
  await navigate(new URL(actualHref).pathname.slice(1)+new URL(actualHref).search,2400);
  for(const step of (width===320?[1,3,4,5,6]:[1,2,3,4,5,6])){
   await evalJS(`(()=>{
    const b=document.querySelector('#journeyTrack button[data-stage="${step}"]');
    if(!b)return false;b.click();return true;
   })()`);
   await delay(430);
   await checkPage(width,'brief',step);
   if(width!==320||[3,4,6].includes(step)){
     await shot('brief-'+width+'-stage-'+step+'.png',stages[step]);
   }
  }
  if(width===1440){
   const data=await evalJS(`(()=>{
     const link=document.querySelector('#trialConversion a[href*="SNAPSHOT"]');
     if(!link)return {ok:false};
     link.addEventListener('click',ev=>ev.preventDefault(),{once:true,capture:true});
     link.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
     const dest=new URL(link.href);
     return {ok:true,field:dest.searchParams.get('field'),targets:dest.searchParams.get('targets'),
       href:link.href,preview:document.querySelector('#previewPdf')?.disabled};
   })()`);
   console.log(JSON.stringify({kind:'report-to-service',...data}));
   if(!data.ok||data.field!=='UNI'||!data.targets)throw Error('Report-to-service context lost: '+JSON.stringify(data));
  }
 }
 for(const width of [1440,390]){
  await size(width);
  for(const name of ['cpr','gov','uni','star']){
   await navigate(name+'.html',1600);
   await checkPage(width,'sector');
   if(width===1440)await shot('sector-'+name+'-'+width+'.png','.bridge-sector-spread');
  }
  await navigate('this-week.html',1600);
  await checkPage(width,'weekly');
  if(width===1440)await shot('weekly-'+width+'.png','.bridge-weekly-feature');
 }
 console.log('PASS: all 6 live stages, 6 axes, 15 pair analyses, PDF controls, three actual comparisons, four data journals, weekly and responsive sizes 1440/390/320.');
}catch(err){console.error(err);process.exitCode=1}
finally{
 try{socket?.close()}catch{}
 chrome.kill('SIGTERM');await delay(170);
 rmSync(dir,{recursive:true,force:true});
}
