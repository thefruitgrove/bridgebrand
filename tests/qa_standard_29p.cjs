'use strict';
// BES 1.0 visual/PDF smoke: only reads committed public sample data.
// Runs against a local HTTP server in ephemeral GitHub Actions, never production.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const { spawnSync } = require('node:child_process');

const ROOT = path.join(__dirname, '..');
const artifactDir = path.join(ROOT, 'qa-artifacts', 'standard-29p');
fs.mkdirSync(artifactDir, { recursive: true });
const sample = JSON.parse(fs.readFileSync(path.join(ROOT, 'site', 'data', 'samples', 'ent-20261103.json'), 'utf8'));
const rankings = sample.rankings.filter(r => r.domain === 'ENT' && r.ranking_type === 'T100').sort((a, b) => a.rank - b.rank);
assert.equal(rankings.length, 100, 'fixed sample requires 100 complete ranked entities');

const errors = [];
const results = [];
const browserOptions = { headless: true, args: ['--no-sandbox'] };
const fixedA4 = '.pdf-preview-mode .print-report{display:block!important}.pdf-preview-mode .print-sheet{width:794px!important;min-width:794px!important;max-width:794px!important;height:1123px!important;min-height:1123px!important;max-height:1123px!important;overflow:hidden!important;margin:0 auto 16px!important}';

function urlFor(rank, edition = 'standard', language = '한국어') {
  const target = rankings[rank - 1];
  const alternatives = rankings.filter(r => r.external_id !== target.external_id).slice(0, 2);
  const params = new URLSearchParams({
    sample: 'ent-20261103',
    field: 'ENT',
    pick: target.external_id,
    compareA: alternatives[0].external_id,
    compareB: alternatives[1].external_id,
    language
  });
  if (edition === 'basic') params.set('briefing', 'basic');
  return 'http://127.0.0.1:8765/briefing.html?' + params.toString();
}
function pageMetrics() {
  return [...document.querySelectorAll('#printReportDocument .print-sheet')].map(sheet => {
    const body = sheet.querySelector('.print-sheet-main'), footer = sheet.querySelector('.print-sheet-footer');
    const sheetBox = sheet.getBoundingClientRect(), bodyBox = body.getBoundingClientRect();
    const footerTop = footer ? footer.getBoundingClientRect().top : sheetBox.bottom - 18;
    const bottomGap = +(footerTop - bodyBox.bottom).toFixed(1);
    const scrollOverflow = Math.max(0, body.scrollHeight - body.clientHeight);
    const beyondSheet = Math.max(0, bodyBox.bottom - sheetBox.bottom);
    return {
      page: Number(sheet.dataset.page),
      mainBottomGap: bottomGap,
      scrollOverflow: +scrollOverflow.toFixed(1),
      beyondSheet: +beyondSheet.toFixed(1),
      textCharacters: (body.innerText || '').length
    };
  });
}
async function inspect(browser, rank, edition, language, screenshots, savePdf) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 1 });
  const label = 'ENT-' + rank + '-' + edition + '-' + (language === '한국어' ? 'ko' : 'en');
  const jsErrors = [];
  page.on('pageerror', err => jsErrors.push(String(err.message || err)));
  try {
    await page.goto(urlFor(rank, edition, language), { waitUntil: 'domcontentloaded', timeout: 25000 });
    const expected = edition === 'basic' && language === '영어' ? 8 : edition === 'basic' ? 18 : 29;
    await page.waitForFunction(count => document.querySelectorAll('#printReportDocument .print-sheet').length === count, expected, { timeout: 40000 });
    await page.evaluate(async () => {
      document.body.classList.add('pdf-preview-mode');
      if (document.fonts?.ready) await document.fonts.ready;
    });
    await page.addStyleTag({ content: fixedA4 });
    const metrics = await page.evaluate(pageMetrics);
    const cssDiagnostics = await page.evaluate(() => {
      const grid = document.querySelector('#printReportDocument .print-table-split');
      const action = document.querySelector('#printReportDocument .print-sheet[data-page="25"] .print-action');
      const styles = [...document.querySelectorAll('link[rel="stylesheet"]')].map(x => x.getAttribute('href'));
      const state = element => element ? {
        display: getComputedStyle(element).display,
        columns: getComputedStyle(element).gridTemplateColumns,
        gap: getComputedStyle(element).gap
      } : null;
      return {grid:state(grid),action:state(action),styles};
    });
    assert.equal(metrics.length, expected, label + ': wrong sheet count');
    assert.ok(metrics.every((m, i) => m.page === i + 1), label + ': missing/duplicate page number');
    for (const n of screenshots) {
      if (n <= expected) {
        await page.locator('#printReportDocument .print-sheet[data-page="' + n + '"]').screenshot({
          path: path.join(artifactDir, label + '-p' + String(n).padStart(2, '0') + '.png'),
          timeout: 20000
        });
      }
    }
    let pdfPages = null;
    if (savePdf) {
      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await page.evaluate(() => document.getElementById('savePdf').click());
      const download = await downloadPromise;
      const file = path.join(artifactDir, label + '.pdf');
      await download.saveAs(file);
      const count = spawnSync('python', [
        '-c',
        'from pypdf import PdfReader; import sys; print(len(PdfReader(sys.argv[1]).pages))',
        file
      ], { encoding: 'utf8' });
      if (count.status !== 0) throw Error('PDF page counter failed: ' + count.stderr);
      pdfPages = Number(count.stdout.trim());
      assert.equal(pdfPages, expected, label + ': actual downloaded PDF page count');
    }
    const overflows = metrics.filter(m => m.scrollOverflow > 6 || m.beyondSheet > 6 || m.mainBottomGap < -6);
    const result = {
      case: label, expectedPages: expected, pdfPages, jsErrors,
      pageMetrics: metrics, cssDiagnostics, detectedOverflowPages: overflows.map(x => x.page),
      screenshotPages: screenshots.filter(n => n <= expected)
    };
    results.push(result);
    if (jsErrors.length) errors.push(label + ': JS runtime errors: ' + jsErrors.join('; '));
    if (overflows.length) errors.push(label + ': potential clipping on pages ' + overflows.map(o => o.page).join(','));
  } catch (err) {
    errors.push(label + ': ' + String(err.stack || err));
  } finally {
    await page.close();
  }
}

(async () => {
  const browser = await chromium.launch(browserOptions);
  try {
    await inspect(browser, 1, 'standard', '한국어', [1, 4, 10], false);
    await inspect(browser, 50, 'standard', '한국어', [10, 14, 16, 18, 20, 21, 23, 25, 29], true);
    await inspect(browser, 100, 'standard', '한국어', [10], false);
    await inspect(browser, 50, 'basic', '한국어', [4, 11, 14], false);
    await inspect(browser, 50, 'standard', '영어', [9, 10, 21], false);
  } finally {
    await browser.close();
  }
  fs.writeFileSync(path.join(artifactDir, 'qa-results.json'), JSON.stringify({
    fixedSampleId: sample.snapshotId, dataDate: sample.asOfDate, results, failures: errors
  }, null, 2));
  console.log(JSON.stringify(results.map(r => ({
    case: r.case, expected: r.expectedPages, downloadedPdfPages: r.pdfPages,
    overflowPages: r.detectedOverflowPages, runtimeErrors: r.jsErrors.length
  })), null, 2));
  if (errors.length) {
    console.error('BES 1.0 visual QA findings (release gate NOT cleared):\n' + errors.join('\n'));
    process.exitCode = 1;
  }
})().catch(err => {
  console.error(err);
  process.exitCode = 1;
});
