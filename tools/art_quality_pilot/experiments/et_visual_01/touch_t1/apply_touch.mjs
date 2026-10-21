#!/usr/bin/env node
/** Reversible mobile-control exploration derived from immutable selected ET-VISUAL-02-R2. */
import {readFile, writeFile, copyFile, mkdir} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {resolve, join, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const [rootArg, mode] = process.argv.slice(2);
if (!rootArg) throw new Error('Usage: node apply_touch.mjs <fresh-frozen-echo-source-checkout>');
const root = resolve(rootArg);
const toolDir = dirname(fileURLToPath(import.meta.url));
const r2Generator = resolve(toolDir,'..','r2','apply_r2.mjs');
if (mode !== '--already-r2') {
  const inherited=spawnSync(process.execPath,[r2Generator,root],{stdio:'inherit'});
  if(inherited.status!==0)throw new Error('Cannot prepare selected 02-R2');
}
const pathIndex=join(root,'index.html'), pathMain=join(root,'src','main.js'), pathGame=join(root,'src','game.js');
const originalIndex=await readFile(pathIndex,'utf8'),originalMain=await readFile(pathMain,'utf8');
const hash=contents=>createHash('sha256').update(contents).digest('hex');
const originalGameHash=hash(await readFile(pathGame));
function once(s,from,to,label){if(s.indexOf(from)<0||s.indexOf(from)!==s.lastIndexOf(from)) throw Error('Expected one '+label);return s.replace(from,to);}
let index=originalIndex,main=originalMain;
const controls=`      <nav id="et-touch-controls" aria-label="手机游戏触控操作">
        <div class="et-touch-directions" aria-label="方向控制">
          <button type="button" data-code="ArrowLeft" aria-label="按住向左移动">◀ 左</button>
          <button type="button" data-code="ArrowRight" aria-label="按住向右移动">右 ▶</button>
        </div>
        <div class="et-touch-actions" aria-label="动作控制">
          <button type="button" data-code="Space" aria-label="跳跃">跳跃</button>
          <button type="button" data-code="ShiftLeft" aria-label="空中冲刺">冲刺</button>
          <button type="button" data-code="KeyE" aria-label="锚定回声">锚定</button>
        </div>
      </nav>
`;
index=once(index,'      <canvas id="game"',controls+'      <canvas id="game"','canvas markup');
const css=`
/* Touch candidate ET-VISUAL-02-T1. Trial only; portrait below canvas, landscape in side gutters. */
#et-touch-controls { display:none; }
@media (max-width:900px) {
  #et-touch-controls button { touch-action:none; -webkit-user-select:none; user-select:none; -webkit-touch-callout:none;
    min-width:0; min-height:50px; padding:7px 5px; color:#f0fffa;
    border:1px solid rgba(164,255,223,.75); border-radius:10px; background:rgba(16,56,68,.95);
    font-size:13px; font-weight:650; line-height:1.4; font-family:inherit; box-shadow:0 2px 8px rgba(0,0,0,.3); white-space:nowrap; }
  #et-touch-controls .et-touch-pressed {background:#267d80; border-color:#fff0c8; box-shadow:inset 0 0 0 2px rgba(255,240,200,.6);}
  #et-touch-controls { display:flex; align-items:center; justify-content:space-between; gap:8px; order:5; user-select:none; }
  #et-touch-controls > div {display:flex; gap:6px; min-width:0;}
  #et-touch-controls .et-touch-directions {flex:2 1 auto;}
  #et-touch-controls .et-touch-actions {flex:3 1 auto;}
  #et-touch-controls button {flex:1 1 0;}
}
@media (max-width:580px) and (orientation:portrait) {
  #et-touch-controls { margin:10px 0 4px; padding:0 0 max(0px,env(safe-area-inset-bottom)); }
  #et-touch-controls button { min-height:54px; font-size:13px; }
}
@media (min-width:581px) and (max-width:900px) and (orientation:landscape) and (max-height:550px) {
  #et-touch-controls { position:fixed; z-index:10; inset:0; margin:0; padding:0 5px env(safe-area-inset-bottom); pointer-events:none; }
  #et-touch-controls > div {position:absolute; bottom:max(8px,env(safe-area-inset-bottom)); pointer-events:none;}
  #et-touch-controls .et-touch-directions {left:5px; width:min(145px,17vw);}
  #et-touch-controls .et-touch-actions {right:5px; width:min(145px,17vw); display:grid; grid-template-columns:repeat(2,minmax(0,1fr));}
  #et-touch-controls button {pointer-events:auto; min-height:52px; font-size:12px; padding:5px 3px;}
  #et-touch-controls .et-touch-actions button:first-child {grid-column:span 2;}
}
`;
index=once(index,'</head>',`<style id="et-touch-candidate-t1">${css}</style>\n  </head>`,'touch stylesheet');
main=once(main,"import { renderVisualHud } from './visual_hud.js';","import { renderVisualHud } from './visual_hud.js';\nimport { attachTouchControls } from './touch_controls.js';",'touch import');
const count=(main.match(/keys\.has\(/g)||[]).length;if(count<8||count>25)throw Error('Unexpected game input mapping references: '+count);
main=main.replaceAll('keys.has(', 'isDown(');
main=once(main,'const keys = new Set();',`const keys = new Set();
const touchKeys = new Set();
const isDown = code => keys.has(code) || touchKeys.has(code);
const touchControls = attachTouchControls({root:document.getElementById('et-touch-controls'),keys:touchKeys});`,'key Set');
main=once(main,'  keys.clear();\n  canvas.focus();','  keys.clear();\n  touchControls.clear();\n  canvas.focus();','mode change reset');
main=once(main,"addEventListener('blur', () => keys.clear());","addEventListener('blur', () => { keys.clear(); touchControls.clear(); });",'blur release');
main=once(main,"document.addEventListener('visibilitychange', () => {\n  keys.clear();","document.addEventListener('visibilitychange', () => {\n  keys.clear();\n  touchControls.clear();",'visibility release');
main=once(main,'let buttonRestart = false;',`let buttonRestart = false;
// Local trial readout; it exposes no mutation methods and is not a game-exp review.
if (location.hostname === '127.0.0.1') Object.defineProperty(window,'__ET_TOUCH_TRIAL_READONLY__',{
  value:()=>({time:game.time,status:game.status,level:game.levelIndex,
    player:{x:game.player.x,y:game.player.y,vx:game.player.vx,vy:game.player.vy,grounded:game.player.grounded},
    dashes:game.stats.dashes,anchorId:game.anchorId,pressed:[...touchKeys].sort()}),writable:false,configurable:false
});`, 'readonly trial readout');
await writeFile(pathIndex,index,'utf8');await writeFile(pathMain,main,'utf8');
await copyFile(join(toolDir,'touch_controls.js'),join(root,'src','touch_controls.js'));
if(hash(await readFile(pathGame))!==originalGameHash)throw Error('Authoritative game core changed');
const lineage={schema:'et-visual-02-touch-t1', status:'candidate', selected_parent:'candidate-02-r2',user_visual_review:'not_yet_reviewed',
  production_approved:false, independent_ab:false, source_commit:'38b9daa1adf78002c8ec5349c269a4ce31959d8f',
  untouched_game_sha256:originalGameHash, inherited_r2_html_sha256:hash(originalIndex),inherited_r2_main_sha256:hash(originalMain),
  changed_files:['index.html','src/main.js','src/touch_controls.js'],
  not_changed:['src/game.js','src/render.js','src/levels.js','src/route_fork.js','src/airborne_bridge.js','src/visual_hud.js'],
  not_proven:['physical handset testing','human control feel','full mobile level completion','game-exp Review PASS']};
await mkdir(join(root,'visual-eval'),{recursive:true});
await writeFile(join(root,'visual-eval','touch-t1-lineage.json'),JSON.stringify(lineage,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({ok:true,lineage},null,2));
