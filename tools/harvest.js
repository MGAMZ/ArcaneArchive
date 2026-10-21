const fs = require('fs');
const path = require('path');
const PW = '/home/mgam/.local/lib/qwen-code/lib/bundled/browser-use/runtime/node_modules/playwright-core';
const { chromium } = require(PW);

const EXE = '/home/mgam/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome';
const PROFILE = '/tmp/skwiki/profile';
const OUT = '/tmp/skwiki/data';
fs.mkdirSync(OUT, { recursive: true });

const START = 'https://wiki.skland.com/endfield?header=0';

async function openContext() {
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    executablePath: EXE,
    headless: true,
    locale: 'zh-CN',
    viewport: { width: 1600, height: 1000 },
    userAgent:
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--lang=zh-CN'],
  });
  return ctx;
}

// Capture every successful wiki API JSON response, deduped by URL.
function attachRecorder(page, sink) {
  page.on('response', async (res) => {
    const u = res.url();
    if (!/zonai\.skland\.com\/(web|api)\/v1\/wiki\//.test(u)) return;
    if (res.status() !== 200) return;
    let body;
    try {
      body = await res.text();
    } catch (e) {
      return;
    }
    let json;
    try {
      json = JSON.parse(body);
    } catch (e) {
      return;
    }
    if (json.code !== 0) return;
    const key = u;
    if (sink.has(key) && sink.get(key).length >= body.length) return;
    sink.set(key, body);
  });
}

function flush(sink) {
  let n = 0;
  for (const [url, body] of sink) {
    const safe = url
      .replace('https://zonai.skland.com/', '')
      .replace(/[?&=]/g, '_')
      .replace(/[^A-Za-z0-9_.-]/g, '_')
      .replace(/_+$/g, '')
      .slice(0, 150);
    const p = path.join(OUT, safe + '.json');
    fs.writeFileSync(p, body);
    n++;
  }
  return n;
}

module.exports = { openContext, attachRecorder, flush, START, OUT, PROFILE };

if (require.main === module) {
  (async () => {
    const ctx = await openContext();
    const page = ctx.pages()[0] || (await ctx.newPage());
    const sink = new Map();
    attachRecorder(page, sink);
    await page.goto(START, { waitUntil: 'domcontentloaded', timeout: 90000 });
    await page.waitForTimeout(15000);
    const n = flush(sink);
    console.log('saved', n, 'responses');
    for (const u of sink.keys()) console.log(' -', u);
    await ctx.close();
  })().catch((e) => {
    console.error('FATAL:', e.message);
    process.exit(1);
  });
}
