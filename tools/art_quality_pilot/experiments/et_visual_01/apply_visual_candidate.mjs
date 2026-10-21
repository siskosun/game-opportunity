#!/usr/bin/env node
/** Ephemeral, non-production H5 visual candidates; never writes Echo Tide Git refs.
 * This is a SAME-AUTHOR exploratory comparison, not independent-agent A/B evidence.
 */
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve, join} from 'node:path';

const [mode, rootArg] = process.argv.slice(2);
if (!['candidate-01', 'candidate-02', 'candidate-02-r1'].includes(mode) || !rootArg) {
  throw new Error('Usage: node apply_visual_candidate.mjs candidate-01|candidate-02|candidate-02-r1 <checkout-root>');
}
const root = resolve(rootArg);
const source = join(root, 'index.html');
const renderPath = join(root, 'src', 'render.js');
const baseHTML = await readFile(source, 'utf8');
const baseRender = await readFile(renderPath, 'utf8');
const sha256 = value => createHash('sha256').update(value).digest('hex');
function replaceExactlyOnce(text, old, next, note) {
  const first = text.indexOf(old);
  if (first < 0 || text.indexOf(old, first + 1) >= 0) throw new Error(`Expected exactly one anchor (${note})`);
  return text.slice(0, first) + next + text.slice(first + old.length);
}

const shared = `
/* Exploration only: responsive artwork presentation for ET-VISUAL-01. */
:root { color-scheme: dark; }
@media (max-width: 900px) {
  *, *::before, *::after { box-sizing: border-box; }
  html, body { margin: 0; width: 100%; }
  body { display: block; padding: 6px; }
  .wrap { width: 100%; display: flex; flex-direction: column; max-width: none; }
  h1 { order: 0; margin: 0 0 4px; font-size: 13px; line-height: 18px; }
  .lede, #hint, .wrap > .foot:not(#status) { display: none !important; }
  .toolbar { order: 1; display: flex; flex-wrap: nowrap; gap: 5px; margin: 1px 0 5px; min-height: 29px; }
  .toolbar label { display: none; }
  select, button { min-width: 0; font-size: 11px; line-height: 17px; padding: 5px 5px; }
  .toolbar > * { flex: 0 1 auto; }
  #status { order: 2; display: block; margin: 0 0 5px; padding: 5px 9px; font-size: 12px; line-height: 16px; max-height: 27px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  canvas { order: 3; display: block; width: min(100%, calc((100dvh - 98px) * 1.77777778)); height: auto; margin: 0 auto; border-radius: 9px; }
  #game:focus { outline-offset: 1px; }
}
@media (max-width: 580px) and (orientation: portrait) {
  body { padding: 9px 12px; }
  h1 { font-size: 17px; line-height: 22px; }
  .toolbar { flex-wrap: wrap; gap: 5px; margin: 5px 0; }
  select, button { font-size: 12px; padding: 7px; }
  #status { max-height: none; white-space: normal; font-size: 13px; line-height: 20px; }
  canvas { width: 100%; }
}
`;

const css01 = `
/* Candidate 01: calm utility strip, simple edge and clear grouped actions. */
body { background: radial-gradient(820px 300px at 50% -10%, #0d373c, transparent 70%), #071218; }
@media (max-width: 900px) {
  .wrap { background: #07161b; }
  .toolbar { justify-content: space-between; }
  select, button { color: #e0fff1; background: #153c42; border: 1px solid #3b858a; border-radius: 7px; }
  #status { color: #dbf8f4; background: #12333b; border-left: 3px solid #5ed9ba; border-radius: 3px; }
  canvas { box-shadow: 0 0 0 2px rgba(126,219,207,.32); }
}
@media (max-width:580px) and (orientation:portrait){ .toolbar { justify-content: flex-start; } }
`;

