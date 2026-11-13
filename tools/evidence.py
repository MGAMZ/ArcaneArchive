"""把森空岛的检索命中整理成 evidence/evidence_mentions.txt"""

import tarfile

import analyze
import corpus

OUT = corpus.ROOT / 'evidence/evidence_mentions.txt'

# 只留带叙事的类目。装备的命中是板块标题，百科速览是数值表，干员攻略是玩家写的。
GAMEPLAY_ONLY = {'装备', '百科速览', '干员攻略'}


def main():
    with tarfile.open(corpus.SKLAND) as tar:
        items = corpus.load_items(tar)
        meta = {i['itemId']: i for i in items}
        found = analyze.analyze(tar, items)

        story = [r for r in found if r['category'] not in GAMEPLAY_ONLY]
        gameplay = [r for r in found if r['category'] in GAMEPLAY_ONLY]

        out = ['# 全语料中「诀 / 李织烟 / 织烟」命中汇总（已排除技能名与常用词误命中）',
               f'# 语料：wiki.skland.com/endfield 全 {len(items)} 条',
               '']
        out.append(f'## A. 叙事类命中（{len(story)} 个条目）')
        for r in story:
            out.append('')
            out.append(f"### [{r['category']}] {r['name']}  (itemId={r['itemId']}, "
                       f"命中 {r['totalHits']}, 词形 {'+'.join(r['terms'])})")
            seen = set()
            for line in r['lines']:
                if line['text'] in seen:
                    continue
                seen.add(line['text'])
                out.append(f"  <{line['section']}>")
                out.append('  ' + line['text'])

        out.append('')
        out.append(f'## B. 仅结构/数值/攻略类命中（不构成剧情证据，{len(gameplay)} 个条目）')
        for r in gameplay:
            first = r['lines'][0]['section'] if r['lines'] else ''
            out.append(f"  - [{r['category']}] {r['name']} "
                       f"(itemId={r['itemId']}, {r['totalHits']}) → {first}")

        out.append('')
        out.append('## C. 词条交叉引用（entry:1675）——正文未出现「诀」字但链接到她的条目')
        named = {r['itemId'] for r in found}
        for m in tar.getmembers():
            if not (m.name.startswith('txt/') and m.name.endswith('.txt')):
                continue
            item_id = m.name[len('txt/'):-len('.txt')]
            if item_id == '1675':
                continue
            if 'entry:1675' not in tar.extractfile(m).read().decode('utf-8'):
                continue
            item = meta.get(item_id, {})
            mark = '' if item_id in named else '   ← 仅链接、正文无「诀」字'
            out.append(f"  - [{item.get('subName', '?')}] {item.get('name', '?')} "
                       f"(itemId={item_id}){mark}")

    OUT.write_text('\n'.join(out), encoding='utf-8')
    print('wrote', OUT.relative_to(corpus.ROOT), len(out), 'lines')
    print('story items:', len(story), '| gameplay-only:', len(gameplay))


if __name__ == '__main__':
    main()