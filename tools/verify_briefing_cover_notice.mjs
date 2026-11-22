import {spawn} from 'node:child_process';
import {mkdtempSync,mkdirSync,rmSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';import {join} from 'node:path';
const base=process.env.BRIDGE_AUDIT_ORIGIN||'https://bridgebrand.co.kr/';
const out=process.env.BRIDGE_QA_OUTPUT||'/tmp/bridge-cover-test';mkdirSync(out,{recursive:true});
const snapshot=await(await fetch(new URL('data/latest.json',base))).json();
const rows=snapshot.rankings.filter(r=>r.domain==='UNI'&&r.ranking_type==='T100').sort((x,y)=>x.rank-y.rank).slice(0,3);
if(rows.length!==3)throw Error('No real T100');
const qs=new URLSearchParams({field:'UNI',pick:rows[0].external_id,compareA:rows[1].external_id,compareB:rows[2].external_id,language:'한국어',trial:'free'});
const dir=mkdtempSync(join(tmpdir(),'bridge-cover-')),port=19460+Math.floor(Math.random()*200);
const chrome=spawn(process.env.CHROME_BIN||'/usr/bin/google-chrome',['--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--remote-allow-origins=*','--user-data-dir='+dir,'--remote-debugging-port='+port,'about:blank'],{stdio:'ignore'});
const pause=ms=>new Promise(r=>setTimeout(r,ms));let ws,n=0;const pending=new Map();
async function call(method,params={}){let id=++n;return new Promise((resolve,reject)=>{let timer=setTimeout(()=>{pending.delete(id);reject(Error('timeout '+method))},25000);pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params}))})}
async function evaluate(expression){const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value}
async function screenshot(file){let r=await call('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});writeFileSync(join(out,file),Buffer.from(r.data,'base64'))}
async function visit(file){await call('Page.navigate',{url:new URL(file,base).toString()});await pause(1600)}
try{
 let target;
 for(let i=0;i<110;i++){try{target=(await(await fetch('http://127.0.0.1:'+port+'/json/list')).json()).find(o=>o.type==='page'&&o.webSocketDebuggerUrl);if(target)break}catch{}await pause(160)}
 if(!target)throw Error('Chrome failed');
 ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject});
 ws.onmessage=e=>{let v=JSON.parse(e.data);if(!v.id)return;let f=pending.get(v.id);if(!f)return;clearTimeout(f.timer);pending.delete(v.id);v.error?f.reject(Error(v.error.message)):f.resolve(v.result)};
 await call('Page.enable');await call('Runtime.enable');
 for(const width of [1440,1024,430,390,320]){
  await call('Emulation.setDeviceMetricsOverride',{width,height:920,deviceScaleFactor:1,mobile:false});
  await visit('briefing.html');
  const fail=await evaluate(`(()=>{const el=document.getElementById('coverStats'),box=el.querySelector('.briefing-cover-notice'),a=box?.querySelector('a'),r=el.getBoundingClientRect();return{width:innerWidth,display:getComputedStyle(el).display,box:!!box,ratio:box?.getBoundingClientRect().width/r.width,heading:box?.querySelector('strong')?.innerText,cta:a?.getAttribute('href'),overflow:document.documentElement.scrollWidth>innerWidth+5}})()`);
  console.log('MISSING_SELECTION',JSON.stringify(fail));
  if(!fail.box||fail.display!=='block'||fail.ratio<.95||fail.overflow||fail.cta!=='intelligence.html')throw Error('Failed error layout '+JSON.stringify(fail));
  if([1440,390].includes(width))await screenshot('missing-'+width+'.png');
  await visit('briefing.html?'+qs.toString());
  const good=await evaluate(`(()=>{const el=document.getElementById('coverStats');return{width:innerWidth,stats:el.querySelectorAll(':scope>span').length,notice:el.classList.contains('briefing-cover-notice-mode'),overflow:document.documentElement.scrollWidth>innerWidth+5,pdf:!!document.getElementById('savePdfPreview')}})()`);
  console.log('VALID_SELECTION',JSON.stringify(good));
  if(good.stats!==5||good.notice||good.overflow||!good.pdf)throw Error('Valid report regressed '+JSON.stringify(good));
  if([1440,390].includes(width))await screenshot('normal-'+width+'.png');
 }
 console.log('PASS real Chrome: missing vs valid selections across 1440, 1024, 430, 390 and 320');
}catch(e){console.error(e);process.exitCode=1}finally{try{ws?.close()}catch{}chrome.kill('SIGTERM');await pause(130);try{rmSync(dir,{recursive:true,force:true,maxRetries:8,retryDelay:200})}catch(e){console.warn('Chrome temp cleanup deferred:',e.message)}}
