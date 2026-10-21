/** Real Chrome touch-event QA, NOT a physical iOS/Android handset test. */
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {resolve,join} from 'node:path';
import {mkdir,readFile,readdir,writeFile} from 'node:fs/promises';
const root=resolve(process.env.TOUCH_QA_OUTPUT||'artifacts/et-touch-t1');
const source=resolve(process.env.TOUCH_QA_SOURCE||'_trial_echo');
const origin=process.env.TOUCH_QA_ORIGIN||'http://127.0.0.1:8765';
const moduleRoot=process.env.TOUCH_QA_PLAYWRIGHT;
if(!moduleRoot)throw Error('TOUCH_QA_PLAYWRIGHT required');
const require=createRequire(join(resolve(moduleRoot),'package.json'));
const {chromium}=require('playwright');
const hash=x=>createHash('sha256').update(x).digest('hex');
await mkdir(root,{recursive:true});
const fileRecord=async(relative)=>{
 const b=await readFile(join(root,relative));return {path:relative,bytes:b.length,sha256:hash(b)};
};
const report={schema:'et-visual-02-touch-t1-v1',selected_visual_baseline:'ET-VISUAL-02/candidate-02-r2',
 candidate:'candidate-touch-t1',production_approved:false,game_exp_lifecycle_mutated:false,
 real_physical_device:false,browser:'',viewports:[],touch_trials:[],passed:false,dist_sha256:[]};
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
report.browser=browser.version();
let failed=false;
const targets=[
 {id:'portrait-360',width:360,height:800,isMobile:true},
 {id:'portrait-390',width:390,height:844,isMobile:true},
 {id:'landscape-844',width:844,height:390,isMobile:true},
 {id:'desktop-1280',width:1280,height:900,isMobile:false},
];
function watcher(page){const errors=[];
 page.on('pageerror',e=>errors.push('pageerror:'+String(e)));
 page.on('console',m=>{if(m.type()==='error')errors.push('console:'+m.text())});
 page.on('requestfailed',r=>errors.push('network:'+r.url()));
 page.on('response',r=>{if(r.status()>=400)errors.push(`HTTP${r.status()}:${r.url()}`)});
 return errors;
}
async function snapshot(page){return page.evaluate(()=>{
 const ids=['ArrowLeft','ArrowRight','Space','ShiftLeft','KeyE'];
 const buttons=ids.map(code=>{const e=document.querySelector(`[data-code="${code}"]`);const b=e.getBoundingClientRect();
  return {code,x:b.x,y:b.y,w:b.width,h:b.height,display:getComputedStyle(e).display};});
 const nav=document.getElementById('et-touch-controls'),game=document.getElementById('game'),canvas=game.getBoundingClientRect();
 const n=nav.getBoundingClientRect(),hud=document.getElementById('et-readable-hud').getBoundingClientRect();
 return {size:[innerWidth,innerHeight],horizontalOverflow:document.documentElement.scrollWidth>innerWidth+1,
 navVisible:getComputedStyle(nav).display!=='none',nav:{x:n.x,y:n.y,w:n.width,h:n.height},
 canvas:{x:canvas.x,y:canvas.y,w:canvas.width,h:canvas.height,bottom:canvas.bottom},
 hud:{bottom:hud.bottom},buttons,scrollY,readonly:window.__ET_TOUCH_TRIAL_READONLY__?.()||null};
 });}
