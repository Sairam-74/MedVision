// Real browser demonstration. No credentials, traces or cookies are saved.
import { chromium } from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { setTimeout as sleep } from 'node:timers/promises';

const root = process.cwd();
const output = path.join(root, process.env.MEDVISION_BROWSER_OUTPUT || 'experiments/session_20261006_p6p7/browser');
await fs.mkdir(output, { recursive: true });
const password = (await fs.readFile(path.join(root, '.local_demo/demo_password.txt'), 'utf8')).trim();
const executablePath = process.env.MEDVISION_BROWSER || path.join(process.env.LOCALAPPDATA, 'ms-playwright/chromium-1234/chrome-win64/chrome.exe');
const browser = await chromium.launch({ headless: true, executablePath });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, recordVideo: { dir: output, size: { width: 1440, height: 1000 } } });
const page = await context.newPage();
const errors = [];
const checks = [];
const timings = [];
const base = 'http://localhost:8000';
page.on('pageerror', (error) => errors.push(error.message));
function check(value, message) { if (!value) throw new Error(message); checks.push(message); }
const screenshot = async (name) => { await page.evaluate(() => window.scrollTo(0, 0)); return page.screenshot({ path: path.join(output, name + '.png'), fullPage: true }); };
try {
  let healthy = false;
  for (let attempt = 0; attempt < 30; attempt++) {
    try { healthy = (await context.request.get(base + '/health', { timeout: 1000 })).ok(); }
    catch { /* The local server may still be starting; retry within this bound. */ }
    if (healthy) break;
    await sleep(500);
  }
  check(healthy, 'local server ready before browser rehearsal');
  await page.goto(base + '/login');
  await page.getByRole('heading', { name: 'Welcome back' }).waitFor();
  await page.getByLabel('Email', { exact: true }).fill('demo.clinician@example.invalid');
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('heading', { name: 'Home dashboard' }).waitFor();
  check(!await page.getByRole('link', { name: 'Sign up', exact: true }).count(), 'signed-in workspace keeps account actions on authentication pages');
  await screenshot('desktop_dashboard');
  const fixtures = JSON.parse(await fs.readFile(path.join(output, '../browser_inputs/inputs.json'), 'utf8'));
  const cases = [];
  for (const fixture of fixtures) {
    await page.goto(base + '/upload');
    await page.getByRole('heading', { name: 'Image intake station' }).waitFor();
    const started = performance.now();
    const upload = page.waitForResponse((response) => response.url() === base + '/analyses' && response.request().method() === 'POST');
    await page.locator('input[type=file]').setInputFiles(path.join(root, fixture.path));
    const uploaded = await upload;
    check(uploaded.ok(), 'real multipart accepted: ' + fixture.id);
    const { analysisId } = await uploaded.json();
    await page.waitForURL(base + '/results/' + analysisId, { timeout: 90000 });
    await page.getByRole('heading', { name: 'Prediction result' }).waitFor();
    await page.waitForFunction(() => [...document.querySelectorAll('figure img')].length === 2 && [...document.querySelectorAll('figure img')].every((img) => img.complete && img.naturalWidth > 0));
    timings.push(performance.now() - started);
    const result = await (await context.request.get(base + '/analyses/' + analysisId)).json();
    const original = await context.request.get(base + result.originalImageUrl);
    const hash = crypto.createHash('sha256').update(await original.body()).digest('hex');
    check(hash === fixture.sha256, 'displayed original belongs to upload: ' + fixture.id);
    check(await page.locator('figure img').first().evaluate((img) => img.naturalWidth > 0 && Math.abs(img.clientWidth / img.clientHeight - img.naturalWidth / img.naturalHeight) < .02), 'original image keeps native aspect ratio');
    check(await page.getByText(/Research prototype/).count() === 1, 'research disclaimer visible');
    check(result.metrics.dice === null && result.metrics.iou === null, 'no fabricated uploaded-image accuracy');
    const downloadEvent = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Export result JSON' }).click();
    const download = await downloadEvent;
    await download.saveAs(path.join(output, fixture.id + '-result.json'));
    const exported = JSON.parse(await fs.readFile(path.join(output, fixture.id + '-result.json'), 'utf8'));
    check(exported.analysisId === analysisId, 'export belongs to current case');
    cases.push({ analysisId, image: fixture.id, modelSha256: result.modelSha256, fractureStatus: result.fractureStatus });
    await screenshot(fixture.id + '_result');
    await page.reload();
    await page.getByRole('heading', { name: 'Prediction result' }).waitFor();
    check(page.url().endsWith(analysisId), 'session restores on protected deep-link reload');
  }
  check(cases[0].analysisId !== cases[1].analysisId, 'distinct real uploads create distinct results');
  await page.goto(base + '/history');
  await page.getByRole('heading', { name: 'History', exact: true }).waitFor();
  await screenshot('desktop_history');
  const history = await (await context.request.get(base + '/analyses')).json();
  const historical = history.filter((entry) => entry.status === 'completed' && !cases.some((current) => current.analysisId === entry.id)).at(-1);
  if (historical) {
    const historicalResult = await (await context.request.get(base + '/analyses/' + historical.id)).json();
    check(historicalResult.originalImageUrl.startsWith('/generated/'), 'legacy history uses current protected image origin');
    await page.goto(base + '/results/' + historical.id);
    await page.getByRole('heading', { name: 'Prediction result' }).waitFor();
    await page.waitForFunction(() => [...document.querySelectorAll('figure img')].length === 2 && [...document.querySelectorAll('figure img')].every((img) => img.complete && img.naturalWidth > 0));
    checks.push('persisted legacy original and overlay load after authentication changes');
  }
  await page.goto(base + '/profile');
  await page.getByRole('heading', { name: 'Profile', exact: true }).waitFor();
  check(await page.getByText('Account details').count() === 1 && !await page.getByRole('button', { name: 'Save changes' }).count(), 'profile shows real account without fake controls');
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('button', { name: 'Open navigation' }).click();
  await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
  await page.getByRole('heading', { name: 'Home dashboard' }).waitFor();
  checks.push('first mobile navigation item is not covered by the header');
  await screenshot('mobile_dashboard');
  await page.getByRole('button', { name: 'Open navigation' }).click();
  await page.getByRole('link', { name: 'Research', exact: true }).click();
  await page.getByRole('heading', { name: 'Research & evidence' }).waitFor();
  await page.getByRole('heading', { name: 'Training progress' }).waitFor();
  const researchResponse = await context.request.get(base + '/api/research');
  const research = await researchResponse.json();
  check(researchResponse.status() === 200 && research.dataset.total === 4017 && research.dataset.validation === 612, 'research UI uses actual frozen-manifest counts');
  check(research.runs.length === 3 && research.delivery.reservedTestEvaluated === false, 'research UI distinguishes incomplete experiments and reserved test');
  check(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), 'mobile research table scrolls without page overflow');
  await page.getByText('Why is there no accuracy score for my upload?', { exact: true }).click();
  check(await page.getByText(/A new upload has no expert reference mask/).isVisible(), 'methodology explanations expand');
  await screenshot('mobile_research');
  await page.setViewportSize({ width: 1440, height: 1000 });
  await screenshot('desktop_research');
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('button', { name: 'Open navigation' }).click();
  await page.getByRole('link', { name: 'Upload', exact: true }).click();
  await page.getByRole('heading', { name: 'Image intake station' }).waitFor();
  check(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), 'mobile upload has no horizontal page overflow');
  await screenshot('mobile_upload');
  await page.getByRole('button', { name: 'Toggle theme' }).click();
  await page.waitForFunction(() => document.documentElement.classList.contains('dark'));
  await page.waitForFunction(() => {
    const badge = [...document.querySelectorAll('div')].find((element) => element.textContent === 'JPG');
    return badge && window.getComputedStyle(badge).color === window.getComputedStyle(document.body).color;
  });
  check(await page.evaluate(() => window.getComputedStyle(document.body).backgroundColor !== 'rgb(248, 247, 241)'), 'dark theme changes background');
  await screenshot('mobile_dark_upload');
  await page.getByRole('button', { name: 'Logout', exact: true }).click();
  await page.getByRole('button', { name: 'Cancel', exact: true }).click();
  check(!await page.getByRole('heading', { name: 'Confirm logout' }).count(), 'logout Cancel closes dialog');
  await page.getByRole('button', { name: 'Logout', exact: true }).click();
  await page.getByRole('button', { name: 'Log out', exact: true }).click();
  await page.getByRole('heading', { name: 'Welcome back' }).waitFor();
  check((await context.request.get(base + '/analyses')).status() === 401, 'logout revokes backend access');
  const outsider = await browser.newContext();
  check((await outsider.request.get(base + '/analyses')).status() === 401, 'anonymous browser cannot read history');
  check((await outsider.request.get(base + '/generated/history.json')).status() === 401, 'anonymous browser cannot read saved files');
  await outsider.close();
  check(errors.length === 0, 'no browser runtime exceptions');
  await fs.rm(path.join(output, 'failure.json'), { force: true });
  await fs.writeFile(path.join(output, 'browser_checks.json'), JSON.stringify({ checks_passed: checks.length, checks, cases, upload_to_visible_result_ms: timings, browser_errors: errors, viewport: [1440,1000], mobile: [390,844], modelScope: 'original diagnostic checkpoint; no independent test claim', finalTestAccessed: false }, null, 2));
  console.log(JSON.stringify({ checks_passed: checks.length, cases, upload_to_visible_result_ms: timings }));
} catch (error) {
  await screenshot('failure');
  await fs.writeFile(path.join(output, 'failure.json'), JSON.stringify({ error: error.message, browser_errors: errors, checks }, null, 2));
  throw error;
} finally {
  const video = page.video();
  await context.close();
  if (video) await video.saveAs(path.join(output, 'medvision_demo.webm'));
  await browser.close();
}
