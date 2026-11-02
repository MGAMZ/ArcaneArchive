"""把 fz.wiki 接口原样的 JSON 展开成纯文本。

语料包里的 `*-raw/` 是接口返回原样，`*-text/` 是展开结果。展开规则按页面形态分七种：
PRTS 记录用 `flatten_prts`，任务、干员与活动页用 `flatten_story`，环带纪略与公告复用
`flatten_prts`，物品、装备、武器、蚀刻章各有一套只取文字字段的展开器，塔卫研报词典按
词条输出。这些规则都只读 `revision.contentJson`，接口的 `text` 字段对它们为空，不能直接用。
影片页不在这里展开，字幕要另下，用 `fetch_fz.py --rebuild-text`。

```bash
python3 tools/extract_fz.py prts-raw prts-text
python3 tools/extract_fz.py story-raw story-text
python3 tools/extract_fz.py item-raw item-text
```

两个参数都相对 `tmp/fzwiki/`，也可以给绝对路径。
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def flatten_prts(node, out):
    """PRTS 记录：正文在 wikiCardItem 的 segments 里，表格按行拼接。"""
    if isinstance(node, list):
        for n in node:
            flatten_prts(n, out)
        return
    if not isinstance(node, dict):
        return
    t = node.get('type')
    if t == 'text':
        out.append(node.get('text', ''))
        return
    if t == 'wikiCardItem':
        data = (node.get('attrs') or {}).get('data') or {}
        title = data.get('title') or data.get('name')
        if title:
            out.append('\n### ' + str(title) + '\n')
        for seg in data.get('segments') or []:
            if isinstance(seg, dict) and seg.get('type') == 'text':
                out.append(seg.get('text', '') + '\n')
            elif isinstance(seg, str):
                out.append(seg + '\n')
        return
    if t == 'heading':
        lvl = (node.get('attrs') or {}).get('level', 2)
        out.append('\n' + '#' * min(int(lvl) + 1, 6) + ' ')
    if t in ('paragraph', 'heading'):
        flatten_prts(node.get('content') or [], out)
        out.append('\n')
        return
    flatten_prts(node.get('content') or [], out)
    if t == 'tableRow':
        out.append('\n')
    elif t == 'tableCell':
        out.append(' | ')


def text_of(node):
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return ''.join(text_of(n) for n in node)
    if not isinstance(node, dict):
        return ''
    if node.get('type') == 'text':
        return node.get('text', '')
    return text_of(node.get('content') or [])


def emit_segments(segs, out):
    for s in segs or []:
        if isinstance(s, str):
            out.append(s + '\n')
            continue
        if not isinstance(s, dict):
            continue
        t = s.get('type')
        if t == 'text':
            out.append(s.get('text', '') + '\n')
        elif t == 'line':
            out.append(f"{s.get('actor', '')}：{s.get('text', '')}\n")
        elif t == 'bubble':
            for ln in s.get('lines') or []:
                out.append(f"{ln.get('actor', '')}：{ln.get('text', '')}\n")
        elif t == 'choice':
            opts = ' / '.join(o.get('text', '') for o in s.get('options') or [])
            out.append(f"【选项】{opts}\n")
        elif t == 'summary':
            out.append(f"\n【梗概】{s.get('text', '')}\n")
        elif t == 'notice':
            out.append(f"【编者注】{s.get('text', '')}\n")
        elif t == 'image':
            continue
        elif t:
            for k in ('title', 'text', 'name', 'desc'):
                if s.get(k):
                    out.append(str(s[k]) + '\n')
                    break


def emit_quest_info(a, out):
    out.append(f"\n【任务】{a.get('name', '')}　地区：{a.get('region', '')}　类型：{a.get('typeLabel', '')}\n")
    if a.get('description'):
        out.append(f"【任务描述】{a['description']}\n")


def emit_quest_flow(flow, out):
    """任务流程模板只有步骤与目标，没有对白；目标文字是这类页面唯一的正文。"""
    for branch in (flow or {}).get('timeline') or []:
        for b in branch.get('branches') or []:
            label = b.get('label') or ''
            for beat in b.get('beats') or []:
                obj = beat.get('objective') or ''
                if not obj:
                    continue
                tag = '【目标·可选】' if beat.get('optional') else '【目标】'
                prefix = f'{label} ' if label and len(branch.get('branches') or []) > 1 else ''
                out.append(f"{tag}{prefix}{obj}\n")


def flatten_story(node, out):
    """任务、干员与活动页：对白在回忆卡的 segments 里，任务卡另有描述与目标。"""
    if isinstance(node, list):
        for n in node:
            flatten_story(n, out)
        return
    if not isinstance(node, dict):
        return
    t = node.get('type')
    if t == 'endfieldCardQuestInfo':
        emit_quest_info(node.get('attrs') or {}, out)
        return
    if t == 'wikiCardItem':
        a = node.get('attrs') or {}
        d = a.get('data') or {}
        if d.get('segments'):
            if d.get('title'):
                out.append(f"\n### {d['title']}\n")
            emit_segments(d.get('segments'), out)
        elif d.get('body'):
            if d.get('title'):
                out.append(f"\n### {d['title']}\n")
            out.append(str(d['body']) + '\n')
        elif d.get('text'):
            if d.get('title'):
                out.append(f"\n### {d['title']}\n")
            out.append(str(d['text']) + '\n')
        return
    if t == 'wikiTemplateInstance':
        a = node.get('attrs') or {}
        if a.get('templateName') == '任务流程':
            emit_quest_info(a.get('info') or {}, out)
            emit_quest_flow(a.get('flow') or {}, out)
            return
        entries = (a.get('entries') or {}).get('entries') or []
        for e in entries:
            nm = e.get('name') or e.get('title') or ''
            if nm:
                out.append(f"\n### {nm}\n")
            if e.get('subtitle'):
                out.append(str(e['subtitle']) + '\n')
            emit_segments(e.get('segments'), out)
        return
    if t == 'heading':
        out.append('\n## ' + text_of(node.get('content') or []) + '\n')
        return
    if t == 'paragraph':
        s = text_of(node.get('content') or []).strip()
        if s and not s.startswith('Category:'):
            out.append(s + '\n')
        return
    flatten_story(node.get('content') or [], out)


def _join(*parts):
    return ''.join(f'【{k}】{v}\n' for k, v in parts if v)


def flatten_item(node, out):
    """物品页：名称、用途与一行记述在 endfieldCardItemEntryHero 里，其余是获取与合成表，不收。
    分类页只有 wikiIndexTable，展开成子条目清单。"""
    if isinstance(node, list):
        for n in node:
            flatten_item(n, out)
        return
    if not isinstance(node, dict):
        return
    t = node.get('type')
    a = node.get('attrs') or {}
    if t == 'endfieldCardItemEntryHero':
        out.append(_join(('物品', a.get('name')), ('分组', a.get('groupName')),
                         ('用途', a.get('desc')), ('记述', a.get('decoDesc'))))
        return
    if t == 'wikiTemplateInstance' and isinstance(a.get('hero'), dict):
        h = a['hero']
        out.append(_join(('物品', h.get('name')), ('分组', h.get('groupName')),
                         ('用途', h.get('desc')), ('记述', h.get('decoDesc'))))
        return
    if t == 'wikiIndexTable':
        entries = a.get('entries') or []
        out.append(f'【分类索引】{len(entries)} 条\n')
        for e in entries:
            out.append(f"- {e.get('name', '')}\n")
        return
    if t == 'paragraph':
        s = text_of(node.get('content') or []).strip()
        if s and not s.startswith('Category:'):
            out.append(s + '\n')
        return
    if t == 'heading':
        out.append('\n## ' + text_of(node.get('content') or []) + '\n')
        return
    flatten_item(node.get('content') or [], out)


def flatten_equip(node, out):
    """装备页：只取简介与 flavor，属性、材料与套组效果是数值表。"""
    if isinstance(node, list):
        for n in node:
            flatten_equip(n, out)
        return
    if not isinstance(node, dict):
        return
    t = node.get('type')
    a = node.get('attrs') or {}
    if t == 'endfieldCardEquipmentHero':
        out.append(_join(('装备', a.get('name')), ('部位', a.get('slotType')),
                         ('套组', a.get('suitName')), ('简介', a.get('description')),
                         ('记述', a.get('flavor'))))
        return
    if t == 'paragraph':
        s = text_of(node.get('content') or []).strip()
        if s and not s.startswith('Category:'):
            out.append(s + '\n')
        return
    flatten_equip(node.get('content') or [], out)


def flatten_weapon(node, out):
    """武器页：只取简介、flavor 与背景长文，属性与技能数值表不收。"""
    if isinstance(node, list):
        for n in node:
            flatten_weapon(n, out)
        return
    if not isinstance(node, dict):
        return
    t = node.get('type')
    a = node.get('attrs') or {}
    if t == 'endfieldCardWeaponHero':
        out.append(_join(('武器', a.get('name')), ('类型', a.get('weaponType')),
                         ('简介', a.get('description')), ('记述', a.get('flavor'))))
        return
    if t == 'endfieldCardWeaponBackground':
        if a.get('body'):
            out.append('\n## 背景\n' + str(a['body']) + '\n')
        return
    if t == 'paragraph':
        s = text_of(node.get('content') or []).strip()
        if s and not s.startswith('Category:'):
            out.append(s + '\n')
        return
    if t == 'heading':
        out.append('\n## ' + text_of(node.get('content') or []) + '\n')
        return
    flatten_weapon(node.get('content') or [], out)


def flatten_medal(node, out):
    """蚀刻章页：说明与达成条件在 endfieldCardAchvEntry 及其 wikiCardItem 条件里。"""
    if isinstance(node, list):
        for n in node:
            flatten_medal(n, out)
        return
    if not isinstance(node, dict):
        return
    t = node.get('type')
    a = node.get('attrs') or {}
    if t == 'endfieldCardAchvEntry':
        out.append(_join(('蚀刻章', a.get('name')), ('类别', a.get('categoryName')),
                         ('组别', a.get('groupName')), ('说明', a.get('desc'))))
        flatten_medal(node.get('content') or [], out)
        return
    if t == 'wikiCardItem':
        d = (a.get('data') or {})
        for c in d.get('conditions') or []:
            out.append(f"【条件】{c.get('desc', '')}\n")
        if d.get('completeDesc'):
            out.append(f"【达成】{d['completeDesc']}\n")
        return
    flatten_medal(node.get('content') or [], out)


def flatten_dict(node, out):
    """塔卫研报的词典页：每个词条一行标题加一段释义。"""
    if isinstance(node, list):
        for n in node:
            flatten_dict(n, out)
        return
    if not isinstance(node, dict):
        return
    t = node.get('type')
    a = node.get('attrs') or {}
    if t == 'endfieldCardGameLabelDictionary':
        flatten_dict(node.get('content') or [], out)
        return
    if t == 'wikiCardItem':
        d = a.get('data') or {}
        label = d.get('label') or d.get('name') or d.get('key') or ''
        if label:
            out.append(f"\n### {label}\n")
        cat = d.get('category') or ''
        if cat:
            out.append(f"【分类】{cat}\n")
        if d.get('description'):
            out.append(str(d['description']) + '\n')
        return
    if t == 'paragraph':
        s = text_of(node.get('content') or []).strip()
        if s and not s.startswith('Category:'):
            out.append(s + '\n')
        return
    if t == 'heading':
        out.append('\n## ' + text_of(node.get('content') or []) + '\n')
        return
    flatten_dict(node.get('content') or [], out)


EXPANDERS = {
    'prts': flatten_prts,
    'story': flatten_story,
    'prose': flatten_prts,
    'item': flatten_item,
    'equip': flatten_equip,
    'weapon': flatten_weapon,
    'medal': flatten_medal,
    'dict': flatten_dict,
}


def expand(kind, content_json):
    out = []
    EXPANDERS[kind](content_json, out)
    text = ''.join(out)
    text = re.sub(r'[ \t]+\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text


KIND_BY_DIR = {
    'prts': 'prts',
    'story': 'story',
    'chronicle': 'prose',
    'news': 'prose',
    'item': 'item',
    'equip': 'equip',
    'weapon': 'weapon',
    'medal': 'medal',
    'report': 'dict',
    'video': 'video',
}


def kind_of(raw_dir):
    name = pathlib.Path(raw_dir).name
    return KIND_BY_DIR.get(name.split('-')[0])


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src = pathlib.Path(sys.argv[1])
    dst = pathlib.Path(sys.argv[2])
    src = src if src.is_absolute() else ROOT / 'tmp/fzwiki' / src
    dst = dst if dst.is_absolute() else ROOT / 'tmp/fzwiki' / dst
    kind = kind_of(src)
    if kind == 'video':
        raise SystemExit('影片页要用 fetch_fz.py --only video --rebuild-text，字幕不在 raw 里')
    if kind not in EXPANDERS:
        raise SystemExit(f'不知道 {src.name} 该用哪套展开规则')
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in sorted(src.glob('*.json')):
        data = json.loads(p.read_text(encoding='utf-8'))
        text = expand(kind, data['revision']['contentJson'])
        (dst / (p.stem + '.txt')).write_text(text, encoding='utf-8')
        n += 1
    print('expanded', n, src.name, '->', dst.name)


if __name__ == '__main__':
    main()
