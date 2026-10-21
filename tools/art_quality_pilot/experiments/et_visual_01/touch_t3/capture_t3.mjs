/** Verify portrait gate, game-clock pause, true landscape touch, rotate safety and pinned T1 geometry.
 * These are Chrome emulation tests, NOT physical iOS/Android QA. */
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {resolve,join} from 'node:path';
import {mkdir,readFile,readdir,writeFile} from 'node:fs/promises';
const output=resolve(process.env.T3_QA_OUTPUT||'artifacts/et-touch-t3');
const source=resolve(process.env.T3_QA_SOURCE||'_trial_echo');
const origin=process.env.T3_QA_ORIGIN||'http://127.0.0.1:8765';
const pwRoot=process.env.T3_QA_PLAYWRIGHT;
if(!pwRoot)throw Error('T3_QA_PLAYWRIGHT required');
const require=createRequire(join(resolve(pwRoot),'package.json'));
const {chromium}=require('playwright');
const hash=x=>createHash('sha256').update(x).digest('hex');
await mkdir(output,{recursive:true});
const report={schema:'et-visual-touch-t3-20261021',candidate:'landscape-mobile-t3',selected_visual:'candidate-02-r2',
  source_sha:'38b9daa1adf78002c8ec5349c269a4ce31959d8f',production_approved:false,
  actual_phone_tested:false,game_exp_review_recorded:false,
  browser:'',portrait:[],landscape:[],desktop:null,rotation:null,passed:false,files:[],build:[]};
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
report.browser=browser.version();
const issues=[];
async function snapshot(page){return page.evaluate(()=>{
 const gate=document.getElementById('et-landscape-gate');
 const nav=document.getElementById('et-touch-controls');
 const canvas=document.getElementById('game');
 const rect=(el)=>{let r=el.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,bottom:r.bottom}};
 return {size:[innerWidth,innerHeight],portraitMatch:matchMedia('(max-width:580px) and (orientation:portrait) and (pointer:coarse)').matches,
  gateVisible:getComputedStyle(gate).display!=='none',gateAriaHidden:gate.getAttribute('aria-hidden'),gate:rect(gate),
  navVisible:getComputedStyle(nav).display!=='none',wrapInert:document.querySelector('.wrap').inert,
  canvas:rect(canvas),horizontalOverflow:document.documentElement.scrollWidth>innerWidth+1,
  buttons:['ArrowLeft','ArrowRight','Space','ShiftLeft','KeyE'].map(code=>{
    const x=document.querySelector(`[data-code="${code}"]`);return {code,...rect(x),display:getComputedStyle(x).display};}),
  game:window.__ET_TOUCH_TRIAL_READONLY__?.()||null};
});}
async function screenshot(page,id){let relative=`${id}.png`;await page.screenshot({path:join(output,relative),animations:'disabled',fullPage:false});let b=await readFile(join(output,relative));report.files.push({path:relative,bytes:b.length,sha256:hash(b)});}
function watch(page){const e=[];page.on('pageerror',x=>e.push('pageerror '+x));page.on('console',x=>{if(x.type()==='error')e.push('console '+x.text());});page.on('requestfailed',x=>e.push('network '+x.url()));page.on('response',x=>{if(x.status()>=400)e.push('http '+x.status()+' '+x.url());});return e;}
async function loadPage(v){
 const ctx=await browser.newContext({viewport:{width:v.width,height:v.height},isMobile:v.mobile,hasTouch:v.mobile,deviceScaleFactor:1});
 await ctx.addInitScript(()=>{let prev=Crypto.prototype.getRandomValues;Crypto.prototype.getRandomValues=function(a){if(a instanceof Uint32Array&&a.length===1){a[0]=3;return a;}return prev.call(this,a);};});
 const page=await ctx.newPage(),errors=watch(page);const res=await page.goto(origin+'/',{waitUntil:'networkidle',timeout:30000});
 if(res.status()!==200)errors.push('non-200 response');
 await page.waitForFunction(()=>typeof window.__ET_TOUCH_TRIAL_READONLY__==='function',{timeout:12000});
 return {ctx,page,errors};
}
// Geometry from the already user-accepted T1 horizontal controls, CI #39573056148.
const reference={'ArrowLeft':{x:5,y:330,w:68.734375,h:52},'ArrowRight':{x:79.734375,y:330,w:68.734375,h:52},
 'Space':{x:695.53125,y:272,w:143.46875,h:52},'ShiftLeft':{x:695.53125,y:330,w:68.734375,h:52},
 'KeyE':{x:770.265625,y:330,w:68.734375,h:52}};
