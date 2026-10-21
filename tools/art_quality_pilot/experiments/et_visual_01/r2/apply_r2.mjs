#!/usr/bin/env node
/** Test-only next candidate based on the exact selected 02-R1 recipe.
 * Visual DOM readout, no game.js/levels.js/physics changes, no gameplay approval.
 */
import { readFile, writeFile, copyFile, mkdir } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
const [rootArg] = process.argv.slice(2);
if (!rootArg) throw new Error('Usage: node apply_r2.mjs <echo-source-checkout>');
const root = resolve(rootArg);
const toolDir = dirname(fileURLToPath(import.meta.url));
const inherited = resolve(toolDir, '..', 'apply_visual_candidate.mjs');
const cmd = spawnSync(process.execPath, [inherited, 'candidate-02-r1', root], { stdio: 'inherit' });
if (cmd.status !== 0) throw new Error('Frozen selected 02-R1 setup failed');
const indexPath = join(root, 'index.html');
const mainPath = join(root, 'src', 'main.js');
const gamePath = join(root, 'src', 'game.js');
const read = async p => readFile(p, 'utf8');
const sha = value => createHash('sha256').update(value).digest('hex');
function one(input, find, replace, note) {
  const first = input.indexOf(find);
  if (first < 0 || input.indexOf(find, first + find.length) >= 0) throw new Error('Expected exactly one '+ note);
  return input.slice(0, first) + replace + input.slice(first + find.length);
}
const beforeIndex = await read(indexPath);
const beforeMain = await read(mainPath);
const beforeGame = sha(await readFile(gamePath));
const htmlMarkup = `      <section id="et-readable-hud" aria-label="游戏状态与落点提示" role="group">
        <div class="et-hud-row"><span id="et-hud-level">关卡 1/3</span><strong id="et-hud-time">潮汐 --s</strong></div>
        <div class="et-hud-row et-hud-detail"><span id="et-hud-goal">潮印待揭晓</span><span id="et-hud-cue">首跳教学</span></div>
      </section>
`;
const css = `
/* Candidate 02-R2 (unapproved): mirror the *real* game state at CSS reading size. */
#et-readable-hud { display:none; }
@media (max-width:580px) and (orientation:portrait) {
  .toolbar > select, .toolbar > button { min-height:46px; }
  #status { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip-path:inset(50%); white-space:nowrap; }
  #et-readable-hud {
    display:grid; gap:4px; order:3; margin:2px 0 9px; padding:8px 10px;
    border:1px solid rgba(255,233,175,.60); border-radius:8px;
    background:linear-gradient(90deg,#133a40,#0d252c);
    color:#fff0c8; box-shadow:0 1px 8px #081c22;
    text-align:left; font-size:13px; line-height:19px;
  }
  #et-readable-hud .et-hud-row { display:flex; justify-content:space-between; align-items:flex-start; gap:10px; min-width:0; }
  #et-readable-hud .et-hud-row > * { min-width:0; overflow-wrap:anywhere; }
  #et-hud-time { flex:0 0 auto; color:#d9fff6; font-size:14px; }
  #et-hud-goal { flex:0 0 auto; color:#a4ffdf; font-weight:650; }
  #et-readable-hud .et-hud-detail { display:block; }
  #et-hud-cue { display:block; text-align:left; margin-top:2px; font-size:13px; color:#fff0c8; }
  #et-readable-hud[data-state="blocked"], #et-readable-hud[data-state="lost"] { border-color:#ffb089; }
  #et-readable-hud[data-state="blocked"] #et-hud-cue { color:#ffb089; }
  canvas { order:4; }
}
`;
let html = one(beforeIndex, '      <canvas id="game"', htmlMarkup+'      <canvas id="game"', 'game canvas anchor');
html = one(html, '</head>', `<style id="et-visual-hud-r2">${css}</style>\n  </head>`, 'style head');
let main = one(beforeMain,
  "import { draw } from './render.js';",
  "import { draw } from './render.js';\nimport { renderVisualHud } from './visual_hud.js';", 'renderer import');
main = one(main,
  '  syncUi();\n  requestAnimationFrame(frame);',
  '  syncUi();\n  renderVisualHud(game);\n  requestAnimationFrame(frame);', 'live UI sync');
await copyFile(join(toolDir, 'visual_hud.js'), join(root, 'src','visual_hud.js'));
await writeFile(indexPath, html, 'utf8');
await writeFile(mainPath, main, 'utf8');
const afterGame = sha(await readFile(gamePath));
if (beforeGame !== afterGame) throw new Error('Authoritative game.js content changed');
const provenance = {
  schema: 'et-visual-02-r2-exploratory-v1', status:'candidate', production_approved:false,
  parent_selected:'et-visual-01/candidate-02-r1', parent_visual_source_commit:'f2372233ceae93898bdd3b65c0240b5eae91a175',
  pinned_echo_source_sha:'38b9daa1adf78002c8ec5349c269a4ce31959d8f',
  original_game_sha256:beforeGame, new_game_sha256:afterGame,
  inherited_r1_html_sha256:sha(beforeIndex), inherited_main_js_sha256:sha(beforeMain),
  changed_files:['index.html','src/main.js','src/visual_hud.js'],
  not_changed:['src/game.js','src/render.js','src/levels.js','src/route_fork.js','src/airborne_bridge.js'],
  change_claim:'Presentation-only responsive mirror from authoritative game state. No manual game state injections in production.',
  not_proven:['human-readable under actual device conditions','human visual preference','game-exp Review PASS','touch gestures']
};
await mkdir(join(root,'visual-eval'),{recursive:true});
await writeFile(join(root,'visual-eval','r2-lineage.json'), JSON.stringify(provenance,null,2)+'\n', {flag:'wx'});
console.log(JSON.stringify({ok:true,provenance},null,2));
