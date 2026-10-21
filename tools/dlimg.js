// Download the text-bearing images of one item, named by their section.
const fs = require('fs');
const path = require('path');
const https = require('https');
const { inventory } = require('./images.js');

const OUT = '/tmp/skwiki/img';
fs.mkdirSync(OUT, { recursive: true });

// Sections worth OCR-ing (story / personnel text), matched as substrings.
const PRIORITY = process.env.SECTIONS
  ? process.env.SECTIONS.split('|')
  : ['蓬蓬的特邀嘉宾Q&A', '干员履历', '后勤备忘', '溯始先声', '干员叙事', 'Baker通信', '潜能明信片'];

function slug(s) {
  return s.replace(/[^\u4e00-\u9fa5A-Za-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 60);
}

function get(url, dest) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0', Referer: 'https://wiki.skland.com/' } }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return get(res.headers.location, dest).then(resolve, reject);
      }
      if (res.statusCode !== 200) return reject(new Error('HTTP ' + res.statusCode));
      const f = fs.createWriteStream(dest);
      res.pipe(f);
      f.on('finish', () => f.close(() => resolve(fs.statSync(dest).size)));
    });
    req.on('error', reject);
    req.setTimeout(45000, () => req.destroy(new Error('timeout')));
  });
}

(async () => {
  const itemId = process.argv[2];
  const inv = inventory(itemId);
  const jobs = [];
  const seen = new Set();
  for (const row of inv.rows) {
    if (!PRIORITY.some((p) => row.section.includes(p))) continue;
    if (row.url.endsWith('.gif')) continue; // animation, not text
    if (seen.has(row.url)) continue;
    seen.add(row.url);
    const ext = (row.url.match(/\.(png|jpe?g|webp)/i) || [, 'webp'])[1].toLowerCase();
    const idx = jobs.filter((j) => j.section === row.section).length + 1;
    const name = `${itemId}_${slug(row.section)}_${idx}.${ext === 'jpeg' ? 'jpg' : ext}`;
    jobs.push({ section: row.section, url: row.url, name });
  }
  console.log(`${itemId} ${inv.name}: ${jobs.length} 张待下载`);
  for (const j of jobs) {
    const dest = path.join(OUT, j.name);
    if (fs.existsSync(dest) && fs.statSync(dest).size > 1000) { console.log('  skip', j.name); continue; }
    try {
      const sz = await get(j.url, dest);
      console.log(`  ok ${j.name} (${(sz / 1024).toFixed(0)} KB) ← ${j.section}`);
    } catch (e) {
      console.log(`  FAIL ${j.name}: ${e.message}`);
    }
  }
  fs.writeFileSync(path.join(OUT, `${itemId}_manifest.json`), JSON.stringify(jobs, null, 1));
})();
