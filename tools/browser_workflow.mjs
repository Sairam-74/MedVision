import { chromium, expect } from '@playwright/test';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { Buffer } from 'node:buffer';
import { createHash } from 'node:crypto';
await mkdir('test-results', { recursive: true });
await writeFile(
  'test-results/synthetic-xray.png',
  Buffer.from(
    'iVBORw0KGgoAAAANSUhEUgAAAKAAAAB4CAAAAABQyaazAAAAyElEQVR4Ac3BAQEAAABAIP6fdkOJcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHcziHc/gWBdFLARW3xfsAAAAASUVORK5CYII=',
    'base64',
  ),
);
const base = 'http://localhost:8001';
const checks = [];
const browser = await chromium.launch({
  headless: true,
  executablePath:
    process.env.MEDVISION_BROWSER ||
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));

try {
  await expect
    .poll(
      async () => {
        try {
          return (await page.request.get(base + '/health')).status();
        } catch {
          return 0;
        }
      },
      { timeout: 30000 },
    )
    .toBe(200);
  await page.goto(base + '/login');
  await page
    .getByLabel('Email', { exact: true })
    .fill('feature.clinician@example.invalid');
  await page
    .getByLabel('Password', { exact: true })
    .fill(
      (await readFile('.feature_data/clinician_password.txt', 'utf8')).trim(),
    );
  await page.getByRole('button', { name: /^sign in$/i }).click();
  await expect(
    page.getByRole('heading', { name: /home dashboard/i }),
  ).toBeVisible();
  checks.push('real browser login and dashboard');
  await page.goto(base + '/upload');
  await page
    .getByLabel('Patient name', { exact: true })
    .fill('Synthetic Browser ' + Date.now());
  await page.getByLabel('Age', { exact: true }).fill('35');
  await page.getByLabel('Gender', { exact: true }).selectOption('Female');
  await page.getByLabel('Examination date', { exact: true }).fill('2026-10-14');
  await page.getByLabel('Body part', { exact: true }).fill('Forearm');
  await page.getByLabel('Laterality', { exact: true }).selectOption('Left');
  await page
    .getByLabel('Clinical history', { exact: true })
    .fill('Synthetic browser research fixture');
  await page
    .getByRole('button', { name: 'Save study and upload views' })
    .click();
  await page.waitForURL('**/studies/*');
  const studyId = page.url().split('/').at(-1);
  checks.push('patient-first intake persists and opens study');
  for (const view of ['AP', 'Lateral', 'Oblique']) {
    await page.getByLabel('View type', { exact: true }).selectOption(view);
    await page
      .getByLabel('Study X-ray', { exact: true })
      .setInputFiles('test-results/synthetic-xray.png');
    await page.getByRole('button', { name: 'Upload and analyze view' }).click();
    await expect
      .poll(
        async () => {
          const r = await page.request.get(base + '/studies/' + studyId);
          const s = await r.json();
          return s.images.filter(
            (i) => i.view_type === view && i.analysis.status === 'completed',
          ).length;
        },
        { timeout: 90000 },
      )
      .toBe(1);
    checks.push('real browser ' + view + ' upload and inference');
  }
  await expect(page.getByAltText('Original X-ray').first()).toBeVisible();
  await page
    .getByAltText('Original X-ray')
    .first()
    .evaluate((img) => img.decode());
  const viewport = page.getByTestId('viewer-viewport').first();
  const transform = page.getByTestId('viewer-transform').first();
  const original = page.getByAltText('Original X-ray').first();
  const src = await original.getAttribute('src');
  const beforeRaw = await (await page.request.get(src)).body();
  const beforeHash = createHash('sha256').update(beforeRaw).digest('hex');
  const firstScreenshot = await viewport.screenshot();
  await page.getByLabel('Brightness', { exact: true }).first().fill('160');
  await expect(original).toHaveCSS('filter', 'brightness(1.6) contrast(1)');
  const afterScreenshot = await viewport.screenshot();
  if (Buffer.compare(firstScreenshot, afterScreenshot) === 0)
    throw new Error('Brightness did not change rendered pixels');
  checks.push('brightness changes real rendered pixels and numeric display');
  await page.getByLabel('Contrast', { exact: true }).first().fill('145');
  await expect(original).toHaveCSS('filter', 'brightness(1.6) contrast(1.45)');
  checks.push('contrast changes displayed image');
  await page
    .getByRole('button', { name: 'Zoom in', exact: true })
    .first()
    .click();
  await expect(page.getByLabel('Zoom level').first()).toHaveText('125%');
  await viewport.hover();
  await page.mouse.wheel(0, -250);
  await expect
    .poll(async () => await page.getByLabel('Zoom level').first().textContent())
    .not.toBe('125%');
  checks.push('zoom button and mouse-wheel zoom');
  const box = await viewport.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(
    box.x + box.width / 2 + 70,
    box.y + box.height / 2 + 50,
    { steps: 5 },
  );
  await page.mouse.up();
  const moved = await transform.getAttribute('style');
  if (moved.includes('translate(0px, 0px)'))
    throw new Error('Pan transform did not move');
  checks.push('drag-to-pan changes shared layer transform');
  await page
    .getByRole('button', { name: 'Reset all adjustments' })
    .first()
    .click();
  await expect(original).toHaveCSS('filter', 'brightness(1) contrast(1)');
  await expect(page.getByLabel('Zoom level').first()).toHaveText('100%');
  checks.push('all viewer adjustments reset');
  await page.getByLabel('Display layer').first().selectOption('mask');
  await expect(
    page.getByAltText('Native segmentation mask').first(),
  ).toBeVisible();
  await page.getByLabel('Display layer').first().selectOption('overlay');
  await page.getByLabel('Overlay opacity', { exact: true }).first().fill('75');
  await expect(
    page.getByLabel('Aligned segmentation overlay').first(),
  ).toHaveCSS('opacity', '0.75');
  const dims = await page
    .locator('[data-testid="viewer-transform"]')
    .first()
    .evaluate((node) => ({
      children: node.children.length,
      transform: window.getComputedStyle(node).transform,
    }));
  if (dims.children !== 2) throw new Error('Layers do not share transform');
  checks.push('mask switching and overlay opacity share image transform');
  const unchanged = await (await page.request.get(src)).body();
  if (createHash('sha256').update(unchanged).digest('hex') !== beforeHash)
    throw new Error('Viewer modified original input');
  checks.push('viewer leaves original uploaded bytes unchanged');
  const study = await (
    await page.request.get(base + '/studies/' + studyId)
  ).json();
  await page
    .getByLabel('Select study view', { exact: true })
    .selectOption(study.images[1].id);
  await expect(
    page.getByRole('heading', { name: 'Lateral — completed', exact: true }),
  ).toBeVisible();
  checks.push('study view switching');
  await page.getByLabel('Compare all completed views').check();
  await expect(page.getByAltText('Original X-ray')).toHaveCount(3);
  checks.push('three-view comparison');
  await page.getByLabel('Compare all completed views').uncheck();
  await page
    .getByRole('button', { name: 'Submit preliminary feedback' })
    .click();
  await expect(page.getByText(/Preliminary ·/).first()).toBeVisible();
  checks.push('correct feedback saved through browser');
  await page.getByLabel('AI assessment').selectOption('incorrect');
  await page.getByLabel('Error category').selectOption('Wrong localization');
  await page
    .getByLabel('Feedback comments')
    .fill('Synthetic browser correction');
  await page
    .getByRole('button', { name: 'Submit preliminary feedback' })
    .click();
  await expect(page.getByText('Synthetic browser correction')).toBeVisible();
  checks.push('incorrect feedback saved through browser');
  await page.getByRole('button', { name: 'Generate report draft' }).click();
  await expect(page.getByLabel('Report findings')).toBeVisible();
  await page
    .getByLabel('Report findings')
    .fill('Synthetic radiologist-reviewed findings');
  await page
    .getByLabel('Report impression')
    .fill('Synthetic research impression');
  await page.getByLabel('AI suggestions').selectOption('corrected');
  await page.getByRole('button', { name: 'Save draft', exact: true }).click();
  await expect(page.getByText(/Revision 2 · Updated/)).toBeVisible();
  await page
    .getByRole('button', { name: 'Finalize report', exact: true })
    .click();
  await expect(page.getByLabel('Report findings')).toBeDisabled();
  await page.getByRole('button', { name: 'Reopen report' }).click();
  await expect(page.getByLabel('Report findings')).toBeEnabled();
  checks.push('report editing, persistence, finalization and reopening');
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.emulateMedia({ media: 'print' });
  await expect(page.locator('#radiology-report .print-only')).toBeVisible();
  await page.screenshot({
    path: 'test-results/report-print.png',
    fullPage: true,
  });
  checks.push(
    'structured print report includes persisted context and reviewed findings',
  );
  await page.emulateMedia({ media: 'screen' });
  await page.screenshot({
    path: 'test-results/study-browser.png',
    fullPage: true,
  });
  await page.goto(base + '/history');
  await page
    .getByLabel('Patient history search')
    .fill(study.patient.identifier);
  await expect(page.getByRole('link', { name: 'Open study' })).toBeVisible();
  checks.push('backend-backed patient identifier history search');
  await page.getByRole('link', { name: 'Open study' }).click();
  await expect(page.getByLabel('Report findings')).toHaveValue(
    'Synthetic radiologist-reviewed findings',
  );
  checks.push('previous study and edited report retrieved');
  await page.goto(base + '/upload');
  await page
    .getByLabel('Find returning patient')
    .fill(study.patient.identifier);
  await expect(
    page.getByLabel('Existing patient').locator('option'),
  ).toHaveCount(2);
  await page.getByLabel('Existing patient').selectOption(study.patient.id);
  await expect(
    page.getByLabel('Patient identifier', { exact: true }),
  ).toHaveValue(study.patient.identifier);
  checks.push('returning patient selection populates stored identity');
  await page.goto(base + '/research');
  await expect(
    page.getByText('Production model and reviewed-feedback training'),
  ).toBeVisible();
  await page.goto(base + '/profile');
  await expect(
    page.getByRole('heading', { name: /profile/i }).first(),
  ).toBeVisible();
  checks.push('research and profile navigation retained');
  if (errors.length) throw new Error('Browser errors: ' + errors.join('; '));
  await writeFile(
    'test-results/browser-workflow.json',
    JSON.stringify(
      {
        checks_passed: checks.length,
        checks,
        real_backend: true,
        real_checkpoint: true,
        synthetic_patient_data: true,
        study_id: studyId,
        browser_errors: errors,
      },
      null,
      2,
    ),
  );
  console.log(
    JSON.stringify({ checks_passed: checks.length, checks }, null, 2),
  );
} finally {
  await browser.close();
}
