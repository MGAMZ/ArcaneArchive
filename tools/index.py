"""从两份语料压缩包生成合一出处索引"""

import tarfile
from urllib.parse import quote
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKLAND = ROOT / 'corpus/skland-endfield-wiki_2026-10-17.tar.gz'
FZ = ROOT / 'corpus/fzwiki-2026-10-27.tar.gz'
OUT = ROOT / 'data/source_index.tsv'

items = json.loads((ROOT / 'tools/items_all.json').read_text(encoding='utf-8'))
by_id = {i['itemId']: i for i in items}

rows = []
with tarfile.open(SKLAND) as tar:
    members = [m.name for m in tar.getmembers() if m.name.startswith('txt/') and m.name.endswith('.txt')]
for name in members:
    item_id = name[len('txt/'):-len('.txt')]
    it = by_id[item_id]
    url = ('https://wiki.skland.com/endfield/detail'
           f'?mainTypeId={it["mainTypeId"]}&subTypeId={it["subTypeId"]}&gameEntryId={item_id}&header=0')
    rows.append(('skland', item_id, it['name'], it['subName'], SKLAND.name, name, url))

fz_rows = []
with tarfile.open(FZ) as tar:
    for m in tar.getmembers():
        if not m.name.endswith('.txt') or not m.name.startswith(('prts-text/', 'story-text/')):
            continue
        rel = m.name.split('/', 1)[1][:-len('.txt')].replace('__', '/')
        parts = rel.split('/')
        if len(parts) < 2:
            continue
        category = parts[1] if parts[0] == 'PRTS记录' else parts[0]
        fz_rows.append(('fz', rel, parts[-1], category, FZ.name, m.name,
                        'https://www.fz.wiki/wiki/' + quote(rel)))

rows.sort(key=lambda r: int(r[1]))
fz_rows.sort(key=lambda r: r[1])
rows.extend(fz_rows)

lines = [
    '# 两层语料合一出处索引（source / key / title / category / corpus / member / url）',
    f'# skland 采集于 2026-10-17，{sum(1 for r in rows if r[0] == "skland")} 条',
    f'# fz.wiki 采集于 2026-10-27，{len(fz_rows)} 页',
    '# key 即 data/jue_timeline.json 里证据的 id。member 是压缩包内的路径',
    'source\tkey\ttitle\tcategory\tcorpus\tmember\turl',
]
lines += ['\t'.join(r) for r in rows]
OUT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('rows', len(rows), 'written to', OUT.relative_to(ROOT))
