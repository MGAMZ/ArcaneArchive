"""在森空岛语料里检索「诀 / 李织烟 / 织烟」，剔除技能名与常用词造成的误命中。

读 `corpus/` 里的森空岛包，不必解包。默认打印命中概况，整理成证据文件的是
`tools/evidence.py`。
"""

import json
import re
import tarfile
from bisect import bisect_right

import corpus

# 含「诀」但不指她的词，按全部语料里「诀」的每一处人工判定结果写。
FALSE_JUE = (
    '秘诀', '口诀', '诀窍', '诀别', '永诀', '长诀', '决诀', '诀要', '真诀', '妙诀', '歌诀', '丹诀',
    '惊霆诀', '霆诀',            # 庄方宜 战技「惊霆诀」
    '阵诀',                      # 她自己的 阵诀·智 / 阵诀·意
    '破晦诀明', '晦诀明', '晦诀',  # 终结技二段「破晦诀明」
    '剑诀',
)

TERMS = ('李织烟', '织烟')


def mask(text):
    """把误命中词替换成等长的空字符，保留字符偏移"""
    for w in FALSE_JUE:
        text = text.replace(w, '\x00' * len(w))
    return text


def find_hits(text):
    """返回 [(字符偏移, 词形)]，按偏移升序"""
    hits = [(m.start(), '李织烟') for m in re.finditer('李织烟', text)]
    hits += [(m.start(), '织烟') for m in re.finditer('织烟', text)
             if m.start() == 0 or text[m.start() - 1] != '李']
    hits += [(m.start(), '诀') for m in re.finditer('诀', mask(text))]
    hits.sort(key=lambda h: h[0])
    return hits


def section_of(lines, idx):
    """第 idx 行所属的章 / 板块 / tab"""
    chapter = widget = tab = ''
    for line in lines[:idx + 1]:
        if line.startswith('######## [章] '):
            chapter = line[len('######## [章] '):]
            widget = tab = ''
        elif line.startswith('#### [板块] '):
            widget = re.sub(r'\s*\(widget=.*$', '', line[len('#### [板块] '):])
            tab = ''
        elif line.strip().startswith('-- [tab] '):
            tab = line.strip()[len('-- [tab] '):]
    return ' › '.join(x for x in (chapter, widget, tab) if x)


def analyze(tar, items):
    """逐条检索，返回命中条目，按命中数从多到少"""
    meta = {i['itemId']: i for i in items}
    results = []
    for m in tar.getmembers():
        if not (m.name.startswith('txt/') and m.name.endswith('.txt')):
            continue
        item_id = m.name[len('txt/'):-len('.txt')]
        text = tar.extractfile(m).read().decode('utf-8')
        hits = find_hits(text)
        if not hits:
            continue
        lines = text.split('\n')
        starts = []
        acc = 0
        for line in lines:
            starts.append(acc)
            acc += len(line) + 1
        by_line = {}
        for offset, term in hits:
            by_line.setdefault(bisect_right(starts, offset) - 1, {}).setdefault(term, True)
        item = meta.get(item_id, {})
        results.append({
            'itemId': item_id,
            'name': item.get('name', '?'),
            'category': item.get('subName', '?'),
            'totalHits': len(hits),
            'terms': list(dict.fromkeys(term for _, term in hits)),
            'lines': [{'section': section_of(lines, li),
                       'terms': list(by_line[li]),
                       'text': lines[li].strip()} for li in sorted(by_line)],
        })
    results.sort(key=lambda r: -r['totalHits'])
    return results


def main():
    with tarfile.open(corpus.SKLAND) as tar:
        res = analyze(tar, corpus.load_items(tar))
    print('items with mentions:', len(res))
    by_cat = {}
    for r in res:
        by_cat[r['category']] = by_cat.get(r['category'], 0) + 1
    print('by category:', json.dumps(by_cat, ensure_ascii=False, indent=1))
    print('\n=== top items by hit count ===')
    for r in res[:45]:
        print(f"{r['totalHits']:>4} {r['itemId']:<6} {r['category']:<8} "
              f"{r['name']} | {'+'.join(r['terms'])}")


if __name__ == '__main__':
    main()