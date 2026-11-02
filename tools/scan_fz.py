"""在 fz 三层语料里检索「诀」，产出 evidence/fz_mentions.txt

`analyze.js` 与 `evidence.js` 只读森空岛那一层，fz 的剧情、Baker、补抓三层
一直没有机检。本脚本补上这一段，分三节：

A 点名命中，逐页列出命中的行与所在标题；
B 误命中，「诀」只出现在诀窍、秘诀一类词里；
C 未提名候选，正文没有「诀」字，但落在只跟武陵这条线有关的少数专名上。

C 节是给人看的候选表，不是结论：命中一个专名不等于讲了诀的事。只按地名取词
会把整批武陵任务页都拖进来，所以门槛设成「至少命中一个只属于她这条线的专名」，
武陵、息壤、天师桩这类通用词只用来标注。
"""

import pathlib
import re
import sys
import tarfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
FZ = ROOT / 'corpus/fzwiki-2026-10-27.tar.gz'
BAKER = ROOT / 'corpus/fzwiki-baker-2026-11-02.tar.gz'
SUPPLEMENT = ROOT / 'corpus/fzwiki-supplement-2026-11-02.tar.gz'
OUT = ROOT / 'evidence/fz_mentions.txt'

NAME_TERMS = ('诀', '李织烟', '织烟')
FP_WORDS = ('诀窍', '秘诀', '口诀', '要诀', '妙诀')
LORE_TERMS = ('应龙', '谈剑堂', '噪雷', '息壤', '天师桩', '蚀影', '临渊',
              '武陵', '北部禁区', '归途', '陈千语', '庄方宜', '帝江号')
# 只属于诀这条线的专名。C 节的门槛：至少命中其一，否则武陵的整批任务页都会进来。
# 蚀影、应龙关几乎页页都有，取词时剔除，否则候选表会退回成地名索引。
NARROW_TERMS = ('谈剑堂', '噪雷', '应龙特勤队', '应龙桩', '临渊')
# 不点名的转称。C 节里同时出现这些词的页，才比较可能是在说她。
PROXY_TERMS = ('队长', '应龙队员', '老师')

LAYERS = (
    (FZ, ('prts-text/', 'story-text/'), 'fz 剧情'),
    (BAKER, ('baker-text/',), 'fz Baker'),
    (SUPPLEMENT, ('chronicle-text/', 'video-text/', 'item-text/', 'equip-text/',
                  'weapon-text/', 'medal-text/', 'report-text/', 'news-text/'), 'fz 补抓'),
)

HEADING = re.compile(r'^(#+ |【[^】]{1,20}】)')


def pages(tar_path, prefixes):
    """枚举 `*-text/` 成员，返回 (页面路径, 分类, 正文)。"""
    with tarfile.open(tar_path) as tar:
        for m in tar.getmembers():
            if not m.name.startswith(prefixes) or not m.name.endswith('.txt'):
                continue
            rel = m.name.split('/', 1)[1][:-len('.txt')].replace('__', '/')
            parts = rel.split('/')
            if len(parts) < 2:
                continue
            category = parts[1] if parts[0] == 'PRTS记录' else parts[0]
            body = tar.extractfile(m).read().decode('utf-8')
            yield rel, category, body


def name_hits(text):
    """返回 (词形集合, 命中行号)，「诀」只算非「诀窍」类的出现。"""
    terms = set()
    lines = []
    rest = text
    for w in FP_WORDS:
        rest = rest.replace(w, '')
    if '诀' in rest:
        terms.add('诀')
    if '李织烟' in text:
        terms.add('李织烟')
    if '织烟' in text:
        terms.add('织烟')
    if not terms:
        return terms, lines
    for i, line in enumerate(text.splitlines()):
        s = line
        for w in FP_WORDS:
            s = s.replace(w, '')
        if any(t in s for t in terms):
            lines.append(i)
    return terms, lines


def heading_of(lines, idx):
    for i in range(idx, -1, -1):
        if HEADING.match(lines[i].strip()):
            return lines[i].strip()
    return '(页首)'


def main():
    stats = '--stats' in sys.argv
    named, false_pos, candidates = [], [], []
    for tar_path, prefixes, layer in LAYERS:
        for rel, category, body in pages(tar_path, prefixes):
            terms, hits = name_hits(body)
            if terms:
                named.append((layer, category, rel, body, sorted(terms), hits))
                continue
            if '诀' in body:
                false_pos.append((layer, category, rel))
            found = [w for w in LORE_TERMS if w in body]
            narrow = [w for w in NARROW_TERMS if w in body]
            if narrow:
                candidates.append((layer, category, rel, narrow, found, body))

    if stats:
        print('named', len(named))
        print('false_pos', len(false_pos))
        print('candidates', len(candidates))
        for _, _, rel, narrow, found, _ in candidates[:15]:
            print(' ', rel, '|', '/'.join(narrow), '|', '/'.join(found))
        return

    out = ['# fz 三层语料中「诀 / 李织烟 / 织烟」的命中与候选',
           '# 语料：fz.wiki 剧情 1293 页、Baker 242 页、补抓 2143 页',
           '# 由 tools/scan_fz.py 生成；A 节是点名命中，C 节是无名字的候选，需人工判读',
           '']

    out.append(f'## A. 点名命中（{len(named)} 页）')
    by_layer = {}
    for row in named:
        by_layer.setdefault(row[0], []).append(row)
    for layer, rows in by_layer.items():
        out.append('')
        out.append(f'### {layer}（{len(rows)} 页）')
        for _, category, rel, body, terms, hits in rows:
            lines = body.splitlines()
            out.append('')
            out.append(f'  [{category}] {rel}  (命中 {len(hits)}, 词形 {"+".join(terms)})')
            seen = set()
            for i in hits:
                h = heading_of(lines, i)
                key = (h, lines[i])
                if key in seen:
                    continue
                seen.add(key)
                out.append(f'    <{h}>')
                out.append('    ' + lines[i].strip())

    out.append('')
    out.append(f'## B. 误命中（{len(false_pos)} 页，「诀」只出现在诀窍、秘诀一类词里）')
    for layer, category, rel in false_pos:
        out.append(f'  - [{category}] {rel}')

    out.append('')
    out.append(f'## C. 未提名候选（{len(candidates)} 页）')
    out.append('# 正文没有「诀」字，但命中只属于她这条线的专名。相关与否要读正文判断。')
    out.append('# 后缀「转称」指同页还出现队长、应龙队员、老师这类不点名的称呼，这类页更可能是在说她。')
    candidates.sort(key=lambda c: (not any(w in c[5] for w in PROXY_TERMS), -len(c[3]), c[2]))
    for layer, category, rel, narrow, found, body in candidates:
        proxy = [w for w in PROXY_TERMS if w in body]
        mark = f'   ← 转称：{"/".join(proxy)}' if proxy else ''
        out.append(f'  - [{category}] {rel}  ({"/".join(narrow)} | {"/".join(found)}){mark}')

    OUT.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print('wrote', OUT.relative_to(ROOT), len(out), 'lines')
    print('named', len(named), '| false_pos', len(false_pos), '| candidates', len(candidates))


if __name__ == '__main__':
    main()
