/** Read-only browser evidence for the frozen public Echo Tide build.
 * Does not modify game sources, declare art approval, or fabricate asset attempts.
 * Run inside a short-lived GitHub Actions job with a pinned Chrome binary.
 */
import { createHash } from 'node:crypto';
import { mkdir, readdir, readFile, writeFile } from 'node:fs/promises';
import { resolve, join, relative } from 'node:path';
import { createRequire } from 'node:module';

const frozenRef = '38b9daa1adf78002c8ec5349c269a4ce31959d8f';
const origin = process.env.ECHO_VISUAL_ORIGIN || 'http://127.0.0.1:8765';
const variantId = process.env.ET_VISUAL_VARIANT_ID;
if (!['candidate-01', 'candidate-02', 'candidate-02-r1'].includes(variantId)) throw new Error('ET_VISUAL_VARIANT_ID is required');
const sourceRoot = resolve(process.env.ECHO_VISUAL_SOURCE || '_frozen_echo');
const outputRoot = resolve(process.env.ECHO_VISUAL_OUTPUT || 'artifacts/echo-visual');
const moduleRoot = process.env.ECHO_PLAYWRIGHT_ROOT;
if (!moduleRoot) throw new Error('ECHO_PLAYWRIGHT_ROOT is required');
const require = createRequire(join(resolve(moduleRoot), 'package.json'));
const { chromium } = require('playwright');
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');

async function fileEntry(path, base = sourceRoot) {
  const bytes = await readFile(path);
  return { path: relative(base, path).replaceAll('\\', '/'), sha256: sha256(bytes), bytes: bytes.length };
}
async function hashedBuild() {
  const files = [join(sourceRoot, 'dist/index.html')];
  for (const name of (await readdir(join(sourceRoot, 'dist/assets'))).sort()) files.push(join(sourceRoot, 'dist/assets', name));
  return await Promise.all(files.map(f => fileEntry(f)));
}

const viewports = [
  { id: 'mobile-portrait', width: 390, height: 844 },
  { id: 'mobile-portrait-min', width: 360, height: 800 },
  { id: 'mobile-landscape', width: 844, height: 390 },
  { id: 'desktop', width: 1280, height: 900 },
];

async function metadata(page) {
  return await page.evaluate(() => {
    const canvas = document.getElementById('game');
    const rect = canvas?.getBoundingClientRect();
    const root = document.documentElement;
    const nodes = ['room', 'difficulty', 'style', 'restart', 'next'].map(id => {
      const el = document.getElementById(id);
      const r = el?.getBoundingClientRect();
      return { id, visible: !!(el && el.getClientRects().length), bounding_css_px: r ? { x: r.x, y: r.y, width: r.width, height: r.height } : null,
        text_align: el ? getComputedStyle(el).textAlign : null, font_size: el ? getComputedStyle(el).fontSize : null };
    });
    return {
      title: document.title,
      viewport_css_px: { width: innerWidth, height: innerHeight },
      document_css_px: { scrollWidth: root.scrollWidth, scrollHeight: root.scrollHeight },
      horizontal_overflow: root.scrollWidth > innerWidth + 1,
      dpr: devicePixelRatio,
      canvas: canvas ? { bitmap_width: canvas.width, bitmap_height: canvas.height, css_rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height } } : null,
      controls: nodes,
      canvas_visible_fraction_in_initial_viewport: rect ? Math.round(Math.max(0, Math.min(innerHeight, rect.bottom) - Math.max(0, rect.top)) / rect.height * 1000) / 1000 : null,
      canvas_entirely_inside_initial_viewport: !!(rect && rect.y >= 0 && rect.bottom <= innerHeight),
      status: document.getElementById('status')?.textContent || null,
      hint: document.getElementById('hint')?.textContent || null,
    };
  });
}

