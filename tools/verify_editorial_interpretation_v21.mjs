import {spawn} from 'node:child_process';
import {mkdtempSync,mkdirSync,rmSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';import {join} from 'node:path';
const base=process.env.BRIDGE_AUDIT_ORIGIN||'https://bridgebrand.co.kr/';
const out=process.env.BRIDGE_QA_OUTPUT||'/tmp/bridge-cover-test';mkdirSync(out,{recursive:true});
const snapshot=await(await fetch(new URL('data/latest.json',base))).json();
const selected=['라이즈','엔하이픈','제로베이스원'];
const rows=selected.map(name=>snapshot.rankings.find(r=>r.domain==='ENT'&&r.ranking_type==='T100'&&r.name===name));
if(rows.some(x=>!x||!x.external_id))throw Error('Missing the exact user-approved ENT comparison subjects');
if(rows.length!==3)throw Error('No real T100');
const qs=new URLSearchParams({field:'ENT',pick:rows[0].external_id,compareA:rows[1].external_id,compareB:rows[2].external_id,language:'한국어',trial:'free'});
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
 ws.onmessage=e=>{let v=JSON.parse(e.data);if(v.method==='Runtime.consoleAPICalled')console.log('PAGE_CONSOLE',JSON.stringify((v.params.args||[]).map(x=>x.value||x.description)).slice(0,1500));if(v.method==='Runtime.exceptionThrown')console.log('PAGE_EXCEPTION',JSON.stringify(v.params.exceptionDetails).slice(0,1800));if(!v.id)return;let f=pending.get(v.id);if(!f)return;clearTimeout(f.timer);pending.delete(v.id);v.error?f.reject(Error(v.error.message)):f.resolve(v.result)};
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
  if(good.notice){const details=await evaluate(`document.getElementById('coverStats').innerText`);console.log('INVALID_SELECTION_DETAILS',String(details).slice(0,700));}
  if(good.stats!==5||good.notice||good.overflow||!good.pdf)throw Error('Valid report regressed '+JSON.stringify(good));
  const text=await evaluate(`(()=>{
    const pulse=[...document.querySelectorAll('#fieldPulseNarrative>p')].map(x=>x.innerText);
    const pair=[...document.querySelectorAll('#pairGrid>article')].map(x=>x.innerText);
    const stageRank=document.getElementById('rankChangeOverview').innerText;
    const stagePos=document.getElementById('positionNarrative').innerText;
    const activity=[...document.querySelectorAll('#activityNarrative .narrative-group-subject>p')].filter(x=>x.querySelector('b')).map(x=>x.innerText);
    const priority=[...document.querySelectorAll('#pairPriority article')].map(x=>x.innerText);
    const pdf=document.querySelectorAll('#printReportDocument .print-sheet').length;
    return {pulse: pulse.length,subjectStarts:pulse.slice(4).every(p=>p.includes('라이즈')&&p.indexOf('라이즈')<8),
      pulsePositive:pulse[4]?.includes('관계')&&pulse[6]?.includes('다음 단계'),
      pair:pair.length,pairStructure:pair.every(p=>p.includes('활용 제안')&&p.includes('새로운 결합점수')),
      priority:priority.length,priorityMeaning:priority.every(p=>p.includes('활용 제안')),
      rank:stageRank.includes('74.76')&&stageRank.includes('엔하이픈')&&stageRank.includes('제로베이스원'),
      position:stagePos.includes('해석')||stagePos.includes('관계'),
      activity:activity.length,
      mypick:!!document.querySelector('.position-row-mypick .mypick-marker'),
      pdf:pdf};
  })()`);
  console.log('EDITORIAL_WEB',JSON.stringify({width,...text}));
  if(text.pulse!==7||!text.subjectStarts||text.pair!==15||!text.pairStructure||text.priority!==3||!text.priorityMeaning||!text.rank||!text.position||text.activity!==5||!text.mypick||text.pdf!==33)throw Error('New editorial contract failed '+JSON.stringify(text));
  await evaluate(`document.querySelector('[data-stage="4"]').click();true`);
  await pause(160);
  const contrast=await evaluate(`(()=>{const b=document.querySelector('#pickAnalysisCopy blockquote'),s=getComputedStyle(b),r=b.getBoundingClientRect();return{color:s.color,bg:s.backgroundColor,width:r.width,overflow:document.documentElement.scrollWidth>innerWidth+5}})()`);
  console.log('EDITORIAL_CONTRAST',JSON.stringify({width,...contrast}));
  if(contrast.color!=='rgb(23, 49, 78)'||contrast.bg!=='rgb(234, 243, 255)'||contrast.width<170||contrast.overflow)throw Error('Poor blockquote contrast '+JSON.stringify(contrast));
  if([1440,390].includes(width))await screenshot('editorial-stage04-'+width+'.png');
  await evaluate(`document.querySelector('[data-stage="3"]').click();true`);
  await pause(150);
  if([1440,390].includes(width))await screenshot('editorial-stage03-'+width+'.png');
  await evaluate(`document.querySelector('[data-stage="2"]').click();true`);
  await pause(150);
  if([1440,390].includes(width))await screenshot('editorial-stage02-'+width+'.png');
  if([1440,390].includes(width))await screenshot('normal-'+width+'.png');
 }
 console.log('PASS editorial v2.1: 02/03/04 stages, RIIZE comparison, 15 pairings, contrast and 33-page report at five widths');
}catch(e){console.error(e);process.exitCode=1}finally{try{ws?.close()}catch{}chrome.kill('SIGTERM');await pause(130);try{rmSync(dir,{recursive:true,force:true,maxRetries:8,retryDelay:200})}catch(e){console.warn('Chrome temp cleanup deferred:',e.message)}}