const css02 = `
/* Candidate 02: focal play stage + status hierarchy for game-in-context legibility. */
body { background: radial-gradient(790px 390px at 50% -11%, #184b50 0%, #07151d 80%); }
@media (max-width:900px) {
  h1 { color: #f9eecb; letter-spacing: .02em; font-weight: 650; }
  h1 span { color: #a4ffdf; }
  .toolbar { justify-content: center; }
  select, button { color: #f0fffa; background: #103844; border: 1px solid rgba(164,255,223,.65); border-radius: 100px; }
  #status { background: linear-gradient(90deg, #133a40, #0d252c); border: 1px solid rgba(255,233,175,.55); border-radius: 8px; font-weight: 650; color: #fff0c8; box-shadow: 0 1px 8px #081c22; }
  canvas { border-radius: 8px; box-shadow: 0 0 0 2px #68e8cf, 0 14px 25px rgba(0,0,0,.36); }
}
`;
const revision02 = `
/* Candidate 02 revision 1: preserve the approved-as-preferred palette, frame and legibility.
   Round-1 human preference only; never implies game-exp or production approval. */
@media (min-width: 581px) and (max-width: 900px) {
  /* Landscape: separate adjacent selectors while retaining the first-screen game area. */
  .toolbar { column-gap: 14px; }
  .toolbar > select, .toolbar > button { padding-left: 9px; padding-right: 9px; }
}
@media (max-width: 580px) and (orientation: portrait) {
  /* Portrait: four controls in a stable 2 x 2 grid, rather than centered uneven pills. */
  .toolbar {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    column-gap: 12px;
    row-gap: 9px;
    justify-content: stretch;
    align-items: stretch;
    margin-top: 8px;
    margin-bottom: 8px;
  }
  .toolbar > select, .toolbar > button {
    display: block;
    width: 100%;
    min-width: 0;
    min-height: 42px;
    padding: 8px 12px;
    text-align: left;
    font-size: 12px;
    line-height: 20px;
    white-space: nowrap;
  }
  .toolbar > select { padding-right: 24px; }
}
`;
const variantCss = mode === 'candidate-01' ? css01 :
  css02 + (mode === 'candidate-02-r1' ? '\n' + revision02 : '');
let html = replaceExactlyOnce(baseHTML, '</head>', `<style id="et-visual-exploratory">${shared}\n${variantCss}</style>\n  </head>`, 'head-insert');
let render = baseRender;
if (mode === 'candidate-02' || mode === 'candidate-02-r1') {
  // These are visual-only changes; geometry and target are always from the real game state.
  const marker = "    ctx.strokeRect(rect.x, rect.y, rect.w, rect.h);";
  const improvement = `${marker}
    // Distinct corner-notch identity, directly attached to the real predicted rectangle.
    if (!stone) {
      ctx.setLineDash([]);
      ctx.strokeStyle = '#f6efbb';
      ctx.lineWidth = 3;
      const notch = Math.min(13, rect.w * 0.22);
      ctx.beginPath();
      ctx.moveTo(rect.x + 2, rect.y + notch); ctx.lineTo(rect.x + 2, rect.y + 2);
      ctx.lineTo(rect.x + notch, rect.y + 2);
      ctx.moveTo(rect.x + rect.w - notch, rect.y + rect.h - 2);
      ctx.lineTo(rect.x + rect.w - 2, rect.y + rect.h - 2);
      ctx.lineTo(rect.x + rect.w - 2, rect.y + rect.h - notch);
      ctx.stroke();
    }`;
  render = replaceExactlyOnce(render, marker, improvement, 'predicted-rectangle');
  // This is a two-line status abbreviation only on very narrow screens. It does not change game state.
  const label = "  ctx.fillText(`${Number.isInteger(game.levelIndex) ? `${game.levelIndex + 1} / 3` : '练习'}  ${game.level.title} · ${game.level.subtitle}`, 24, 18);";
  const alt = "  ctx.fillText((typeof innerWidth !== 'undefined' && innerWidth < 580) ? `${Number.isInteger(game.levelIndex) ? `${game.levelIndex + 1}/3` : '练习'} · ${game.level.title}` : `${Number.isInteger(game.levelIndex) ? `${game.levelIndex + 1} / 3` : '练习'}  ${game.level.title} · ${game.level.subtitle}`, 24, 18);";
  render = replaceExactlyOnce(render, label, alt, 'hud-title');
}
const manifest = {
  schema: 'et-visual-exploratory-0.1',
  mode,
  revision_parent: mode === 'candidate-02-r1' ? 'candidate-02' : null,
  round_1_reviewer_feedback_applied: mode === 'candidate-02-r1' ? ['landscape-control-spacing', 'portrait-even-grid-left-text-alignment'] : [],
  reviewer_verdict: 'preference_only_not_approval',
  pinned_original_ref: '38b9daa1adf78002c8ec5349c269a4ce31959d8f',
  source_index_sha256: sha256(baseHTML),
  source_render_sha256: sha256(baseRender),
  output_index_sha256: sha256(html),
  output_render_sha256: sha256(render),
  gameplay_logic_unchanged: true,
  production_approved: false,
  independent_agent_comparison: false,
  explanatory_note: 'Same-author candidate artwork iteration; do not treat reviewer preference as causal effect of art pack',
};
await writeFile(source, html, 'utf8');
await writeFile(renderPath, render, 'utf8');
await mkdir(join(root,'visual-eval'),{recursive:true});
await writeFile(join(root,'visual-eval','lineage.json'),JSON.stringify(manifest,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({mode,changed:[source,renderPath],manifest},null,2));
