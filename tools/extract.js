// Converts a Skland Endfield wiki `item/info` payload into ordered, readable text.
const fs = require('fs');

function inlineToText(el) {
  if (!el) return '';
  if (el.kind === 'text') return (el.text && el.text.text) || '';
  if (el.kind === 'entry') {
    const e = el.entry || {};
    return `\u3010entry:${e.id}${e.count ? 'x' + e.count : ''}\u3011`;
  }
  if (el.kind === 'link') {
    const l = el.link || el.text || {};
    return (l.text && l.text.text) || l.url || '';
  }
  if (el.text && el.text.text) return el.text.text;
  return '';
}

function blockText(b) {
  if (!b) return '';
  if (b.kind === 'text' || b.kind === 'quote') {
    const ies = (b.text && b.text.inlineElements) || [];
    const s = ies.map(inlineToText).join('');
    return b.kind === 'quote' ? '> ' + s : s;
  }
  if (b.kind === 'image') return '[image]';
  if (b.kind === 'horizontalLine') return '---';
  if (b.kind === 'externalVideo') return '[video]';
  if (b.kind === 'table') return null; // handled separately
  const ies = (b.text && b.text.inlineElements) || [];
  return ies.map(inlineToText).join('');
}

function renderDoc(doc, documentMap, depth = 0) {
  if (!doc) return [];
  const bm = doc.blockMap || {};
  const childrenOf = {};
  for (const b of Object.values(bm)) {
    const p = b.parentId || 'document-id';
    (childrenOf[p] = childrenOf[p] || []).push(b);
  }

  // Collect the rendering of one block (and its descendants) into `target`.
  // Each block is emitted exactly once; table cells are flattened to one line.
  const collect = (block, indent, target) => {
    if (!block) return;
    if (block.kind === 'table') {
      const t = block.table || {};
      for (const r of t.rowIds || []) {
        const cells = [];
        for (const c of t.columnIds || []) {
          const cellParts = [];
          for (const cb of childrenOf[`${r}_${c}`] || []) collect(cb, '', cellParts);
          cells.push(cellParts.join(' ').replace(/\s+/g, ' ').trim());
        }
        const line = cells.join(' | ').replace(/(\s\|\s)+$/g, '').trim();
        if (line && line !== '|') target.push(indent + '| ' + line + ' |');
      }
      return;
    }
    const s = blockText(block);
    if (s !== null && s !== '') target.push(indent + s);
    for (const cb of childrenOf[block.id] || []) collect(cb, indent + '  ', target);
  };

  const out = [];
  for (const id of doc.blockIds || []) collect(bm[id], '', out);
  return out;
}

function extractItem(item) {
  const d = item.document || {};
  const dm = d.documentMap || {};
  const wm = d.widgetCommonMap || {};
  const lines = [];
  const chapters = d.chapterGroup || [];

  for (const ch of chapters) {
    lines.push(`\n######## [章] ${ch.title}`);
    for (const wgt of ch.widgets || []) {
      const w = wm[wgt.id];
      lines.push(`\n#### [板块] ${wgt.title}  (widget=${wgt.id}${w ? ', type=' + w.type : ''})`);
      if (!w) {
        lines.push('  (no widget data)');
        continue;
      }
      if (w.tableList && w.tableList.length) {
        for (const row of w.tableList) {
          lines.push(`  ${row.label}: ${row.value}`);
        }
      }
      const tabList = w.tabList || [];
      const tabTitle = {};
      for (const t of tabList) tabTitle[t.tabId] = t.title;
      const tdm = w.tabDataMap || {};
      for (const tabId of Object.keys(tdm)) {
        const td = tdm[tabId];
        const tname = tabTitle[tabId] || tabId;
        lines.push(`\n  -- [tab] ${tname}`);
        if (td.intro) {
          const introDoc = dm[td.intro];
          if (introDoc) renderDoc(introDoc, dm).forEach((l) => lines.push('  intro> ' + l));
          else lines.push('  intro> ' + String(td.intro).slice(0, 400));
        }
        if (td.content && dm[td.content]) {
          renderDoc(dm[td.content], dm).forEach((l) => lines.push('  ' + l));
        }
        if (td.audioList && td.audioList.length) {
          for (const a of td.audioList) {
            lines.push(`  [语音] ${a.title || ''} :: ${a.profile || ''}`);
          }
        }
      }
      if (w.dialogList && w.dialogList.length) {
        for (const dlg of w.dialogList) lines.push('  [dialog] ' + JSON.stringify(dlg).slice(0, 500));
      }
    }
  }
  return lines.join('\n');
}

module.exports = { extractItem };

if (require.main === module) {
  const p = process.argv[2] || '/tmp/skwiki/jue_item_info.json';
  const j = JSON.parse(fs.readFileSync(p, 'utf8'));
  const txt = extractItem(j.data.item);
  const out = p.replace(/\.json$/, '.txt');
  fs.writeFileSync(out, txt);
  console.log('wrote', out, txt.length, 'chars,', txt.split('\n').length, 'lines');
}
