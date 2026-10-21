// Cross-corpus search for references to the operator 诀 (real name 李织烟).
// Handles the single-character false-positive problem: 秘诀/口诀/诀窍/诀别/永诀/长诀/决诀 etc.
const fs = require('fs');
const path = require('path');

const TXT = '/tmp/skwiki/txt';
const items = JSON.parse(fs.readFileSync('/tmp/skwiki/items_all.json', 'utf8'));
const meta = {};
for (const it of items) meta[it.itemId] = it;

// Compound words containing 诀 that are NOT a reference to the operator.
// Built empirically from all 397 occurrences of 诀 in the 2478-item corpus
// (see window-frequency audit): every X诀 / 诀X collocation was classified.
const FALSE_JUE = [
  // common Chinese words
  '秘诀', '口诀', '诀窍', '诀别', '永诀', '长诀', '决诀', '诀要', '真诀', '妙诀', '歌诀', '丹诀',
  // other operators' skill names
  '惊霆诀', '霆诀',            // 庄方宜 战技「惊霆诀」
  // 诀's own skill names (her kit, not a third-party reference to her)
  '阵诀',                      // 阵诀·智 / 阵诀·意
  '破晦诀明', '晦诀明', '晦诀', // 终结技二段「破晦诀明」
  '剑诀',
];

// Mask false positives so remaining 诀 occurrences are (near-)certainly the operator.
function mask(text) {
  let out = text;
  for (const w of FALSE_JUE) out = out.split(w).join('\u0000'.repeat(w.length));
  return out;
}

const TERMS = [
  { key: '李织烟', re: /李织烟/g, weight: 'unambiguous' },
  { key: '织烟', re: /(?<!李)织烟/g, weight: 'unambiguous' },
  { key: '诀', re: /诀/g, weight: 'needs-mask' },
];

function findHits(text) {
  const masked = mask(text);
  const hits = [];
  for (const t of TERMS) {
    if (t.key === '诀') continue; // handled via masked text below
    let m;
    const re = new RegExp(t.re.source, 'g');
    while ((m = re.exec(text)) !== null) hits.push({ term: t.key, idx: m.index });
  }
  let m;
  const re = /诀/g;
  while ((m = re.exec(masked)) !== null) hits.push({ term: '诀', idx: m.index });
  return hits.sort((a, b) => a.idx - b.idx);
}

function context(text, idx, before = 90, after = 90) {
  const s = Math.max(0, idx - before);
  const e = Math.min(text.length, idx + before + after);
  return (s > 0 ? '…' : '') + text.slice(s, e).replace(/\s+/g, ' ') + (e < text.length ? '…' : '');
}

// Which section (章/板块/tab) does a character offset belong to?
function sectionAt(lines, lineIdx) {
  let ch = '', wg = '', tb = '';
  for (let i = 0; i <= lineIdx; i++) {
    const l = lines[i];
    if (l.startsWith('######## [章] ')) { ch = l.replace('######## [章] ', ''); wg = ''; tb = ''; }
    else if (l.startsWith('#### [板块] ')) { wg = l.replace('#### [板块] ', '').replace(/\s*\(widget=.*$/, ''); tb = ''; }
    else if (l.trim().startsWith('-- [tab] ')) { tb = l.trim().replace('-- [tab] ', ''); }
  }
  return [ch, wg, tb].filter(Boolean).join(' › ');
}

function analyze(targetIds) {
  const files = targetIds
    ? targetIds.map((x) => (String(x).endsWith('.txt') ? String(x) : String(x) + '.txt'))
    : fs.readdirSync(TXT).filter((f) => f.endsWith('.txt'));
  const results = [];
  for (const f of files) {
    const id = f.replace('.txt', '');
    const p = path.join(TXT, f);
    let text;
    try { text = fs.readFileSync(p, 'utf8'); } catch (e) { continue; }
    const hits = findHits(text);
    if (!hits.length) continue;
    const lines = text.split('\n');
    // map char offset -> line index
    const lineStart = [];
    let acc = 0;
    for (const l of lines) { lineStart.push(acc); acc += l.length + 1; }
    const lineOf = (idx) => {
      let lo = 0, hi = lineStart.length - 1;
      while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (lineStart[mid] <= idx) lo = mid; else hi = mid - 1; }
      return lo;
    };

    // group hits by line so we emit one context per line
    const byLine = new Map();
    for (const h of hits) {
      const li = lineOf(h.idx);
      if (!byLine.has(li)) byLine.set(li, { terms: new Set(), line: lines[li] });
      byLine.get(li).terms.add(h.term);
    }

    const m = meta[id] || {};
    results.push({
      itemId: id,
      name: m.name || '?',
      category: m.subName || '?',
      mainType: m.mainTypeId,
      totalHits: hits.length,
      terms: Array.from(new Set(hits.map((h) => h.term))),
      lines: Array.from(byLine.entries())
        .sort((a, b) => a[0] - b[0])
        .map(([li, v]) => ({ section: sectionAt(lines, li), terms: Array.from(v.terms), text: v.line.trim() })),
    });
  }
  return results.sort((a, b) => b.totalHits - a.totalHits);
}

module.exports = { analyze, mask, FALSE_JUE };

if (require.main === module) {
  const res = analyze();
  fs.writeFileSync('/tmp/skwiki/jue_mentions.json', JSON.stringify(res, null, 1));
  console.log('items with mentions:', res.length);
  const byCat = {};
  for (const r of res) byCat[r.category] = (byCat[r.category] || 0) + 1;
  console.log('by category:', JSON.stringify(byCat, null, 1));
  console.log('\n=== top items by hit count ===');
  for (const r of res.slice(0, 45)) {
    console.log(String(r.totalHits).padStart(4), r.itemId.padEnd(6), r.category.padEnd(8), r.name, '|', r.terms.join('+'));
  }
}
