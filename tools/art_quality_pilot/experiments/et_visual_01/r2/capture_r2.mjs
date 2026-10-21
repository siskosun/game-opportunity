/** Browser QA for candidate-02-r2, plus separately labeled production-core state mirrors. */
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir, readdir } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { join, resolve } from 'node:path';

const root=resolve(process.env.ECHO_VISUAL_OUTPUT||'artifacts/candidate-02-r2');
const source=resolve(process.env.ECHO_VISUAL_SOURCE||'_trial_echo');
const origin=process.env.ECHO_VISUAL_ORIGIN||'http://127.0.0.1:8765';
const qaOrigin=process.env.ECHO_QA_ORIGIN||'http://127.0.0.1:8766';
const moduleRoot=process.env.ECHO_PLAYWRIGHT_ROOT;
if(!moduleRoot)throw new Error('ECHO_PLAYWRIGHT_ROOT required');
const require=createRequire(join(resolve(moduleRoot),'package.json'));
const {chromium}=require('playwright');
const sha=b=>createHash('sha256').update(b).digest('hex');
const fileEntry=async(file)=>{const bytes=await readFile(file);return {name:file.slice(root.length+1),sha256:sha(bytes),bytes:bytes.length};};
const viewports=[
{id:'portrait-360',width:360,height:800},
{id:'portrait-390',width:390,height:844},
{id:'landscape-844',width:844,height:390},
{id:'desktop-1280',width:1280,height:900}];
const scenes=['rail-preview','rail-inflight','blocked-edge','lost','won-room1','won-room2','won-room3'];
const report={schema:'ET-VISUAL-02-qa-v1',candidate:'candidate-02-r2',
 selected_parent:'candidate-02-r1', pinned_source_sha:'38b9daa1adf78002c8ec5349c269a4ce31959d8f',
 provenance:'real Chrome run against ephemeral candidate and separately labeled core-driven QA harness',
 production_approved:false,game_exp_lifecycle_mutated:false,real_touch_device:false,
 browser:null, live_pages:[], state_mirrors:[], technical_ok:false};
await mkdir(root,{recursive:true});
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
report.browser={version:browser.version(),mode:'Playwright Chrome Ubuntu',device:'CSS viewport emulation, not a mobile device'};
let hasFailures=false;
async function save(page,relative){
 const target=join(root,relative);
 await page.screenshot({path:target,animations:'disabled',fullPage:false});
 return fileEntry(target);
}
function listen(page){const errors=[];page.on('pageerror',e=>errors.push('pageerror:'+String(e)));
 page.on('console',m=>{if(m.type()==='error')errors.push('console:'+m.text())});
 page.on('requestfailed',r=>errors.push('network:'+r.url()));
 page.on('response',r=>{if(r.status()>=400)errors.push('HTTP '+r.status()+':'+r.url());});return errors;}
