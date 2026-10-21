#!/usr/bin/env node
/** Portrait orientation gate for the already accepted R2 visuals / landscape T1 controls.
 * No change to game rules; phone portrait becomes a non-playable rotate prompt.
 */
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';
const rootArg=process.argv[2];
if(!rootArg)throw Error('Usage: node apply_t3.mjs <Echo Tide checkout already converted to R2 + T1>');
const root=resolve(rootArg);
const hash=b=>createHash('sha256').update(b).digest('hex');
const files=['src/game.js','src/render.js','src/levels.js','src/route_fork.js','src/airborne_bridge.js','src/touch_controls.js','src/visual_hud.js'];
const frozen=Object.fromEntries(await Promise.all(files.map(async p=>[p,hash(await readFile(join(root,p)))])));
const indexPath=join(root,'index.html'),mainPath=join(root,'src/main.js');
let html=await readFile(indexPath,'utf8'),js=await readFile(mainPath,'utf8');
if(!html.includes('id="et-touch-candidate-t1"')||!js.includes('attachTouchControls'))throw Error('Expected frozen R2 + T1 input surface');
if(html.includes('id="et-landscape-gate"')||js.includes('portraitTouchMode'))throw Error('T3 already applied');
function once(s,from,to,where){
 if(s.indexOf(from)<0||s.indexOf(from)!==s.lastIndexOf(from))throw Error('Missing/duplicate '+where);
 return s.replace(from,to);
}
const gate=String.raw`<aside id="et-landscape-gate" role="status" aria-label="请横屏游玩" aria-hidden="true">
    <div class="et-landscape-card">
      <div class="et-landscape-phone" aria-hidden="true"><span></span></div>
      <p class="et-landscape-kicker">叠影潮 · 手机模式</p>
      <h2>横过手机，开始跳跃</h2>
      <p>这是一款需要精确移动和跳跃的横版游戏。竖屏操作空间不足，不再显示虚拟方向键。</p>
      <p class="et-landscape-help">请旋转手机至横屏。若画面没有切换，请检查系统的屏幕旋转锁定。</p>
      <p class="et-landscape-pause">当前关卡会暂停，转为横屏后继续。</p>
    </div>
  </aside>`;
