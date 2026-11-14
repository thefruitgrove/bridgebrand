/** Live Chrome visual contract for reviewed BRIDGEBRAND 2.0 edition.
 * No site writes, no database changes, no synthetic reputation scores.
 * Real current UNI T100 used for live 6-stage and report preview checks.
 */
import {spawn} from 'node:child_process';
import {mkdtempSync,mkdirSync,rmSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';

const base=process.env.BRIDGE_AUDIT_ORIGIN||'https://bridgebrand.co.kr/';
const out=process.env.BRIDGE_QA_OUTPUT||'/tmp/bridge-polish-qa';
mkdirSync(out,{recursive:true});
const snapshot=await(await fetch(new URL('data/latest.json',base),{cache:'no-store'})).json();
const rows=(snapshot.rankings||[]).filter(x=>x.domain==='UNI'&&x.ranking_type==='T100'&&x.external_id).sort((a,b)=>Number(a.rank)-Number(b.rank));
if(snapshot.dataStatus!=='published'||snapshot.recordCount!==400||rows.length<3)throw Error('Published T100 data invalid');
const qs=new URLSearchParams({field:'UNI',pick:String(rows[2].external_id),compareA:String(rows[1].external_id),compareB:String(rows[0].external_id),language:'한국어',trial:'free'});
const temp=mkdtempSync(join(tmpdir(),'bridge-polish-'));
const port=19890+Math.floor(Math.random()*500);
const chrome=spawn(process.env.CHROME_BIN||'/usr/bin/google-chrome',[
 '--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--no-first-run',
 '--remote-allow-origins=*','--user-data-dir='+temp,'--remote-debugging-port='+port,'about:blank'
],{stdio:'ignore'});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
let socket,seq=0;const pending=new Map();
async function call(method,params={}){
 const id=++seq;return new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>{pending.delete(id);reject(Error('Chrome timeout '+method));},25000);
  pending.set(id,{resolve,reject,timer});
  socket.send(JSON.stringify({id,method,params}));
 });
}
async function evalJS(expression){
 const response=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
 if(response.exceptionDetails)throw Error('Browser evaluation failed '+JSON.stringify(response.exceptionDetails).slice(0,500));
 return response.result.value;
}
async function shot(name,selector){
 if(selector){await evalJS(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e?.scrollIntoView({block:'start',behavior:'instant'});return !!e})()`);await delay(200)}
 const img=await call('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});
 writeFileSync(join(out,name),Buffer.from(img.data,'base64'));
}
async function open(path,ms=2000){
 await call('Page.navigate',{url:new URL(path,base).toString()});
 await delay(ms);
}
async function metrics(expression){
 const data=await evalJS(expression);
 if(data.overflow)throw Error('Viewport horizontal overflow: '+JSON.stringify(data));
 console.log(JSON.stringify(data));
 return data;
}
function assert(ok,msg,data){if(!ok)throw Error(msg+': '+JSON.stringify(data))}
try{
 let target;
 for(let i=0;i<60;i++){
  try{const r=await fetch('http://127.0.0.1:'+port+'/json/list');target=(await r.json()).find(x=>x.type==='page'&&x.webSocketDebuggerUrl);if(target)break}catch{}
  await delay(200);
 }
 if(!target)throw Error('Chrome failed to start');
 socket=new WebSocket(target.webSocketDebuggerUrl);
 await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject});
 socket.onmessage=event=>{
  const packet=JSON.parse(event.data);if(!packet.id)return;
  const p=pending.get(packet.id);if(!p)return;clearTimeout(p.timer);pending.delete(packet.id);
  packet.error?p.reject(Error(packet.error.message)):p.resolve(packet.result);
 };
 await call('Page.enable');await call('Runtime.enable');
 const vps=[1440,390,320];
 for(const width of vps){
  await call('Emulation.setDeviceMetricsOverride',{width,height:940,deviceScaleFactor:1,mobile:false});
  await open('',1700);
  const home=await metrics(`(()=>{
   const a=document.querySelector('.v2-mag-issue');
   const c=document.querySelector('.v2-photo-credit');
   const d=document.querySelector('.v2-footer-bottom>span');
   return {page:'home',width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth+5,
    issue:a?.innerText,oldJournal:a?.innerText?.includes('JOURNAL'),
    oldNumber:a?.innerText?.includes('ISSUE 02'),
    photoFont:c?getComputedStyle(c).fontSize:null,
    operatorFont:d?getComputedStyle(d).fontSize:null};
  })()`);
  assert(home.issue?.includes('REPUTATION INTELLIGENCE')&&!home.oldJournal&&!home.oldNumber,'Homepage masthead unchanged',home);
  assert(home.photoFont===home.operatorFont,'Footer photo-credit size differs from operator attribution',home);
  if(width===1440)await shot('home-cover-'+width+'.png','.v2-mag-cover');
  for(const name of ['cpr','gov','uni','star']){
   await open(name+'.html',1500);
   const page=await metrics(`(()=>{
    const h=document.querySelector('.bridge-field-headline');
    const lines=[...document.querySelectorAll('.bridge-field-line')];
    return {page:location.pathname,width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth+5,
      count:lines.length,headline:h?.textContent,
      lineHeights:lines.map(x=>Math.round(x.getBoundingClientRect().height)),
      lineOverflow:lines.map(x=>x.scrollWidth>x.clientWidth+4),
      font:h?getComputedStyle(h).fontFamily:null};
   })()`);
   assert(page.count===2,'Sector headline lacks two authored lines',page);
   if(width===1440)assert(!page.lineOverflow.some(Boolean),'Desktop sector title extends beyond paper column',page);
   if(width===1440)await shot('field-'+name+'-'+width+'.png','.list-hero-photo');
  }
  await open('intelligence.html',2000);
  const intel=await metrics(`(()=>{
    const parent=document.querySelector('#trioSnapshotMeta')?.parentElement;
    return {page:'intelligence',width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth+5,
      escaped:parent?.innerText?.includes('\\\\n'),peer:!!document.querySelector('#bridgePeerSuggest'),
      journey:!!document.querySelector('[data-bridge-journey="v2"]')};
   })()`);
  assert(!intel.escaped&&intel.peer&&intel.journey,'Intelligence comparison help contains escaped newline',intel);
  await open('briefing.html?'+qs.toString(),3400);
  const cover=await metrics(`(()=>{
    const h=document.querySelector('#coverTitle');
    const deck=document.querySelector('#coverDeck');
    return {page:'briefing-cover',width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth+5,
      titleLines:h?.querySelectorAll('.br-cover-title-line').length,title:h?.textContent,
      deck:deck?.textContent,deckSingle:deck?.classList.contains('br-deck-long')===false,
      imageStyles:!!document.querySelector('link[href*="bridge-v2-report-edition.css"]')};
   })()`);
  assert(cover.titleLines===3&&cover.imageStyles,'Three-line briefing cover or PDF stylesheet missing',cover);
  if(width===1440)await shot('briefing-cover-1440.png','#reportTop');
  const click=async stage=>{
   const clicked=await evalJS(`(()=>{const b=document.querySelector('#journeyTrack [data-stage="${stage}"]');if(!b)return false;b.click();return true})()`);
   assert(clicked,'Cannot open stage '+stage,{});
   await delay(450);
  };
  await click(1);
  const guide=await metrics(`(()=>{
    const note=document.querySelector('.bridge-guide-copy .lead-copy');
    const metric=document.querySelector('#metricList');
    const values=[...metric.querySelectorAll('.metric-row strong')];
    return {page:'guide',width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth+5,
      leadPad:note?getComputedStyle(note).paddingLeft:null,
      leadBorder:note?getComputedStyle(note).borderLeftWidth:null,
      total:values.length,textual:values.filter(x=>x.classList.contains('metric-textual')).map(x=>x.textContent),
      textualFont:values.find(x=>x.classList.contains('metric-textual'))?getComputedStyle(values.find(x=>x.classList.contains('metric-textual'))).fontFamily:null};
   })()`);
  assert(parseFloat(guide.leadPad)>=15&&parseFloat(guide.leadBorder)>0&&guide.total>=8,'Guide typography or metric classification failed',guide);
  if(width===1440)await shot('guide-metrics-1440.png','#sg-index');
  for(const [stage,id,count] of [[3,'positionNarrative',4],[4,'radarExplanation',3]]){
   await click(stage);
   const data=await metrics(`(()=>{
    const e=document.getElementById(${JSON.stringify(id)});
    const nodes=[...e.querySelectorAll('p>b')];
    return {page:'labels-${stage}',width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth+5,
      count:nodes.length,linebreaks:nodes.filter(x=>x.querySelector('br')).length,
      fonts:nodes.map(x=>getComputedStyle(x).fontFamily)};
   })()`);
   assert(data.count>=count&&data.linebreaks>=count,'Stage 03/04 balanced editorial headings missing',data);
   if(width===1440)await shot('stage-'+stage+'-explanations.png','#'+id);
  }
  await click(6);
  await evalJS("document.getElementById('previewPdf').click();true");
  await delay(1700);
  const pdf=await metrics(`(()=>{
    const one=document.querySelector('.print-sheet[data-page="1"]');
    const img=one?.querySelector('.print-cover-editorial-photo img');
    const figure=one?.querySelector('.print-cover-editorial-photo');
    const meta=one?.querySelector('.print-cover-meta');
    const overlap=(a,b)=>{if(!a||!b)return false;const x=a.getBoundingClientRect(),y=b.getBoundingClientRect();return Math.min(x.right,y.right)-Math.max(x.left,y.left)>1&&Math.min(x.bottom,y.bottom)-Math.max(x.top,y.top)>1};
    return {page:'pdf-preview',width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth+5,
      pages:document.querySelectorAll('.print-sheet').length,
      loaded:!!img&&img.naturalWidth>0,
      photo:!!figure,brand:!!one?.querySelector('.print-brand-name'),
      figureAndMetaOverlap:overlap(figure,meta),
      coverBackground:one?getComputedStyle(one).backgroundImage:null,
      footerBg:document.querySelector('.print-sheet[data-page="2"] .print-sheet-footer')?getComputedStyle(document.querySelector('.print-sheet[data-page="2"] .print-sheet-footer')).backgroundColor:null};
   })()`);
  assert(pdf.pages===29&&pdf.loaded&&pdf.brand,'Magazine PDF cover or report pages missing',pdf);
  if(width===1440)assert(!pdf.figureAndMetaOverlap,'Cover photo overlaps the report metadata',pdf);
  if(width===1440)await shot('pdf-cover-1440.png','.print-sheet[data-page="1"]');
  if(width===390)await shot('pdf-mobile-cover-390.png','.print-sheet[data-page="1"]');
 }
 console.log('PASS: home masthead+credits, 4 exact field titles, Intelligence, 3-line cover, value text, 03/04 headings, actual photo-led 29-page report on PC/mobile.');
}catch(error){console.error(error);process.exitCode=1}
finally{try{socket?.close()}catch{}chrome.kill('SIGTERM');await delay(180);rmSync(temp,{recursive:true,force:true})}
