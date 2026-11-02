"""从四层语料压缩包生成合一出处索引（森空岛 + fz 剧情 + fz Baker + fz 补抓）"""

import tarfile
from urllib.parse import quote
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKLAND = ROOT / 'corpus/skland-endfield-wiki_2026-10-17.tar.gz'
FZ = ROOT / 'corpus/fzwiki-2026-10-27.tar.gz'
BAKER = ROOT / 'corpus/fzwiki-baker-2026-11-02.tar.gz'
SUPPLEMENT = ROOT / 'corpus/fzwiki-supplement-2026-11-02.tar.gz'
OUT = ROOT / 'data/source_index.tsv'

# 补抓包按命名空间分目录，只认 `*-text/`，免得同一页因 raw 与 text 各占一行
SUPPLEMENT_DIRS = ('chronicle-text/', 'video-text/', 'item-text/', 'equip-text/',
                   'weapon-text/', 'medal-text/', 'report-text/', 'news-text/')

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


def fz_pages(tar, dirs):
    """枚举 `*-text/` 成员，返回 (页面路径, 标题, 分类, 包内路径) 四元组。"""
    for m in tar.getmembers():
        if not m.name.endswith('.txt') or not m.name.startswith(dirs):
            continue
        rel = m.name.split('/', 1)[1][:-len('.txt')].replace('__', '/')
        parts = rel.split('/')
        if len(parts) < 2:
            continue
        category = parts[1] if parts[0] == 'PRTS记录' else parts[0]
        yield rel, parts[-1], category, m.name


fz_rows = []
with tarfile.open(FZ) as tar:
    for rel, title, category, member in fz_pages(tar, ('prts-text/', 'story-text/')):
        fz_rows.append(('fz', rel, title, category, FZ.name, member,
                        'https://www.fz.wiki/wiki/' + quote(rel)))

baker_rows = []
with tarfile.open(BAKER) as tar:
    for rel, title, _, member in fz_pages(tar, ('baker-text/',)):
        baker_rows.append(('fz', rel, title, 'Baker', BAKER.name, member,
                           'https://www.fz.wiki/wiki/' + quote(rel)))

supplement_rows = []
with tarfile.open(SUPPLEMENT) as tar:
    for rel, title, category, member in fz_pages(tar, SUPPLEMENT_DIRS):
        supplement_rows.append(('fz', rel, title, category, SUPPLEMENT.name, member,
                                'https://www.fz.wiki/wiki/' + quote(rel)))

rows.sort(key=lambda r: int(r[1]))
for group in (fz_rows, baker_rows, supplement_rows):
    group.sort(key=lambda r: r[1])
    rows.extend(group)

lines = [
    '# 四层语料合一出处索引（森空岛 + fz 剧情 + fz Baker + fz 补抓；source / key / title / category / corpus / member / url）',
    f'# skland 采集于 2026-10-17，{sum(1 for r in rows if r[0] == "skland")} 条',
    f'# fz.wiki 剧情页采集于 2026-10-27，{len(fz_rows)} 页',
    f'# fz.wiki Baker 页采集于 2026-11-02，{len(baker_rows)} 页',
    f'# fz.wiki 补抓页采集于 2026-11-02，{len(supplement_rows)} 页',
    '# key 即 data/jue_timeline.json 里证据的 id。member 是压缩包内的路径',
    'source\tkey\ttitle\tcategory\tcorpus\tmember\turl',
]
lines += ['\t'.join(r) for r in rows]
OUT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('rows', len(rows), 'written to', OUT.relative_to(ROOT))