html=once(html,'</body>',`  ${gate}\n  </body>`,'body close');
const css=String.raw`
/* T3, mobile PORTRAIT ONLY: orientation gate instead of tiny virtual controls.
   Landscape's T1 controls and R2's visual design must not be changed. */
#et-landscape-gate{display:none;}
@media (max-width:580px) and (orientation:portrait) and (pointer:coarse){
  #et-touch-controls{display:none!important;}
  #et-landscape-gate{
    display:flex;position:fixed;inset:0;z-index:120;box-sizing:border-box;
    align-items:center;justify-content:center;overflow:auto;
    padding:max(18px,env(safe-area-inset-top)) max(18px,env(safe-area-inset-right))
            max(18px,env(safe-area-inset-bottom)) max(18px,env(safe-area-inset-left));
    color:#e7fff8;background:radial-gradient(ellipse at 50% 22%,#19454b 0%,#0a1822 62%,#070d12 100%);
    font-family:"Noto Sans CJK SC","Microsoft YaHei",system-ui,sans-serif;
    text-align:center;line-height:1.55;overscroll-behavior:contain;
  }
  .et-landscape-card{box-sizing:border-box;max-width:400px;width:100%;padding:28px 22px 24px;
    border:1px solid rgba(123,205,194,.5);border-radius:22px;background:rgba(10,29,38,.88);
    box-shadow:0 20px 54px rgba(0,0,0,.35);}
  .et-landscape-phone{box-sizing:border-box;width:54px;height:86px;border:3px solid #8df6df;border-radius:12px;
    transform:rotate(-90deg);margin:6px auto 18px;position:relative;background:rgba(54,115,119,.25);}
  .et-landscape-phone:after{content:"";position:absolute;width:5px;height:5px;border-radius:50%;
    background:#8df6df;left:calc(50% - 2.5px);bottom:4px;}
  .et-landscape-phone span{position:absolute;inset:7px 6px 13px;border:1px solid rgba(141,246,223,.35);
    border-radius:5px;background:linear-gradient(120deg,rgba(19,99,105,.65),rgba(5,20,29,.8));}
  #et-landscape-gate .et-landscape-kicker{color:#90e6d9;font-size:13px;letter-spacing:.09em;margin:0 0 8px;}
  #et-landscape-gate h2{font-size:clamp(20px,6vw,26px);margin:0 0 12px;line-height:1.4;color:#e4fff7;}
  #et-landscape-gate p{font-size:14px;line-height:1.65;margin:8px 0;color:#c5e3dd;}
  #et-landscape-gate .et-landscape-help{font-size:13px;color:#a8d6d0;}
  #et-landscape-gate .et-landscape-pause{font-size:12px;color:#91d0c4;margin-top:15px;}
}
`;
html=once(html,'</head>',`<style id="et-landscape-only-t3">${css}</style>\n  </head>`,'head close');
const keyInit="const touchControls = attachTouchControls({root:document.getElementById('et-touch-controls'),keys:touchKeys});";
js=once(js,keyInit,keyInit+"\nconst portraitTouchMode = window.matchMedia('(max-width:580px) and (orientation:portrait) and (pointer:coarse)');",'touch init');
const dtOld='const dt = document.hidden ? 0 : Math.min(0.083, (now - last) / 1000);';
js=once(js,dtOld,'const dt = (document.hidden || portraitTouchMode.matches) ? 0 : Math.min(0.083, (now - last) / 1000);','simulation gate');
const endOld='\nrequestAnimationFrame(frame);\n';
const endNew=`function syncOrientationMode() {
  // Cancel all held keys even if the device rotates during a two-finger gesture.
  keys.clear();
  touchControls.clear();
  accumulator = 0;
  last = performance.now();
  const portrait = portraitTouchMode.matches;
  document.querySelector('.wrap').inert = portrait;
  document.getElementById('et-landscape-gate').setAttribute('aria-hidden',String(!portrait));
}
portraitTouchMode.addEventListener('change',syncOrientationMode);
addEventListener('orientationchange',syncOrientationMode);
syncOrientationMode();
requestAnimationFrame(frame);`;
js=once(js,endOld,'\n'+endNew+'\n','rAF startup');
// Verify no gameplay rules or input mapping code was modified.
for(const p of files)if(hash(await readFile(join(root,p)))!==frozen[p])throw Error('Forbidden core file mutation '+p);
await writeFile(indexPath,html,'utf8');await writeFile(mainPath,js,'utf8');
await mkdir(join(root,'visual-eval'),{recursive:true});
const record={schema:'et-visual-02-touch-t3',candidate:'landscape-only-mobile-t3',selected_visual:'candidate-02-r2',
  previous_feedback:'Portrait control surface too small; portrait unsuitable for virtual buttons.',
  approved_landscape:'T1 layout preserved',portrait_policy:'orientation prompt and paused game, no portrait controls',
  touch_review:'not_yet_reviewed',production_approved:false,real_handset_tested:false,game_exp_lifecycle_mutated:false,
  modified_files:['index.html','src/main.js'],untouched_source_sha256:frozen,
  inherited_r2_source:'38b9daa1adf78002c8ec5349c269a4ce31959d8f',
  html_sha256:hash(html),main_js_sha256:hash(js),limitations:['No forced device rotation','Mobile browser orientation lock may be user-controlled','Chrome emulation is not physical device']};
await writeFile(join(root,'visual-eval','touch-t3-lineage.json'),JSON.stringify(record,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({ok:true,portrait_gate:true,landscape_unchanged:true,html_sha256:record.html_sha256,main_js_sha256:record.main_js_sha256}));
