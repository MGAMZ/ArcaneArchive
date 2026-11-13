// 从森空岛语料包的 data/ 读出条目清单。
const fs = require('fs');
const path = require('path');
const { WORK } = require('./paths.js');

const DATA = path.join(WORK, 'data');

function load() {
  const items = [];
  for (const mainId of ['1', '2', '3']) {
    const p = path.join(DATA, `web_v1_wiki_item_catalog_typeMainId_${mainId}.json`);
    const payload = JSON.parse(fs.readFileSync(p, 'utf8'));
    for (const group of payload.data.catalog) {
      for (const sub of group.typeSub || []) {
        for (const item of sub.items || []) {
          items.push({
            mainTypeId: mainId,
            subTypeId: sub.id,
            subName: sub.name,
            itemId: item.itemId,
            name: item.name,
            lang: item.lang,
            status: item.status,
          });
        }
      }
    }
  }
  return items;
}

module.exports = { load, WORK, DATA };