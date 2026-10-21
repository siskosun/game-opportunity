#!/usr/bin/env node
/** Portrait-only ergonomic redesign of T1. Do not change accepted landscape controls or core. */
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {resolve,join,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const [rootArg,mode]=process.argv.slice(2);
if(!rootArg)throw Error('Usage: node apply_t2.mjs <Echo Tide checkout> [--already-t1]');
const root=resolve(rootArg),dir=dirname(fileURLToPath(import.meta.url));
if(mode!=='--already-t1'){
  const t1=resolve(dir,'..','touch_t1','apply_touch.mjs');
  const result=spawnSync(process.execPath,[t1,root,'--already-r2'],{stdio:'inherit'});
  if(result.status!==0)throw Error('Cannot inherit T1');
}
const indexPath=join(root,'index.html');
let index=await readFile(indexPath,'utf8');
if(!index.includes('id="et-touch-candidate-t1"'))throw Error('Missing frozen T1 template');
if(index.includes('id="et-touch-candidate-t2"'))throw Error('T2 already injected');
const getSha=buffer=>createHash('sha256').update(buffer).digest('hex');
const sourcePaths=['src/game.js','src/render.js','src/levels.js','src/route_fork.js','src/airborne_bridge.js','src/main.js','src/touch_controls.js','src/visual_hud.js'];
const before=Object.fromEntries(await Promise.all(sourcePaths.map(async p=>[p,getSha(await readFile(join(root,p)))])));
const css=String.raw`
/* T2 PORTRAIT ONLY: thumb zones anchored at the safe bottom edge.
   Landscape and desktop deliberately retain T1 unchanged. */
@media (max-width:580px) and (orientation:portrait) {
  #et-touch-controls {
    position:fixed; z-index:20; order:5;
    inset:auto max(12px,env(safe-area-inset-right)) max(12px,env(safe-area-inset-bottom)) max(12px,env(safe-area-inset-left));
    width:auto; height:auto; margin:0; padding:0;
    display:flex; flex-flow:row nowrap; align-items:flex-end;
    justify-content:space-between; gap:clamp(25px,8vw,75px);
    pointer-events:none; background:none;
  }
  #et-touch-controls > div { min-width:0; flex:0 0 auto; pointer-events:none; }
  #et-touch-controls .et-touch-directions {
    display:grid; grid-template-columns:repeat(2,clamp(54px,17vw,66px));
    grid-template-rows:76px; gap:10px; align-items:end;
  }
  #et-touch-controls .et-touch-actions {
    display:grid;
    grid-template-columns:clamp(52px,16vw,62px) clamp(68px,21vw,76px);
    grid-template-rows:44px 76px;
    grid-template-areas:'. anchor' 'dash jump';
    gap:8px; align-items:end;
  }
  #et-touch-controls button {
    pointer-events:auto; box-sizing:border-box;
    margin:0; padding:5px 3px; min-width:0; min-height:0;
    height:76px; font-size:15px; border-radius:16px;
    background:rgba(15,52,66,.97);
    box-shadow:0 4px 14px rgba(0,0,0,.38),inset 0 0 0 1px rgba(170,245,224,.12);
    -webkit-tap-highlight-color:transparent;
  }
  #et-touch-controls .et-touch-directions button {width:100%;font-size:15px;}
  #et-touch-controls .et-touch-actions button[data-code="Space"] {
    grid-area:jump; width:100%; height:76px;
    font-size:17px; font-weight:750;
    background:rgba(22,100,105,.98); border-color:#a4ffdf;
  }
  #et-touch-controls .et-touch-actions button[data-code="ShiftLeft"] {
    grid-area:dash; width:100%; height:66px;
    font-size:13px; align-self:end;
  }
  #et-touch-controls .et-touch-actions button[data-code="KeyE"] {
    grid-area:anchor; width:100%; height:44px;
    font-size:12px; border-style:dashed;
    color:#b8d7d1; background:rgba(17,47,55,.95);
  }
  #et-touch-controls .et-touch-pressed {
    background:rgba(46,127,128,.98)!important;
    border-color:#fff0c8!important;
    box-shadow:inset 0 0 0 2px rgba(255,240,200,.72)!important;
  }
}
`;
const tag=`<style id="et-touch-candidate-t2">${css}</style>`;
if(index.indexOf('</head>')<0)throw Error('Missing head end');
index=index.replace('</head>',`${tag}\n  </head>`);
await writeFile(indexPath,index,'utf8');
for(const p of sourcePaths){if(getSha(await readFile(join(root,p)))!==before[p])throw Error('T2 modified forbidden source: '+p);}
const record={schema:'et-visual-02-touch-t2',candidate:'portrait-thumbzones-t2',inherits:'candidate-touch-t1',selected_visual:'candidate-02-r2',user_touch_review:'awaiting',production_approved:false,
  modified_files:['index.html'],unchanged_source_sha256:before,
  assumptions:['Thumb placement is preliminary without human handset trial','CSS 360x800/390x844 and 844x390 do not prove ergonomics'],
  rejected_t1_feedback:'Landscape acceptable; portrait interaction counterintuitive',layout_principle:'left thumb moves, right thumb jumps/dashes; infrequent anchor above right zone'};
await mkdir(join(root,'visual-eval'),{recursive:true});
await writeFile(join(root,'visual-eval','touch-t2-lineage.json'),JSON.stringify(record,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({ok:true,t2:true,source_unchanged:true,css_scoped_to_portrait:true,html_sha256:getSha(index)}));