try{
 for(const viewport of viewports){
  const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},deviceScaleFactor:1});
  await context.addInitScript(()=>{const original=Crypto.prototype.getRandomValues;Crypto.prototype.getRandomValues=function(a){if(a instanceof Uint32Array&&a.length===1){a[0]=3;return a;}return original.call(this,a);};});
  const page=await context.newPage(),errors=listen(page);
  const response=await page.goto(origin+'/',{waitUntil:'networkidle',timeout:30000});
  await page.waitForSelector('#et-readable-hud[data-state]',{timeout:15000});
  const snapshot=async()=>page.evaluate(()=>{
    const hud=document.getElementById('et-readable-hud');
    const canvas=document.getElementById('game');const bbox=canvas.getBoundingClientRect();
    const elements=['room','difficulty','style','restart'].map(id=>document.getElementById(id));
    return {viewport:[innerWidth,innerHeight],width:document.documentElement.scrollWidth,
      canvas:{x:bbox.x,y:bbox.y,width:bbox.width,height:bbox.height,bottom:bbox.bottom},
      hud:{visible:getComputedStyle(hud).display!=='none',state:hud.dataset.state,
        cue:document.getElementById('et-hud-cue')?.textContent,
        goal:document.getElementById('et-hud-goal')?.textContent,
        clock:document.getElementById('et-hud-time')?.textContent,
        fontPx:parseFloat(getComputedStyle(hud).fontSize),
        cueAlign:getComputedStyle(document.getElementById('et-hud-cue')).textAlign},
      controls:elements.map(el=>{const r=el.getBoundingClientRect();return {id:el.id,w:r.width,h:r.height,x:r.x,y:r.y,align:getComputedStyle(el).textAlign};}),
      status:document.getElementById('status').textContent,
    };
  });
  const initial=await snapshot();
  const initialImg=await save(page,`${viewport.id}-initial.png`);
  const issues=[];
  if(!response||response.status()!==200)issues.push('HTTP != 200');
  if(initial.width>viewport.width+1)issues.push('horizontal overflow');
  if(initial.canvas.y<0||initial.canvas.bottom>viewport.height+1)issues.push('canvas clipped in initial viewport');
  const portrait=viewport.width<=390;
  if(portrait){
    if(!initial.hud.visible)issues.push('readable external HUD missing');
    if(initial.hud.fontPx<13)issues.push('readable HUD font too small');
    if(initial.hud.cueAlign!=='left')issues.push('new HUD text not left aligned');
    if(!initial.hud.clock?.includes('潮汐')||!initial.hud.goal?.includes('潮印'))issues.push('live HUD missing state');
    if(initial.controls.some(c=>c.h<44))issues.push('portrait touch-target box under 44 CSS px');
    if(Math.abs(initial.controls[0].w-initial.controls[1].w)>1||Math.abs(initial.controls[2].w-initial.controls[3].w)>1)issues.push('portrait grid widths diverge');
  }else if(initial.hud.visible)issues.push('new mobile HUD unexpectedly visible outside portrait');
  await page.locator('#game').focus();
  await page.keyboard.down('ArrowRight');await page.keyboard.down('Space');await page.waitForTimeout(290);
  await page.keyboard.up('Space');await page.keyboard.up('ArrowRight');await page.waitForTimeout(650);
  const afterInput=await snapshot();
  const inputImg=await save(page,`${viewport.id}-after-input.png`);
  if(afterInput.width>viewport.width+1||afterInput.canvas.bottom>viewport.height+1)issues.push('input caused overflow or clipped canvas');
  await page.locator('#room').selectOption('1');await page.waitForTimeout(140);
  const changed=await snapshot();
  const changedImg=await save(page,`${viewport.id}-room2.png`);
  if(portrait&&!changed.hud.goal)issues.push('changed room did not present a goal state');
  if(portrait){const label=await page.locator('#et-hud-level').textContent();if(!label.includes('2/3'))issues.push('room selection not reflected in live HUD');}
  if(errors.length)issues.push(...errors);
  report.live_pages.push({viewport,initial,after_input:afterInput,room2:changed,
    screenshots:[initialImg,inputImg,changedImg],errors,issues,passed:issues.length===0});
  if(issues.length)hasFailures=true;
  await context.close();
 }
 for(const scenario of scenes){
  const viewport=scenario.includes('rail')||scenario.includes('blocked')?{width:360,height:800}:{width:844,height:390};
  const ctx=await browser.newContext({viewport,deviceScaleFactor:1});const page=await ctx.newPage();const errors=listen(page);
  const response=await page.goto(qaOrigin+'/qa_states.html?scenario='+encodeURIComponent(scenario),{waitUntil:'networkidle',timeout:30000});
  await page.waitForFunction(()=>window.__ET_QA_READY__||window.__ET_QA_ERROR__,{timeout:16000});
  const summary=await page.evaluate(()=>({ok:!!window.__ET_QA_READY__,error:window.__ET_QA_ERROR__||null,details:window.__ET_QA_SUMMARY__||null,
    canvasRect:(()=>{let r=document.getElementById('test-game').getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom};})()}));
  const screenshot=await save(page,`state-${scenario}.png`);
  const issues=[];
  if(!response||response.status()!==200||!summary.ok)issues.push('QA core state failed: '+summary.error);
  if(summary.canvasRect.bottom>viewport.height+1)issues.push('QA state canvas clipped');
  if(errors.length)issues.push(...errors);
  report.state_mirrors.push({scenario,viewport,http:response?.status(),summary,screenshot,issues,passed:issues.length===0});
  if(issues.length)hasFailures=true;
  await ctx.close();
 }
}finally{await browser.close();}
const distAssets=(await readdir(join(source,'dist','assets'))).filter(x=>x.endsWith('.js')).sort();
report.build_files=await Promise.all([join(source,'dist','index.html'),...distAssets.map(x=>join(source,'dist','assets',x))].map(async f=>({relative:f.slice(source.length+1),sha256:sha(await readFile(f))})));
report.technical_ok=!hasFailures;
await writeFile(join(root,'runtime-report.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({browser:report.browser.version,passed:!hasFailures,live:report.live_pages.map(x=>({viewport:x.viewport.id,issues:x.issues})),states:report.state_mirrors.map(x=>({scenario:x.scenario,issues:x.issues}))},null,2));
if(hasFailures)process.exitCode=1;
