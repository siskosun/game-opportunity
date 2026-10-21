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
      return { id, visible: !!(el && el.getClientRects().length), bounding_css_px: r ? { x: r.x, y: r.y, width: r.width, height: r.height } : null };
    });
    return {
      title: document.title,
      viewport_css_px: { width: innerWidth, height: innerHeight },
      document_css_px: { scrollWidth: root.scrollWidth, scrollHeight: root.scrollHeight },
      horizontal_overflow: root.scrollWidth > innerWidth + 1,
      dpr: devicePixelRatio,
      canvas: canvas ? { bitmap_width: canvas.width, bitmap_height: canvas.height, css_rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height } } : null,
      controls: nodes,
      status: document.getElementById('status')?.textContent || null,
      hint: document.getElementById('hint')?.textContent || null,
    };
  });
}

async function run() {
  await mkdir(outputRoot, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const results = [];
  let failed = false;
  try {
    for (const viewport of viewports) {
      const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, deviceScaleFactor: 1 });
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
        await page.screenshot({ path: whole, fullPage: true, animations: 'disabled' });
        await canvas.screenshot({ path: canvasPath, animations: 'disabled' });
        screenshots.push({ stage, page: await fileEntry(whole, outputRoot), canvas: await fileEntry(canvasPath, outputRoot) });
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
      results.push({
        viewport, url: page.url(), http_status: response.status(),
        initial, final, screenshots, errors, blocked_requests: blocked,
        input: [{ action: 'focus canvas' }, { action: 'hold ArrowLeft', duration_ms: 180 }, { action: 'hold Space + ArrowLeft', duration_ms: 210 }, { action: 'release', wait_ms: 620 }],
        verified_states: ['initial canvas display', 'real keyboard input issued'],
        not_verified: ['successful platform landing', 'narrow-bridge cue', 'moving-rail target', 'blocked-warning text', 'human assessment', 'visual improvement or rework reduction'],
      });
      if (errors.length || initial.horizontal_overflow || final.horizontal_overflow) failed = true;
      await context.close();
    }
  } finally { await browser.close(); }
  const report = {
    schema_version: 'echo-runtime-capture-v0.1',
    source_repo: 'https://github.com/siskosun/echo-tide',
    pinned_source_sha: frozenRef,
    provenance: 'checked-out GitHub source built within the runner, not a human visual review',
    game_exp_status: 'read-only external observation; no Candidate/Review/Ledger mutation',
    visual_pilot_task: 'ET-VISUAL-01',
    browser: 'Playwright Chrome headless in GitHub-hosted Ubuntu',
    build_files: await hashedBuild(),
    outputs: results,
    browser_technical_ok: !failed,
    report_scope: 'Screenshots, browser console, viewport/canvas geometry and input dispatch only. No subjective art approval or actual asset-production timing.',
  };
  const reportPath = join(outputRoot, 'runtime-report.json');
  await writeFile(reportPath, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ report: reportPath, technical_ok: report.browser_technical_ok, screenshots: results.reduce((acc, r) => acc+r.screenshots.length*2, 0), viewport_count: results.length }));
  if (failed) process.exitCode = 1;
}

run().catch(e => { console.error(e); process.exitCode = 1; });
