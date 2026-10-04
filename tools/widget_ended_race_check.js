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
   const snapshot=()=>({ended:v.ended,cycles:emotionCycles,time:v.currentTime});
   const cycles=[];
   // 정상 이벤트 직전 워치독이 실행되는 순서를 세 사이클 연속 강제한다.
   for(let i=0;i<3;i++){
    const cycle=await new Promise(resolve=>{v.onended=()=>{const before=snapshot();
      window.__watchdogProbe();const afterWatchdog=snapshot();
      ended();const afterEvent=snapshot();v.onended=ended;
      setTimeout(()=>resolve({before,afterWatchdog,afterEvent,afterGrace:snapshot()}),200);};});
    cycles.push(cycle);
   }
   const normalWarnings=[...warnings];warnings.length=0;
   // 정상 이벤트가 유실되면 복구하고, 그 뒤 늦게 도착한 이벤트는 무시한다.
   const recovered=await new Promise(resolve=>{v.onended=()=>{const before=snapshot();
     window.__watchdogProbe();setTimeout(()=>{const afterWatchdog=snapshot();
       ended();const afterEvent=snapshot();v.onended=ended;
       resolve({before,afterWatchdog,afterEvent,warnings:[...warnings]});},200);};});
   // 복구 예약 직후 두 버퍼를 재사용해도 이전 콜백이 새 상태를 바꾸면 안 된다.
   warnings.length=0;
   const reused=await new Promise((resolve,reject)=>{v.onended=async()=>{try{
     window.__watchdogProbe();
     await setState('happy1',{pin:false});await setState('basic1',{pin:false});
     const before=snapshot();ended();await new Promise(r=>setTimeout(r,200));
     resolve({ownerChanged:clipOwner.get(v)!==oldOwner,before,after:snapshot(),warnings:[...warnings]});
   }catch(e){reject(e);}};const oldOwner=clipOwner.get(v);});
   return {cycles,normalWarnings,recovered,reused};
  })()`);
  console.log(JSON.stringify(result,null,2));
  for(const c of result.cycles)if(c.afterEvent.cycles!==c.before.cycles+1||c.afterGrace.cycles!==c.afterEvent.cycles)throw Error('같은 종료를 워치독과 ended가 중복 처리함');
  if(result.normalWarnings.length)throw Error('정상 종료에 워치독 개입');
  const r=result.recovered;
  if(r.afterWatchdog.cycles!==r.before.cycles+1||r.afterEvent.cycles!==r.afterWatchdog.cycles||r.warnings.length!==1)throw Error('이벤트 유실 복구 또는 지연 이벤트 차단 실패');
  if(!result.reused.ownerChanged||result.reused.after.cycles!==result.reused.before.cycles||result.reused.warnings.length)throw Error('재사용한 버퍼에 오래된 종료 처리 적용');
  console.log('PASS 연속 3사이클 중복 방지, 이벤트 유실 복구, 늦은 이벤트·재사용 버퍼 보호');
 }finally{ws?.close();chrome.kill();server.close();await sleep(500);fs.rmSync(profile,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
