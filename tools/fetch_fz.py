"""按命名空间前缀抓取 fz.wiki 页面，落接口原样 JSON 与展开文本。

列表接口 `GET /api/v1/articles?prefix=<前缀>&size=200&page=N` 给出该前缀下的全部标题与
`total`；逐页再走 `by-title` 取 `currentRevisionId`，最后走 `revisions/{id}` 取正文。列表接口
的条目不含 `currentRevisionId`，所以每页两次请求，不能省。

```bash
python3 tools/fetch_fz.py                 # 抓默认清单里的全部命名空间
python3 tools/fetch_fz.py --only video     # 只抓影片
python3 tools/fetch_fz.py --dry-run        # 只列标题与条数
```

输出写到 `tmp/fzwiki/<目录>-raw/`（原样 JSON）与 `<目录>-text/`（展开文本），影片另存
`video-sub/`（接口给的简体中文 .ass 字幕）。已存在的页会跳过，中断后可直接重跑。
"""
import argparse
import json
import pathlib
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import requests

import extract_fz

BASE = 'https://api.fz.wiki/api/v1'
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'tmp/fzwiki'

# (前缀, 目录名, 展开规则)。目录名写内容类别，展开规则见 extract_fz 与下文 expand_video。
TARGETS = [
    ('环带纪略/', 'chronicle', 'prose'),
    ('影片/剧情/', 'video', 'video'),
    ('物品/', 'item', 'item'),
    ('装备/', 'equip', 'equip'),
    ('武器/', 'weapon', 'weapon'),
    ('蚀刻章/', 'medal', 'medal'),
    ('塔卫研报/名词释义', 'report', 'dict'),
    ('塔卫研报/富文本词典', 'report', 'dict'),
    ('塔卫研报/物品词典', 'report', 'dict'),
    ('塔卫研报/装备词典', 'report', 'dict'),
    ('塔卫研报/武器词典', 'report', 'dict'),
    ('塔卫研报/敌人词典', 'report', 'dict'),
    ('游戏动态/', 'news', 'prose'),
]

S = requests.Session()
S.headers.update({'User-Agent': 'ArcaneArchive-research/1.0 (lore archival)',
                  'Accept': 'application/json'})


def get_json(url, tries=4):
    for i in range(tries):
        try:
            r = S.get(url, timeout=40)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
        except Exception:
            pass
        time.sleep(1.0 * (i + 1))
    return None


def get_bytes(url, tries=4):
    for i in range(tries):
        try:
            r = S.get(url, timeout=60)
            if r.status_code == 200:
                return r.content
            if r.status_code == 404:
                return None
        except Exception:
            pass
        time.sleep(1.0 * (i + 1))
    return None


def enum_titles(prefix):
    out, page = [], 1
    while True:
        d = get_json(f'{BASE}/articles?' + urllib.parse.urlencode(
            {'prefix': prefix, 'size': 200, 'page': page}))
        if not d:
            break
        out += [a['title'] for a in d.get('articles') or []]
        if len(out) >= d.get('total', 0) or not d.get('articles'):
            break
        page += 1
    return sorted(set(out))


def slug(title):
    return title.replace('/', '__')


def variant_subtitles(attrs):
    """一页影片的简体中文字幕，按变体（female / male / neutral）分组。"""
    picked = []
    for name, v in (attrs.get('variants') or {}).items():
        tr = [t for t in v.get('subtitleTracks') or [] if t.get('language') == 'CN']
        if tr:
            picked.append((name, round(v.get('durationSeconds') or 0), tr[0]['src']))
    return picked


def ass_lines(text):
    """ASS 的 Events 行，返回 (时刻, 文本)。标签、强制换行与矢量绘制事件在这里清掉。

    BigLogo 样式里有大量 `m … l …` 绘图事件（台标动画），去掉样式标签后只剩一串坐标，
    不是字幕，按绘制命令的开头识别并丢弃。
    """
    lines = []
    for line in text.splitlines():
        if not line.startswith('Dialogue:'):
            continue
        fields = line[len('Dialogue:'):].split(',', 9)
        if len(fields) < 10:
            continue
        stamp, body = fields[1].strip(), fields[9]
        body = re.sub(r'\{[^}]*\}', '', body).replace('\\N', ' ').replace('\\n', ' ')
        body = re.sub(r'\s+', ' ', body).strip()
        if not body or re.match(r'^[mnlbscp] -?\d', body):
            continue
        lines.append((stamp, body))
    return lines


