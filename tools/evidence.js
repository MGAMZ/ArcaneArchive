const fs = require('fs');
const { analyze } = require('./analyze.js');
const items = require('./items_all.json');
const meta = {};
for (const i of items) meta[i.itemId] = i;

// Story-bearing categories only. 装备 hits are section titles ("推荐装备干员 › 诀");
// 百科速览 hits are aggregate stat tables; 干员攻略 is player-written, not official lore.
const GAMEPLAY_ONLY = new Set(['装备', '百科速览', '干员攻略']);

const all = analyze();
const out = [];
out.push('# 全语料中「诀 / 李织烟 / 织烟」命中汇总（已排除技能名与常用词误命中）');
out.push('# 语料：wiki.skland.com/endfield 全 2478 条目，采集于 2026-10-17');
out.push('');

const story = all.filter((r) => !GAMEPLAY_ONLY.has(r.category));
const gameplay = all.filter((r) => GAMEPLAY_ONLY.has(r.category));

out.push('## A. 叙事类命中（' + story.length + ' 个条目）');
for (const r of story) {
  out.push('');
  out.push(`### [${r.category}] ${r.name}  (itemId=${r.itemId}, 命中 ${r.totalHits}, 词形 ${r.terms.join('+')})`);
  const seen = new Set();
  for (const l of r.lines) {
    const key = l.text;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(`  <${l.section}>`);
    out.push('  ' + l.text);
  }
}

out.push('');
out.push('## B. 仅结构/数值/攻略类命中（不构成剧情证据，' + gameplay.length + ' 个条目）');
for (const r of gameplay) {
  out.push(`  - [${r.category}] ${r.name} (itemId=${r.itemId}, ${r.totalHits}) → ${r.lines[0] ? r.lines[0].section : ''}`);
}

// C. Cross-reference (entry card) links pointing at 诀 — catches pages that link
// to her without printing her name.
out.push('');
out.push('## C. 词条交叉引用（entry:1675）——正文未出现「诀」字但链接到她的条目');
const files = fs.readdirSync('/tmp/skwiki/txt').filter((f) => f.endsWith('.txt'));
const named = new Set(all.map((r) => r.itemId));
for (const f of files) {
  const id = f.replace('.txt', '');
  if (id === '1675') continue;
  const t = fs.readFileSync('/tmp/skwiki/txt/' + f, 'utf8');
  if (!t.includes('entry:1675')) continue;
  const m = meta[id] || {};
  out.push(`  - [${m.subName || '?'}] ${m.name} (itemId=${id})${named.has(id) ? '' : '   ← 仅链接、正文无「诀」字'}`);
}

fs.writeFileSync('/tmp/skwiki/evidence_mentions.txt', out.join('\n'));
console.log('wrote evidence_mentions.txt', out.length, 'lines');
console.log('story items:', story.length, '| gameplay-only:', gameplay.length);
