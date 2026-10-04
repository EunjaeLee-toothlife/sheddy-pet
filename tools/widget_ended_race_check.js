// 종료 이벤트 직전에 워치독이 실행돼도 한 사이클을 한 번만 세는지 검사한다.
const fs=require('fs'),os=require('os'),path=require('path'),{spawn}=require('child_process');
const {serve,findChrome}=require('./widget_check');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const server=await serve(),profile=fs.mkdtempSync(path.join(os.tmpdir(),'pet-ended-probe-'));
 const chrome=spawn(findChrome(),['--headless=new','--remote-debugging-port=0',`--user-data-dir=${profile}`,'--autoplay-policy=no-user-gesture-required','--no-first-run','--mute-audio','about:blank'],{stdio:'ignore'});let ws;
 try{
  let port;for(let i=0;i<80&&!port;i++){await sleep(100);try{port=Number(fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split('\n')[0])}catch{}}
  const tab=(await(await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t=>t.type==='page');
  ws=new WebSocket(tab.webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);let n=0;const pending=new Map();
  ws.onmessage=e=>{const d=JSON.parse(e.data);if(pending.has(d.id)){pending.get(d.id)(d);pending.delete(d.id)}};
  const send=(method,params={})=>new Promise(r=>{const id=++n;pending.set(id,r);ws.send(JSON.stringify({id,method,params}))});
  const evaluate=async expression=>{const d=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(d.result.exceptionDetails)throw Error(JSON.stringify(d.result.exceptionDetails));return d.result.result.value};
  await send('Page.enable');
  await send('Page.addScriptToEvaluateOnNewDocument',{source:`const realInterval=window.setInterval;window.setInterval=(fn,...args)=>{if(String(fn).includes('watchdog:'))window.__watchdogProbe=fn;return realInterval(fn,...args);};`});
  await send('Page.navigate',{url:`http://127.0.0.1:${server.address().port}/widget.html?dice=0`});
  await sleep(1000);
  const result=await evaluate(`(async()=>{
   const wait=async(test)=>{const end=Date.now()+15000;while(!test()){if(Date.now()>end)throw Error('timeout');await new Promise(r=>setTimeout(r,10));}};
   await wait(()=>current==='idle1'&&!transitioning);pinnedUntil=Infinity;
   await setState('basic1',{pin:false});await wait(()=>current==='basic1'&&!transitioning&&!fade);
   const warnings=[];console.warn=(...a)=>warnings.push(a.join(' '));const v=vids[front],ended=v.onended;
   return await new Promise(resolve=>{v.onended=()=>{const before={ended:v.ended,cycles:emotionCycles,time:v.currentTime};
     window.__watchdogProbe();const afterWatchdog={ended:v.ended,cycles:emotionCycles,time:v.currentTime};
     ended();const afterEvent={ended:v.ended,cycles:emotionCycles,time:v.currentTime};
     v.onended=ended;resolve({before,afterWatchdog,afterEvent,warnings});};});
  })()`);
  console.log(JSON.stringify(result,null,2));
  if(result.afterEvent.cycles!==result.before.cycles+1)throw Error('같은 종료를 워치독과 ended가 중복 처리함');
  console.log('PASS 한 종료에 한 사이클 증가');
 }finally{ws?.close();chrome.kill();server.close();await sleep(500);fs.rmSync(profile,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