def expand_video(attrs, title, sub_dir):
    """影片页：正文就是字幕对白。同一句连续重复多次的只留一次。"""
    out = [f'# {title}\n']
    for name, dur, src in variant_subtitles(attrs):
        path = sub_dir / f'{slug(title)}__{name}.ass'
        body = path.read_bytes() if path.exists() else get_bytes(src)
        if body is None:
            out.append(f'\n## 简体中文（{name}，字幕缺失）\n')
            continue
        if not path.exists():
            sub_dir.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        lines = ass_lines(body.decode('utf-8-sig'))
        out.append(f'\n## 简体中文（{name}，{dur} 秒，{len(lines)} 句）\n')
        last = None
        for stamp, text in lines:
            if text == last:
                continue
            last = text
            out.append(f'[{stamp}] {text}\n')
    return ''.join(out)


def fetch(title, kind, txt_dir, sub_dir):
    raw_dir = txt_dir.parent / (txt_dir.name.split('-')[0] + '-raw')
    raw_path = raw_dir / f'{slug(title)}.json'
    txt_path = txt_dir / f'{slug(title)}.txt'
    if raw_path.exists() and txt_path.exists():
        return title, 'skip'

    art = get_json(f'{BASE}/articles/by-title?' + urllib.parse.urlencode({'title': title}))
    if not art or 'article' not in art:
        return title, 'no-article'
    article = art['article']
    rev = get_json(f"{BASE}/revisions/{article['currentRevisionId']}")
    if not rev or 'revision' not in rev:
        return title, 'no-revision'
    revision = rev['revision']

    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps({'article': article, 'revision': revision}, ensure_ascii=False),
                        encoding='utf-8')
    write_text(title, kind, revision, txt_dir, sub_dir)
    return title, 'ok'


def write_text(title, kind, revision, txt_dir, sub_dir):
    """展开结果直接落盘，末尾不补换行，与 `extract_fz.py` 单独重跑的结果一致。"""
    if kind == 'video':
        attrs = revision['contentJson']['content'][0].get('attrs') or {}
        text = expand_video(attrs, title, sub_dir)
    else:
        text = extract_fz.expand(kind, revision['contentJson'])
    txt_dir.mkdir(parents=True, exist_ok=True)
    (txt_dir / f'{slug(title)}.txt').write_text(text, encoding='utf-8')


def rebuild(name, kind):
    """离线重展开：只读 `<目录>-raw/` 里的 JSON 重写文本，影片复用已下载的字幕。"""
    txt_dir = OUT / f'{name}-text'
    sub_dir = OUT / 'video-sub'
    n = 0
    for p in sorted((OUT / f'{name}-raw').glob('*.json')):
        data = json.loads(p.read_text(encoding='utf-8'))
        write_text(data['article']['title'], kind, data['revision'], txt_dir, sub_dir)
        n += 1
    print('rebuilt', n, name, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', action='append', default=[],
                        help='只跑这些目录名，可重复；默认全部')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--rebuild-text', action='store_true',
                        help='不联网，只从已有的 raw JSON 重写文本')
    parser.add_argument('--workers', type=int, default=8)
    args = parser.parse_args()

    targets = [t for t in TARGETS if not args.only or t[1] in args.only]
    if args.rebuild_text:
        seen = {}
        for _, name, kind in targets:
            seen[name] = kind
        for name, kind in seen.items():
            rebuild(name, kind)
        return

    jobs = []
    for prefix, name, kind in targets:
        titles = enum_titles(prefix)
        print(f'{prefix} -> {name}: {len(titles)} 页', flush=True)
        jobs += [(t, kind, OUT / f'{name}-text', OUT / 'video-sub') for t in titles]
        if args.dry_run:
            for t in titles:
                print('  ', t)
    print('total', len(jobs), flush=True)
    if args.dry_run:
        return

    done = 0
    tally = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for title, status in ex.map(lambda j: fetch(*j), jobs):
            done += 1
            tally[status] = tally.get(status, 0) + 1
            if status in ('no-article', 'no-revision'):
                print(status.upper(), title, flush=True)
            elif done % 200 == 0:
                print('progress', done, flush=True)
    print('done', done, tally, flush=True)


if __name__ == '__main__':
    main()