async function save(page,id){const target=join(root,id);await page.screenshot({path:target,animations:'disabled',fullPage:false});return fileRecord(id);}
function btnCenter(v,code){const b=v.buttons.find(z=>z.code===code);return {x:Math.floor(b.x+b.w/2),y:Math.floor(b.y+b.h/2)};}
async function realTouch(session,type,points){await session.send('Input.dispatchTouchEvent',{type,touchPoints:points.map(p=>({x:p.x,y:p.y,id:p.id,force:1}))});}
async function exerciseTouches(page,viewport){
 const issues=[];const session=await page.context().newCDPSession(page);
 const start=await snapshot(page);const right=btnCenter(start,'ArrowRight'), jump=btnCenter(start,'Space');
 const left=btnCenter(start,'ArrowLeft'),dash=btnCenter(start,'ShiftLeft'), anchor=btnCenter(start,'KeyE');
 const touch=(type,p)=>realTouch(session,type,p);
 // Playwright/Chromium sends actual device touch events through the compositor.
 await touch('touchStart',[{...right,id:1}]);
 await page.waitForTimeout(165);
 const rightHeld=await snapshot(page);
 if(!rightHeld.readonly?.pressed.includes('ArrowRight'))issues.push('right finger not held');
 if(rightHeld.readonly?.player.x<=start.readonly.player.x+5)issues.push('right touch did not move player');
 await touch('touchStart',[{...right,id:1},{...jump,id:2}]);
 await page.waitForTimeout(75);
 const joint=await snapshot(page);
 if(joint.readonly?.player.y>=rightHeld.readonly.player.y-4)issues.push('jump touch did not lift player');
 if(!joint.readonly?.pressed.includes('Space')||!joint.readonly?.pressed.includes('ArrowRight'))issues.push('multitouch not independently held');
 await touch('touchEnd',[{...jump,id:2}]);
 await page.waitForTimeout(170);
 const afterShortJump=await snapshot(page);
 if(afterShortJump.readonly?.pressed.includes('Space'))issues.push('jump remains stuck after short tap');
 if(!afterShortJump.readonly?.pressed.includes('ArrowRight'))issues.push('right finger dropped when jump released');
 await touch('touchStart',[{...right,id:1},{...dash,id:3}]);
 await page.waitForTimeout(120);
 const afterDash=await snapshot(page);
 await touch('touchEnd',[{...right,id:1}]);
 await touch('touchEnd',[]);
 await page.waitForTimeout(140);
 const afterAll=await snapshot(page);
 if(afterAll.readonly?.pressed.length)issues.push('held keys after releasing fingers');
 if(afterDash.readonly?.dashes<1)issues.push('air dash did not register');
 // Pointer cancel and blur clear controls; short actions cannot remain latched.
 await touch('touchStart',[{...left,id:4}]);
 await page.waitForTimeout(40);
 await touch('touchCancel',[]);
 await page.waitForTimeout(40);
 if((await snapshot(page)).readonly.pressed.length)issues.push('touchCancel did not release');
 await touch('touchStart',[{...anchor,id:5}]);
 await page.evaluate(()=>window.dispatchEvent(new Event('blur')));
 await page.waitForTimeout(35);
 if((await snapshot(page)).readonly.pressed.length)issues.push('blur did not release');
 // Reset selection is an existing control and must release touch state.
 await page.locator('#room').selectOption('1');await page.waitForTimeout(80);
 if((await snapshot(page)).readonly.level!==1)issues.push('room select did not restart in new room');
 const screenshot=await save(page,`${viewport.id}-touch-after-actions.png`);
 return {issues,metrics:{start:start.readonly,rightHeld:rightHeld.readonly,joint:joint.readonly,afterShortJump:afterShortJump.readonly,afterDash:afterDash.readonly,afterAll:afterAll.readonly},screenshot};
}
try{
 for(const v of targets){
  const ctx=await browser.newContext({viewport:{width:v.width,height:v.height},deviceScaleFactor:1,
    hasTouch:v.isMobile,isMobile:v.isMobile});
  await ctx.addInitScript(()=>{const previous=Crypto.prototype.getRandomValues;Crypto.prototype.getRandomValues=function(a){
    if(a instanceof Uint32Array&&a.length===1){a[0]=3;return a;}return previous.call(this,a);};});
  const page=await ctx.newPage(),errors=watcher(page);const result=await page.goto(origin+'/',{waitUntil:'networkidle',timeout:30000});
  await page.waitForFunction(()=>window.__ET_TOUCH_TRIAL_READONLY__?.().time>0,{timeout:15000});
  const initial=await snapshot(page);
  const screenshot=await save(page,`${v.id}-initial.png`);
  const issues=[];
  if(result?.status()!==200)issues.push('wrong HTTP response');
  if(initial.horizontalOverflow)issues.push('horizontal overflow');
  if(initial.canvas.bottom>v.height+1)issues.push('canvas not fully visible in viewport');
  const isTouch=v.width<=900;
  if(isTouch&&!initial.navVisible)issues.push('mobile touch buttons hidden');
  if(!isTouch&&initial.navVisible)issues.push('touch bar visible on desktop');
  if(isTouch){
   for(const b of initial.buttons){if(b.w<44||b.h<44)issues.push(`${b.code} touch target under 44px`);
    if(b.x<0||b.y<0||b.x+b.w>v.width+1||b.y+b.h>v.height+1)issues.push(`${b.code} touch target offscreen`);}
   for(let i=0;i<initial.buttons.length;i++)for(let j=i+1;j<initial.buttons.length;j++){
    const a=initial.buttons[i],b=initial.buttons[j];
    const ix=Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x);
    const iy=Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y);
    if(ix>1&&iy>1)issues.push(`touch targets overlap ${a.code}/${b.code}`);
   }
   const portrait=v.height>v.width;
   if(portrait&&initial.buttons.some(b=>b.y<initial.canvas.bottom-1))issues.push('portrait buttons cover game');
   if(!portrait){
    const canvas=initial.canvas;
    const directions=initial.buttons.filter(b=>['ArrowLeft','ArrowRight'].includes(b.code));
    const actions=initial.buttons.filter(b=>!['ArrowLeft','ArrowRight'].includes(b.code));
    if(directions.some(b=>b.x+b.w>canvas.x+1))issues.push('landscape direction overlay obscures canvas');
    if(actions.some(b=>b.x<canvas.x+canvas.w-1))issues.push('landscape action overlay obscures canvas');
   }
  }
  let input=null;
  if(isTouch){
   // Only drive interactive touch if basic hit targets are present.
   if(!issues.length){input=await exerciseTouches(page,v);issues.push(...input.issues);}
   else issues.push('input checks skipped because layout is invalid');
  }
  issues.push(...errors);
  if(issues.length)failed=true;
  report.viewports.push({id:v.id,size:[v.width,v.height],emulatedTouch:v.isMobile,initial,screenshot,
    input:input?{screenshot:input.screenshot,metrics:input.metrics}:null,issues,passed:issues.length===0});
  await ctx.close();
 }
}finally{await browser.close();}
const assets=(await readdir(join(source,'dist','assets'))).filter(x=>x.endsWith('.js')).sort();
report.dist_sha256=await Promise.all([join(source,'dist','index.html'),...assets.map(z=>join(source,'dist','assets',z))].map(async p=>({path:p.slice(source.length+1),sha256:hash(await readFile(p))})));
report.passed=!failed;
await writeFile(join(root,'touch-qa-report.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({browser:report.browser,passed:!failed,viewports:report.viewports.map(v=>({id:v.id,issues:v.issues})),build:report.dist_sha256},null,2));
if(failed)process.exitCode=1;