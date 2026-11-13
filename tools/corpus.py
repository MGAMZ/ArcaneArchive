"""四层语料压缩包的路径、采集日与页面遍历"""

import json
import pathlib
import re
import tarfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKLAND = ROOT / 'corpus/skland-endfield-wiki_2026-11-12.tar.gz'
FZ = ROOT / 'corpus/fzwiki-2026-11-12.tar.gz'
BAKER = ROOT / 'corpus/fzwiki-baker-2026-11-12.tar.gz'
SUPPLEMENT = ROOT / 'corpus/fzwiki-supplement-2026-11-12.tar.gz'


def snapshot(path):
    """压缩包名里的采集日"""
    return re.search(r'\d{4}-\d{2}-\d{2}', path.name).group(0)


def members(tar, prefixes):
    """枚举 `*-text/` 成员，返回 (页面路径, 标题, 分类, TarInfo)"""
    for m in tar.getmembers():
        if not m.name.endswith('.txt') or not m.name.startswith(prefixes):
            continue
        rel = m.name.split('/', 1)[1][:-len('.txt')].replace('__', '/')
        parts = rel.split('/')
        if len(parts) < 2:
            continue
        category = parts[1] if parts[0] == 'PRTS记录' else parts[0]
        yield rel, parts[-1], category, m


def text_dirs(tar):
    """压缩包顶层的 `*-text/` 目录"""
    return tuple(sorted({m.name.split('/', 1)[0] + '/' for m in tar.getmembers()
                         if m.name.split('/', 1)[0].endswith('-text')}))


def load_items(tar):
    """森空岛包里的三份条目目录接口，展开成条目清单"""
    items = []
    for main_id in ('1', '2', '3'):
        payload = json.load(tar.extractfile(
            f'data/web_v1_wiki_item_catalog_typeMainId_{main_id}.json'))
        for group in payload['data']['catalog']:
            for sub in group.get('typeSub') or []:
                for item in sub.get('items') or []:
                    items.append({
                        'mainTypeId': main_id,
                        'subTypeId': sub['id'],
                        'subName': sub['name'],
                        'itemId': item['itemId'],
                        'name': item['name'],
                        'lang': item['lang'],
                    })
    return items