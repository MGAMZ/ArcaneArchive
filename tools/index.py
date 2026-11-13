"""从四层语料压缩包生成合一出处索引（森空岛 + fz 剧情 + fz Baker + fz 补抓）"""

import tarfile
from urllib.parse import quote

import corpus


rows = []
with tarfile.open(corpus.SKLAND) as tar:
    by_id = {i['itemId']: i for i in corpus.load_items(tar)}
    members = [m.name for m in tar.getmembers()
               if m.name.startswith('txt/') and m.name.endswith('.txt')]

for name in members:
    item_id = name[len('txt/'):-len('.txt')]
    it = by_id[item_id]
    url = ('https://wiki.skland.com/endfield/detail'
           f'?mainTypeId={it["mainTypeId"]}&subTypeId={it["subTypeId"]}&gameEntryId={item_id}&header=0')
    rows.append(('skland', item_id, it['name'], it['subName'], corpus.SKLAND.name, name, url))

fz_rows = []
with tarfile.open(corpus.FZ) as tar:
    for rel, title, category, m in corpus.members(tar, ('prts-text/', 'story-text/')):
        fz_rows.append(('fz', rel, title, category, corpus.FZ.name, m.name,
                        'https://www.fz.wiki/wiki/' + quote(rel)))

baker_rows = []
with tarfile.open(corpus.BAKER) as tar:
    for rel, title, _, m in corpus.members(tar, ('baker-text/',)):
        baker_rows.append(('fz', rel, title, 'Baker', corpus.BAKER.name, m.name,
                           'https://www.fz.wiki/wiki/' + quote(rel)))

supplement_rows = []
with tarfile.open(corpus.SUPPLEMENT) as tar:
    for rel, title, category, m in corpus.members(tar, corpus.text_dirs(tar)):
        supplement_rows.append(('fz', rel, title, category, corpus.SUPPLEMENT.name, m.name,
                                'https://www.fz.wiki/wiki/' + quote(rel)))

rows.sort(key=lambda r: int(r[1]))
for group in (fz_rows, baker_rows, supplement_rows):
    group.sort(key=lambda r: r[1])
    rows.extend(group)

lines = [
    '# 四层语料合一出处索引（森空岛 + fz 剧情 + fz Baker + fz 补抓；source / key / title / category / corpus / member / url）',
    f'# skland 采集于 {corpus.snapshot(corpus.SKLAND)}，{sum(1 for r in rows if r[0] == "skland")} 条',
    f'# fz.wiki 剧情页采集于 {corpus.snapshot(corpus.FZ)}，{len(fz_rows)} 页',
    f'# fz.wiki Baker 页采集于 {corpus.snapshot(corpus.BAKER)}，{len(baker_rows)} 页',
    f'# fz.wiki 补抓页采集于 {corpus.snapshot(corpus.SUPPLEMENT)}，{len(supplement_rows)} 页',
    '# key 即 data/jue_timeline.json 里证据的 id。member 是压缩包内的路径',
    'source\tkey\ttitle\tcategory\tcorpus\tmember\turl',
]
lines += ['\t'.join(r) for r in rows]
corpus.ROOT.joinpath('data/source_index.tsv').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('rows', len(rows), 'written to data/source_index.tsv')