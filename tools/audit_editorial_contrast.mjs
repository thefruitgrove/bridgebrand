/**
 * BRIDGEBRAND PC/mobile screenshot-era contrast audit using existing Chrome.
 * Queries computed foreground/background colours; reports near-invisible text.
 * Background-image photography is excluded (requires separate visual review).
 * This script is READ ONLY and makes no changes to the site or database.
 */
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const executable=process.env.CHROME_BIN || '/usr/bin/google-chrome';
const directory=mkdtempSync(join(tmpdir(),'bridge-contrast-'));
const port=19387+Math.floor(Math.random()*1200);
const chrome=spawn(executable,[
 '--headless','--no-sandbox','--disable-gpu','--no-first-run','--disable-dev-shm-usage',
 '--disable-background-networking','--remote-allow-origins=*',
 '--user-data-dir='+directory,'--remote-debugging-port='+port,'about:blank',
],{stdio:'ignore'});
const delay=(ms)=>new Promise(resolve=>setTimeout(resolve,ms));
let socket;let nextId=0;const pending=new Map();
async function command(method,params={}){
  const id=++nextId;
  return new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>{pending.delete(id);reject(new Error('CDP timeout: '+method));},20000);
    pending.set(id,{resolve,reject,timeout});
    socket.send(JSON.stringify({id,method,params}));
  });
}
const scan=`(()=>{
 const visible=(el)=>{
   const st=getComputedStyle(el),box=el.getBoundingClientRect();
   return st.display!=='none'&&st.visibility!=='hidden'&&Number(st.opacity)>.3&&box.width>3&&box.height>7&&!el.closest('[hidden],[aria-hidden="true"]');
 };
 const rgb=(value)=>{
   const m=String(value||'').match(/rgba?\\(([^)]+)\\)/i);
   if(!m)return null;
   const n=m[1].split(',').map(x=>Number.parseFloat(x));
   return [n[0],n[1],n[2],n.length>3?n[3]:1];
 };
 const linear=(c)=>{c/=255;return c<=.04045?c/12.92:Math.pow((c+.055)/1.055,2.4)};
 const luminance=(col)=>.2126*linear(col[0])+.7152*linear(col[1])+.0722*linear(col[2]);
 const ratio=(fg,bg)=>{let a=luminance(fg),b=luminance(bg);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)};
 const selector='h1,h2,h3,h4,p,span,small,strong,b,em,li,label,a,button,th,td,dt,dd,input';
 const nodes=[...document.querySelectorAll(selector)];
 const problems=[],warnings=[];
 for(let index=0;index<nodes.length;index++){
   // Sample long data lists without limiting investigation to the first screen.
   if(index>2600&&index%4!==0)continue;
   const el=nodes[index],str=(el.innerText||el.value||'').trim().replace(/\\s+/g,' ');
   if(!str||!visible(el)||str.length>290)continue;
   // Photography overlays have deliberate white-on-photo caption text;
   // a solid background-color algorithm cannot measure the actual pixels.
   if(el.closest('.v2-mag-cover-photo,.v2-photoessay,.v2-mag-intel-image,.bridge-intel-photo,.bridge-service-photo,.bridge-pulse-photo'))continue;
   const style=getComputedStyle(el);
   let color=rgb(style.color);if(!color)continue;
   let ancestor=el,background=null,image=false;
   while(ancestor){
      const a=getComputedStyle(ancestor);
      if(a.backgroundImage&&a.backgroundImage!=='none'){image=true;break}
      const bg=rgb(a.backgroundColor);
      if(bg&&bg[3]>.9){background=bg;break}
      ancestor=ancestor.parentElement;
   }
   if(image)continue;
   background??=[255,253,247,1];
   const cr=ratio(color,background);
   // Severe low contrast text (roughly unreadable) is a release blocker.
   const item={tag:el.tagName,cls:String(el.className||'').slice(0,110),text:str.slice(0,72),foreground:style.color,background:background.slice(0,3).join(','),ratio:Number(cr.toFixed(2))};
   if(cr<2.15)problems.push(item);
   else if(cr<3.2)warnings.push(item);
 }
 return {page:location.pathname,title:document.title,count:nodes.length,severe:problems.slice(0,45),warnings:warnings.slice(0,12)};
})()`;
async function start(){
  let page=null;
  for(let i=0;i<65;i++){
    try{
      const response=await fetch('http://127.0.0.1:'+port+'/json/list');
      const pages=await response.json();
      page=pages.find(p=>p.webSocketDebuggerUrl&&p.type==='page');
      if(page)break;
    }catch{}
    await delay(180);
  }
  if(!page)throw new Error('Chrome DevTools did not start');
  socket=new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject});
  socket.onmessage=evt=>{
    const packet=JSON.parse(evt.data);
    if(!packet.id)return;
    const item=pending.get(packet.id);if(!item)return;
    clearTimeout(item.timeout);pending.delete(packet.id);
    if(packet.error)item.reject(new Error(packet.error.message));
    else item.resolve(packet.result);
  };
  await command('Page.enable');
  await command('Runtime.enable');
  const base=process.env.BRIDGE_AUDIT_ORIGIN||'https://bridgebrand.co.kr/';
  const pages=['','cpr.html','gov.html','uni.html','star.html','this-week.html','intelligence.html','subscribe.html','briefing.html','methodology.html','trust.html','publicity.html'];
  const fails=[];
  for(const width of [1440,390]){
    await command('Emulation.setDeviceMetricsOverride',{width,height:930,deviceScaleFactor:1,mobile:false});
    for(const path of pages){
      await command('Page.navigate',{url:new URL(path,base).toString()});
      await delay(1350);
      let outcome=await command('Runtime.evaluate',{expression:scan,returnByValue:true,awaitPromise:true});
      if(outcome.exceptionDetails)throw new Error('Audit JS crashed for '+path);
      const report=outcome.result.value;
      console.log(JSON.stringify({width,...report}));
      if(report.severe.length)fails.push({width,path,count:report.severe.length,samples:report.severe.slice(0,8)});
      if(path==='briefing.html'){
        // The initial page alone cannot catch white text on light paper in
        // stage 1 and hidden-on-load field-pulse charts in stage 2.
        for(const stage of [1,2]){
          const click=await command('Runtime.evaluate',{
            expression:`(()=>{
              const button=document.querySelector('.journey-track button[data-stage="${stage}"]');
              if(!button)return false;
              button.click();
              return true;
            })()`,
            returnByValue:true
          });
          if(!click.result?.value)throw new Error('Briefing navigation missing stage '+stage);
          await delay(280);
          const active=await command('Runtime.evaluate',{
            expression:"document.querySelector('.briefing-stage:not([hidden])')?.getAttribute('data-stage-panel')",
            returnByValue:true
          });
          if(String(active.result?.value)!==String(stage))throw new Error('Briefing step '+stage+' did not activate');
          const result=await command('Runtime.evaluate',{expression:scan,returnByValue:true,awaitPromise:true});
          if(result.exceptionDetails)throw new Error('Briefing contrast scan failed, stage '+stage);
          const stageReport=result.result.value;
          console.log(JSON.stringify({width,stage,...stageReport}));
          if(stageReport.severe.length)fails.push({width,path,stage,count:stageReport.severe.length,samples:stageReport.severe.slice(0,8)});
        }
      }
    }
  }
  if(fails.length){
    console.error('Low-contrast regions requiring correction:',JSON.stringify(fails,null,2));
    process.exitCode=1;
  }else console.log('PASS: no computed near-invisible text in sampled public PC/mobile DOM');
}
try{await start()}catch(err){console.error(err);process.exitCode=1}
finally{try{socket?.close()}catch{}chrome.kill('SIGTERM');await delay(150);rmSync(directory,{recursive:true,force:true})}