async function run() {
  await mkdir(outputRoot, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const actualBrowserVersion = browser.version();
  const results = [];
  let failed = false;
  try {
    for (const viewport of viewports) {
      const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, deviceScaleFactor: 1 });
      await context.addInitScript(() => {
        // Same visual scenarios across candidates: deterministic route input, not a production patch.
        const getRandomValuesOriginal = Crypto.prototype.getRandomValues;
        Crypto.prototype.getRandomValues = function (array) {
          if (array instanceof Uint32Array && array.length === 1) {
            array[0] = 41820631;
            return array;
          }
          return getRandomValuesOriginal.call(this, array);
        };
      });
      const page = await context.newPage();
      const errors = [];
      const blocked = [];
      page.on('pageerror', error => errors.push({ type: 'pageerror', message: String(error) }));
      page.on('console', m => { if (m.type() === 'error') errors.push({ type: 'console.error', message: m.text() }); });
      page.on('requestfailed', request => errors.push({ type: 'requestfailed', url: request.url(), failure: request.failure() }));
      await page.route('**/*', route => {
        if (!route.request().url().startsWith(origin + '/')) {
          blocked.push(route.request().url());
          route.abort('blockedbyclient');
        } else route.continue();
      });
      const response = await page.goto(origin + '/', { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(350);
      const canvas = page.locator('#game');
      if (!response || response.status() !== 200 || await canvas.count() !== 1) throw new Error('Frozen build did not return a visible canvas');
      const initial = await metadata(page);
      const screenshots = [];
      async function snap(stage) {
        const whole = join(outputRoot, `${viewport.id}-${stage}-page.png`);
        const canvasPath = join(outputRoot, `${viewport.id}-${stage}-canvas.png`);
        const viewportPath = join(outputRoot, `${viewport.id}-${stage}-viewport.png`);
        await page.screenshot({ path: whole, fullPage: true, animations: 'disabled' });
        await page.screenshot({ path: viewportPath, fullPage: false, animations: 'disabled' });
        await canvas.screenshot({ path: canvasPath, animations: 'disabled' });
        screenshots.push({ stage, page: await fileEntry(whole, outputRoot), viewport: await fileEntry(viewportPath, outputRoot), canvas: await fileEntry(canvasPath, outputRoot) });
      }
      await snap('initial');
      await canvas.focus();
      // Ordinary real browser input only. No direct state injection, patching, or hidden-game API.
      await page.keyboard.down('ArrowLeft');
      await page.waitForTimeout(180);
      await page.keyboard.down('Space');
      await page.waitForTimeout(210);
      await snap('jump');
      await page.keyboard.up('Space');
      await page.keyboard.up('ArrowLeft');
      await page.waitForTimeout(620);
      await snap('after-input');
      const final = await metadata(page);
      const uiLayoutIssues = [];
      if (variantId === 'candidate-02-r1') {
        const coords = initial.controls.slice(0, 4).map(c => c.bounding_css_px);
        const opts = initial.controls.slice(0, 4);
        const near = (a, b, tolerance = 1) => Math.abs(a-b) <= tolerance;
        if (viewport.id.startsWith('mobile-portrait')) {
          const [room, difficulty, style, restart] = coords;
          const columnGap = difficulty.x - (room.x + room.width);
          const rowGap = style.y - (room.y + room.height);
          if (!near(room.x, style.x) || !near(difficulty.x, restart.x) ||
              !near(room.y, difficulty.y) || !near(style.y, restart.y))
            uiLayoutIssues.push('portrait 2 x 2 grid rows/columns do not align');
          if (!coords.every(c => near(c.width, room.width) && c.height >= 40))
            uiLayoutIssues.push('portrait control boxes do not have consistent widths and 40px+ height');
          if (columnGap < 10 || rowGap < 8)
            uiLayoutIssues.push(`portrait grid spacing too small (${columnGap}, ${rowGap})`);
          if (opts.some(c => c.text_align !== 'left'))
            uiLayoutIssues.push('portrait controls are not left-aligned');
        }
        if (viewport.id === 'mobile-landscape') {
          for (let i = 0; i < 3; i++) {
            const gap = coords[i+1].x - (coords[i].x + coords[i].width);
            if (gap < 12) uiLayoutIssues.push(`landscape gap ${i} too small (${gap})`);
          }
        }
        if (coords.some(c => c.x < 0 || c.x + c.width > viewport.width + 1))
          uiLayoutIssues.push('controls outside viewport');
      }
      results.push({
        viewport, url: page.url(), http_status: response.status(),
        initial, final, screenshots, errors, blocked_requests: blocked,
        revision_layout_gate: variantId === 'candidate-02-r1' ? { passed: uiLayoutIssues.length === 0, issues: uiLayoutIssues } : null,
        input: [{ action: 'focus canvas' }, { action: 'hold ArrowLeft', duration_ms: 180 }, { action: 'hold Space + ArrowLeft', duration_ms: 210 }, { action: 'release', wait_ms: 620 }],
        verified_states: ['initial canvas display', 'real keyboard input issued'],
        not_verified: ['successful platform landing', 'narrow-bridge cue', 'moving-rail target', 'blocked-warning text', 'human assessment', 'visual improvement or rework reduction'],
      });
      if (errors.length || initial.horizontal_overflow || final.horizontal_overflow || initial.canvas_visible_fraction_in_initial_viewport < 0.999 || uiLayoutIssues.length) failed = true;
      await context.close();
    }
  } finally { await browser.close(); }
  const report = {
    schema_version: 'et-visual-reviewer-revision-v0.2',
    variant_id: variantId,
    test_only_seed: 41820631,
    source_repo: 'https://github.com/siskosun/echo-tide',
    pinned_source_sha: frozenRef,
    provenance: 'Ephemeral same-author visual variant of pinned GitHub source, built within runner. Not a production game-exp Candidate, not independent A/B production, not an art review.',
    game_exp_status: 'read-only external observation; no Candidate/Review/Ledger mutation',
    visual_pilot_task: 'ET-VISUAL-01',
    independent_executors: false,
    evidence_type: 'real browser screenshot of manually designed exploratory candidate',
    browser: { description: 'Playwright Chrome headless in GitHub-hosted Ubuntu', version: actualBrowserVersion, viewport_only_not_actual_phone: true },
    build_files: await hashedBuild(),
    fontconfig: await fileEntry(join(outputRoot, 'fontconfig.txt'), outputRoot),
    outputs: results,
    browser_technical_ok: !failed,
    recorded_variant_manifest: await fileEntry(join(sourceRoot, 'visual-eval/lineage.json')),
    report_scope: 'Screenshots, browser console, viewport/canvas geometry and input dispatch only. No subjective art approval or actual asset-production timing.',
  };
  const reportPath = join(outputRoot, 'runtime-report.json');
  await writeFile(reportPath, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ report: reportPath, technical_ok: report.browser_technical_ok, screenshots: results.reduce((acc, r) => acc+r.screenshots.length*3, 0), viewport_count: results.length }));
  if (failed) process.exitCode = 1;
}

run().catch(e => { console.error(e); process.exitCode = 1; });
