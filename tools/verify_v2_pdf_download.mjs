/** Live generated PDF smoke for the existing BRIDGEBRAND 6-stage report engine.
 * No account, payment or data modifications. Uses Chrome DevTools and the
 * actual published T100 snapshot, not hard-coded example scores.
 */
import {spawn} from 'node:child_process';
import {mkdtempSync, mkdirSync, rmSync, writeFileSync, readdirSync, readFileSync, statSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';

const base=process.env.BRIDGE_AUDIT_ORIGIN||'https://bridgebrand.co.kr/';
const out=process.env.BRIDGE_QA_OUTPUT||'/tmp/bridge-pdf-qa';
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

  // This is a real download, not merely a check that the PDF button exists.
  try{
    await call('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:out,eventsEnabled:true});
  }catch(e){
    await call('Page.setDownloadBehavior',{behavior:'allow',downloadPath:out});
  }
  await call('Emulation.setDeviceMetricsOverride',{width:1280,height:920,deviceScaleFactor:1,mobile:false});
  await call('Page.navigate',{url});
  await delay(3700);
  await evalJS(`(()=>{
    const button=document.querySelector('#journeyTrack [data-stage="6"]');
    if(!button)return false;button.click();return true;
  })()`);
  await delay(900);
  const ready=await evalJS(`(()=>{
    const $=id=>document.getElementById(id);
    return {ready:!!window.html2canvas&&!!window.jspdf?.jsPDF,
      reportId:$('reportId')?.textContent,save:!!$('savePdf')&&!$('savePdf').disabled,
      print:!!$('printReport'),preview:!!$('previewPdf'),
      stage:$('trialConversion')?.hidden===false};
  })()`);
  console.log(JSON.stringify({kind:'pdf-ready',...ready}));
  if(!ready.ready||!ready.save||!ready.print||!ready.preview||!ready.stage||!ready.reportId||ready.reportId==='BR-REPORT'){
    throw Error('PDF prerequisite failed '+JSON.stringify(ready));
  }
  // Build the exact report pages but do not assume the visually redesigned
  // on-screen chapters are the PDF print template.
  await evalJS("document.getElementById('previewPdf').click();true");
  await delay(1900);
  const preview=await evalJS(`(()=>{
    const $=id=>document.getElementById(id);
    return {previewMode:document.body.classList.contains('pdf-preview-mode'),
      pages:$('printReportDocument')?.querySelectorAll('.print-sheet').length,
      reportId:$('reportId')?.textContent};
  })()`);
  console.log(JSON.stringify({kind:'pdf-preview',...preview}));
  if(!preview.previewMode||preview.pages<17)throw Error('PDF print preview had insufficient actual pages: '+JSON.stringify(preview));
  await evalJS("document.getElementById('exitPdfPreview').click();true");
  await delay(450);
  await evalJS("document.getElementById('savePdf').click();true");
  let downloaded;
  for(let round=0;round<240;round++){
    const filenames=readdirSync(out);
    const file=filenames.find(f=>f.endsWith('.pdf')&&!f.endsWith('.crdownload'));
    if(file && !filenames.some(f=>f.endsWith('.crdownload'))){
      const filepath=join(out,file);
      if(statSync(filepath).size>15000){
        downloaded=filepath;
        break;
      }
    }
    const working=await evalJS("document.getElementById('savePdf')?.getAttribute('aria-busy')");
    if(round>10&&working===null&&!file){
      throw Error('PDF generation finished without a downloaded file');
    }
    await delay(900);
  }
  if(!downloaded)throw Error('No valid downloaded PDF within smoke-test timeout');
  const head=readFileSync(downloaded).subarray(0,8).toString('ascii');
  if(!head.startsWith('%PDF-'))throw Error('Generated output is not a PDF: '+head);
  console.log(JSON.stringify({kind:'pdf-file',file:downloaded,size:statSync(downloaded).size,
    magic:head,pageCountInPreview:preview.pages}));
  await screenshot('pdf-stage6-reviewed.png');
  console.log('PASS: actual STANDARD PDF render, preview and downloaded PDF file with published UNI data');

}catch(e){console.error(e);process.exitCode=1}finally{
 try{socket?.close()}catch{}
 chrome.kill('SIGTERM');await delay(150);rmSync(dir,{recursive:true,force:true});
}
