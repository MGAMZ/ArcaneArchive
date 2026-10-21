const fs = require('fs');
const path = require('path');
const { openContext } = require('./harvest.js');
const { extractItem } = require('./extract.js');

const RAW = '/tmp/skwiki/raw';
const TXT = '/tmp/skwiki/txt';
const LOG = '/tmp/skwiki/harvest.log';
const FAIL = '/tmp/skwiki/failed.json';
fs.mkdirSync(RAW, { recursive: true });
fs.mkdirSync(TXT, { recursive: true });

const BATCH = 100;
const SETTLE_MS = 90;
const NAV_TIMEOUT = 25000;
const MAX_ITEM_ATTEMPTS = 3;

const items = JSON.parse(fs.readFileSync('/tmp/skwiki/items_all.json', 'utf8'));
const detailUrl = (it) =>
  `https://wiki.skland.com/endfield/detail?mainTypeId=${it.mainTypeId}&subTypeId=${it.subTypeId}&gameEntryId=${it.itemId}&header=0`;

function log(msg) {
  const line = `[${new Date().toISOString().slice(11, 19)}] ${msg}`;
  console.log(line);
  fs.appendFileSync(LOG, line + '\n');
}

const have = (id) => {
  const p = path.join(RAW, id + '.json');
  return fs.existsSync(p) && fs.statSync(p).size > 200;
};

// Errors that mean the browser/context is unusable and the batch must restart.
const isFatalBrowserError = (e) => {
  const m = String((e && e.message) || '');
  return /Target (page|closed)|context or browser has been closed|browser has disconnected|Protocol error|Connection closed|net::ERR|Timeout \d+ms exceeded/i.test(m);
};

function waitForItem(page, id, timeoutMs) {
  return new Promise((resolve) => {
    const onRes = async (res) => {
      if (!res.url().includes('/web/v1/wiki/item/info?id=' + id)) return;
      if (res.status() !== 200) return;
      let b; try { b = await res.text(); } catch (e) { return; }
      let j; try { j = JSON.parse(b); } catch (e) { return; }
      if (j.code !== 0) return;
      try { page.off('response', onRes); } catch (e) {}
      clearTimeout(to);
      resolve(j);
    };
    page.on('response', onRes);
    const to = setTimeout(() => { try { page.off('response', onRes); } catch (e) {} resolve(null); }, timeoutMs);
  });
}

async function saveItem(it, json) {
  fs.writeFileSync(path.join(RAW, it.itemId + '.json'), JSON.stringify(json));
  try {
    fs.writeFileSync(path.join(TXT, it.itemId + '.txt'), extractItem(json.data.item));
  } catch (e) {
    fs.writeFileSync(path.join(TXT, it.itemId + '.txt'), '[EXTRACT ERROR] ' + e.message);
  }
}

// Returns the ids saved in this batch. Throws on browser-level failure.
async function runBatch(batch, attempts) {
  const ctx = await openContext();
  const saved = [];
  try {
    const page = ctx.pages()[0] || (await ctx.newPage());
    await page.goto(detailUrl(batch[0]), { waitUntil: 'domcontentloaded', timeout: 90000 });
    await page.waitForTimeout(9000);

    for (const it of batch) {
      if (have(it.itemId)) { saved.push(it.itemId); continue; }
      try {
        const p = waitForItem(page, it.itemId, NAV_TIMEOUT);
        await page.evaluate((u) => {
          window.history.pushState({}, '', u);
          window.dispatchEvent(new PopStateEvent('popstate', { state: {} }));
        }, detailUrl(it));
        const json = await p;
        if (!json) throw new Error('nav timeout');
        await saveItem(it, json);
        saved.push(it.itemId);
      } catch (e) {
        if (isFatalBrowserError(e)) throw e; // restart whole batch
        attempts[it.itemId] = (attempts[it.itemId] || 0) + 1;
        log(`  item fail ${it.itemId} ${it.name} (attempt ${attempts[it.itemId]}): ${String(e.message).split('\n')[0]}`);
      }
      await new Promise((r) => setTimeout(r, SETTLE_MS));
    }
    return saved;
  } finally {
    try { await ctx.close(); } catch (e) {}
  }
}

(async () => {
  const attempts = {};
  log(`start: total=${items.length} pending=${items.filter((i) => !have(i.itemId)).length}`);
  let batchFailStreak = 0;

  for (let round = 0; round < 60; round++) {
    const pending = items.filter((it) => !have(it.itemId) && (attempts[it.itemId] || 0) < MAX_ITEM_ATTEMPTS);
    if (!pending.length) { log(`round ${round}: nothing pending`); break; }

    const batch = pending.slice(0, BATCH);
    try {
      const saved = await runBatch(batch, attempts);
      batchFailStreak = 0;
      log(`round ${round}: saved ${saved.length}/${batch.length} | remaining ${pending.length - saved.length}`);
    } catch (e) {
      batchFailStreak++;
      log(`round ${round}: browser error (${batchFailStreak}) ${String(e.message).split('\n')[0]} | remaining ${pending.length}`);
      if (batchFailStreak >= 8) { log('too many consecutive browser failures; aborting'); break; }
      await new Promise((r) => setTimeout(r, 5000));
    }
  }

  const failed = items.filter((it) => !have(it.itemId));
  fs.writeFileSync(FAIL, JSON.stringify(failed, null, 1));
  log(`DONE saved=${items.length - failed.length} failed=${failed.length}`);
  if (failed.length) log('failed ids: ' + failed.map((f) => f.itemId + '(' + f.name + ')').join(', '));
})().catch((e) => { log('FATAL: ' + e.message); process.exit(1); });