function verifyLandscape(s,label,issueList){
 if(s.portraitMatch||s.gateVisible||s.gateAriaHidden!=='true'||s.wrapInert)issueList.push(label+':landscape gate erroneously active');
 if(!s.navVisible)issueList.push(label+':accepted horizontal controls hidden');
 if(s.horizontalOverflow)issueList.push(label+':horizontal overflow');
 if(s.canvas.bottom>s.size[1]+1)issueList.push(label+':game canvas clipped');
 if(s.size[0]===844){
 for(const x of s.buttons){const e=reference[x.code];for(const f of ['x','y','w','h'])if(Math.abs(x[f]-e[f])>1.1)issueList.push(`${label}:T1 horizontal geometry changed ${x.code}.${f}: ${x[f]} vs ${e[f]}`);}
 }
 const dirs=s.buttons.filter(x=>x.code==='ArrowLeft'||x.code==='ArrowRight');
 const acts=s.buttons.filter(x=>!['ArrowLeft','ArrowRight'].includes(x.code));
 if(dirs.some(x=>x.x+x.w>s.canvas.x+1)||acts.some(x=>x.x<s.canvas.x+s.canvas.w-1))issueList.push(label+':accepted horizontal controls cover game');
}
async function dispatch(session,type,pts){await session.send('Input.dispatchTouchEvent',{type,touchPoints:pts.map(p=>({...p,force:1}))});}
function center(s,code,id){let b=s.buttons.find(x=>x.code===code);return {x:Math.round(b.x+b.w/2),y:Math.round(b.y+b.h/2),id};}
try{
 for(const v of [{id:'portrait-360-short',width:360,height:640,mobile:true},{id:'portrait-360',width:360,height:800,mobile:true},{id:'portrait-390',width:390,height:844,mobile:true},{id:'portrait-430',width:430,height:932,mobile:true}]){
  const {ctx,page,errors}=await loadPage(v),problems=[];
  await page.waitForTimeout(210);
  const s=await snapshot(page);await screenshot(page,v.id+'-rotate-prompt');
  if(!s.portraitMatch||!s.gateVisible||s.gateAriaHidden!=='false')problems.push('portrait rotate prompt missing');
  if(s.navVisible)problems.push('rejected portrait buttons still visible');
  if(!s.wrapInert)problems.push('portrait game surface not inert');
  if(s.horizontalOverflow)problems.push('portrait horizontal overflow');
  if(!s.game||s.game.time>.035)problems.push('game clock advanced behind gate');
  // Even direct keyboard input must not move or advance the game while portrait is gated.
  const t=s.game?.time,x=s.game?.player.x;
  await page.keyboard.down('ArrowRight');await page.waitForTimeout(200);await page.keyboard.up('ArrowRight');
  const after=await snapshot(page);
  if(Math.abs(after.game.time-t)>.02||Math.abs(after.game.player.x-x)>.1)problems.push('portrait input advanced hidden game');
  problems.push(...errors);
  if(problems.length)issues.push(`${v.id}: ${problems.join('; ')}`);
  report.portrait.push({id:v.id,initial:s,after_input:after,issues:problems,passed:problems.length===0});
  await ctx.close();
 }
 // Rotate the SAME mobile tab with a finger held: pressed state must be cleared and game paused.
 {
  const {ctx,page,errors}=await loadPage({id:'rotation',width:390,height:844,mobile:true}),problems=[];
  let s=await snapshot(page);if(!s.gateVisible)problems.push('portrait entry gate missing');
  await page.setViewportSize({width:844,height:390});await page.waitForTimeout(170);
  s=await snapshot(page);verifyLandscape(s,'rotated landscape',problems);
  await screenshot(page,'rotated-to-landscape');
  if(s.game.time<.06)problems.push('game never resumed in landscape');
  const session=await ctx.newCDPSession(page);
  const right=center(s,'ArrowRight',1),jump=center(s,'Space',2),dash=center(s,'ShiftLeft',3);
  const x0=s.game.player.x;
  await dispatch(session,'touchStart',[right]);await page.waitForTimeout(190);
  const held=await snapshot(page);if(!held.game.pressed.includes('ArrowRight')||held.game.player.x<=x0+5)problems.push('landscape moving touch failed');
  await dispatch(session,'touchStart',[right,jump]);await page.waitForTimeout(90);
  const joint=await snapshot(page);if(!joint.game.pressed.includes('Space')||joint.game.player.y>=held.game.player.y-4)problems.push('landscape jump with movement failed');
  await dispatch(session,'touchEnd',[jump]);await page.waitForTimeout(170);
  const released=await snapshot(page);
  if(released.game.pressed.includes('Space')||!released.game.pressed.includes('ArrowRight'))problems.push('released jump disturbed direction key');
  await dispatch(session,'touchStart',[right,dash]);await page.waitForTimeout(120);
  const dashed=await snapshot(page);if(dashed.game.dashes<1)problems.push('landscape air dash failed');
  // Keep both fingers down while rotating to verify release/clock gate.
  await page.setViewportSize({width:390,height:844});await page.waitForTimeout(160);
  const gated=await snapshot(page);await screenshot(page,'rotated-back-to-portrait');
  if(!gated.gateVisible||gated.navVisible)problems.push('portrait gate failed on rotation back');
  if(gated.game.pressed.length)problems.push('held touch keys leaked after rotation');
  const t0=gated.game.time,xp=gated.game.player.x;
  await page.waitForTimeout(180);
  const paused=await snapshot(page);
  if(Math.abs(paused.game.time-t0)>.035||Math.abs(paused.game.player.x-xp)>.3)problems.push('game advanced during portrait pause');
  // Cancel remaining pointers if CDP retains them and check recovery.
  try{await dispatch(session,'touchCancel',[]);}catch{}
  await page.setViewportSize({width:844,height:390});await page.waitForTimeout(130);
  const resumed=await snapshot(page);
  if(resumed.gateVisible||!resumed.navVisible||resumed.game.pressed.length)problems.push('touch or gate persisted after second rotation');
  problems.push(...errors);
  if(problems.length)issues.push(`rotation: ${problems.join('; ')}`);
  report.rotation={initial:s,held,joint,released,dashed,gated,paused,resumed,issues:problems,passed:problems.length===0};
  await ctx.close();
 }
 // Fresh landscape directly booted, and desktop keyboard view are still valid.
 {
  const {ctx,page,errors}=await loadPage({width:844,height:390,mobile:true});
  await page.waitForTimeout(100);const s=await snapshot(page),problems=[];verifyLandscape(s,'direct landscape',problems);
  await screenshot(page,'landscape-844-frozen-controls');problems.push(...errors);
  report.landscape.push({id:'landscape-844',snapshot:s,issues:problems,passed:problems.length===0});if(problems.length)issues.push(problems.join('; '));await ctx.close();
 }
 {
  const {ctx,page,errors}=await loadPage({width:1280,height:900,mobile:false});await page.waitForTimeout(120);
  const s=await snapshot(page),p=[];
  if(s.gateVisible||s.navVisible||s.wrapInert)p.push('desktop lost keyboard view');
  if(s.horizontalOverflow||s.canvas.bottom>900)p.push('desktop overflow');
  p.push(...errors);if(p.length)issues.push(`desktop: ${p.join('; ')}`);
  report.desktop={snapshot:s,issues:p,passed:p.length===0};await screenshot(page,'desktop-keyboard-unchanged');await ctx.close();
 }
}finally{await browser.close();}
const jsAssets=(await readdir(join(source,'dist','assets'))).filter(x=>x.endsWith('.js')).sort();
report.build=await Promise.all(['index.html',...jsAssets.map(x=>'assets/'+x)].map(async p=>({path:'dist/'+p,sha256:hash(await readFile(join(source,'dist',p)))})));
report.passed=issues.length===0;
report.issues=issues;
await writeFile(join(output,'touch-t3-qa.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:report.passed,issues,files:report.files.length,build:report.build,browser:report.browser},null,2));
if(!report.passed)process.exitCode=1;
