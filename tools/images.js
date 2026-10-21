// Inventory every image URL in an item payload, together with the section it lives in.
const fs = require('fs');

const IMG_RE = /^https?:\/\/\S+\.(?:png|jpe?g|webp|gif)(?:\?\S*)?$/i;

function collectUrls(node, path, out) {
  if (node === null || node === undefined) return;
  if (typeof node === 'string') {
    if (IMG_RE.test(node)) out.push({ path, url: node });
    return;
  }
  if (Array.isArray(node)) {
    node.forEach((v, i) => collectUrls(v, `${path}[${i}]`, out));
    return;
  }
  if (typeof node === 'object') {
    for (const k of Object.keys(node)) collectUrls(node[k], `${path}.${k}`, out);
  }
}

// Map a documentId -> the section label it is rendered under.
function buildDocIndex(item) {
  const d = item.document || {};
  const wm = d.widgetCommonMap || {};
  const map = {}; // docId -> "章 › 板块 › tab"
  const push = (docId, label) => { if (docId && typeof docId === 'string') map[docId] = label; };

  for (const ch of d.chapterGroup || []) {
    for (const w of ch.widgets || []) {
      const label0 = `${ch.title} › ${w.title}`;
      const wd = wm[w.id];
      if (!wd) continue;
      const tabTitle = {};
      for (const t of wd.tabList || []) tabTitle[t.tabId] = t.title;
      for (const tabId of Object.keys(wd.tabDataMap || {})) {
        const td = wd.tabDataMap[tabId];
        const label = tabTitle[tabId] ? `${label0} › ${tabTitle[tabId]}` : label0;
        push(td.intro, label + ' [intro]');
        push(td.content, label);
        // audioList / dialogList may carry cover images
        (td.audioList || []).forEach((a, i) => push(a.docId, `${label} [audio:${a.title || i}]`));
      }
      // widget-level images that are not inside a document
      if (wd.image) push(wd.image, label0 + ' [widget.image]');
    }
  }
  return map;
}

function inventory(itemId) {
  const j = JSON.parse(fs.readFileSync(`/tmp/skwiki/raw/${itemId}.json`, 'utf8'));
  const item = j.data.item;
  const out = [];
  collectUrls(item, 'item', out);

  const docIdx = buildDocIndex(item);
  const dm = (item.document || {}).documentMap || {};

  // For each image URL, resolve the document it came from via the JSON path.
  const rows = out.map((o) => {
    const m = o.path.match(/documentMap\.([^.]+)\./);
    let section = '';
    if (m) {
      section = docIdx[m[1]] || `documentMap.${m[1]}`;
    } else {
      // top-level / widget-level field
      section = o.path.replace(/^item\./, '').replace(/\[\d+\]/g, '[]');
    }
    const sizeM = o.path.match(/documentMap\.([^.]+)\.blockMap\.([^.]+)/);
    return { section, url: o.url, path: o.path, inDoc: !!sizeM };
  });

  return { name: item.name, itemId, rows, docIdx };
}

module.exports = { inventory };

if (require.main === module) {
  const ids = process.argv.slice(2);
  for (const id of ids) {
    const r = inventory(id);
    console.log(`\n######## ${id} ${r.name} — 图片 URL ${r.rows.length} 个`);
    const bySection = {};
    for (const row of r.rows) (bySection[row.section] = bySection[row.section] || []).push(row.url);
    for (const s of Object.keys(bySection)) {
      console.log(`  [${s}] ×${bySection[s].length}`);
      bySection[s].slice(0, 3).forEach((u) => console.log('      ' + u.slice(0, 130)));
    }
  }
}
