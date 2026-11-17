import {spawn} from 'node:child_process';
import {mkdtempSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
const dir=mkdtempSync(join(tmpdir(),'newsgraphy-bbi-'));
const out='/tmp/newsgraphy-bbi-check';mkdirSync(out,{recursive:true});
const port=19980+Math.floor(Math.random()*100);
const chrome=spawn(process.env.CHROME_BIN||'/usr/bin/google-chrome',['--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--remote-allow-origins=*','--user-data-dir='+dir,'--remote-debugging-port='+port,'about:blank'],{stdio:['ignore','ignore','pipe']});
let errors='';chrome.stderr.on('data',x=>errors+=String(x).slice(0,2000));
let socket,seq=0;const waiters=new Map(),delay=ms=>new Promise(r=>setTimeout(r,ms));
async function call(method,params={}){const id=++seq;return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{waiters.delete(id);reject(Error(method+' timeout'));},20000);waiters.set(id,{resolve,reject,timer});socket.send(JSON.stringify({id,method,params}));});}
async function evalJS(js){const x=await call('Runtime.evaluate',{expression:js,returnByValue:true,awaitPromise:true});if(x.exceptionDetails)throw Error(x.exceptionDetails.text);return x.result.value;}
try{
 let target;
 for(let i=0;i<100;i++){try{const o=await (await fetch('http://127.0.0.1:'+port+'/json/list')).json();target=o.find(z=>z.type==='page'&&z.webSocketDebuggerUrl);if(target)break;}catch{}await delay(180);}
 if(!target)throw Error('Chrome start failed: '+errors.slice(-1000));
 socket=new WebSocket(target.webSocketDebuggerUrl);
 await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
 socket.onmessage=e=>{const p=JSON.parse(e.data);if(!p.id)return;const w=waiters.get(p.id);if(!w)return;clearTimeout(w.timer);waiters.delete(p.id);p.error?w.reject(Error(p.error.message)):w.resolve(p.result);};
 await call('Page.enable');await call('Runtime.enable');
 await call('Emulation.setDeviceMetricsOverride',{width:1440,height:960,deviceScaleFactor:1,mobile:false});
 await call('Page.navigate',{url:'https://newsgraphy.co.kr/#/'});
 await delay(9000);
 const r=await evalJS(`(()=>{const text=document.body.innerText||'';const index=text.indexOf('BRIDGE Brand Index');return {title:document.title,found:index>=0,excerpt:index<0?text.slice(0,350):text.slice(index,index+900),hasNov16:index>=0&&text.slice(index,index+900).includes('2026-11-16'),hasNov13:index>=0&&text.slice(index,index+900).includes('2026-11-13')}})()`);
 console.log('NEWSGRAPHY_WIDGET',JSON.stringify(r));
 const shot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
 writeFileSync(join(out,'newsgraphy-home.png'),Buffer.from(shot.data,'base64'));
 if(!r.found)throw Error('Live widget not found on rendered Newsgraphy home');
 if(!r.hasNov16)throw Error('BBI widget not displaying verified latest 2026-11-16 snapshot');
 console.log('PASS: live Newsgraphy BBI widget displays verified 2026-11-16 instead of obsolete Nov 13');
}catch(e){console.error(e);process.exitCode=1;}finally{try{socket?.close()}catch{}chrome.kill('SIGTERM');await delay(150);rmSync(dir,{recursive:true,force:true});}
