"""抓取 fz.wiki 的 Baker 命名空间，保存接口原样 JSON 与按消息顺序展开的文本。

标题清单固化在 `tools/baker_titles.txt`，共 242 条；`tmp/fz_sitemap.xml` 只作
后备。Baker 页是游戏内通讯软件的对话聚合，消息节点用 kind: msg / choices /
image 等，和任务页的 type: line 不是一套结构，所以单独走一个展开器。

文本格式：
  # Baker/事件/应龙特勤队
  【话题】...
  [庄方宜] 诀只用三年时间就从候补成为了队长，这么年轻，极不简单。
  【选项】...
"""
import argparse
import json
import pathlib
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import requests

BASE = 'https://api.fz.wiki/api/v1'
ROOT = pathlib.Path(__file__).resolve().parent.parent
SITEMAP = ROOT / 'tmp/fz_sitemap.xml'
TITLES = ROOT / 'tools/baker_titles.txt'
OUT_RAW = ROOT / 'tmp/fzwiki/baker-raw'
OUT_TXT = ROOT / 'tmp/fzwiki/baker-text'

S = requests.Session()
S.headers.update({'User-Agent': 'ArcaneArchive-research/1.0 (lore archival)',
                  'Accept': 'application/json'})


def get(url):
    for i in range(4):
        try:
            r = S.get(url, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
        except Exception:
            pass
        time.sleep(1.2 * (i + 1))
    return None


def baker_titles():
    if TITLES.exists():
        return [line.strip() for line in TITLES.read_text(encoding='utf-8').splitlines()
                if line.strip()]
    text = SITEMAP.read_text(encoding='utf-8')
    urls = re.findall(r'<loc>(.*?)</loc>', text)
    titles = [urllib.parse.unquote(u.split('/wiki/', 1)[1])
              for u in urls if '/wiki/Baker/' in u]
    return sorted(set(titles))


def walk(node, out):
    if isinstance(node, list):
        for n in node:
            walk(n, out)
        return
    if not isinstance(node, dict):
        return

    kind = node.get('kind')
    if kind == 'msg':
        speaker = node.get('speakerName') or node.get('speaker') or ''
        text = node.get('text') or ''
        if text:
            out.append(f'[{speaker}] {text}\n')
        return
    if kind == 'choices':
        for opt in node.get('options') or []:
            text = opt.get('text') or ''
            if text:
                out.append(f'【选项】{text}\n')
            walk(opt.get('replies') or [], out)
        return
    if kind in ('image', 'sns_image'):
        out.append('[图片]\n')
        return
    if kind in ('emoji', 'sns_emoji'):
        out.append('[表情]\n')
        return

    if node.get('type') == 'endfieldCardBakerTopicAggregation':
        attrs = node.get('attrs') or {}
        data = attrs.get('data') or attrs
        name = data.get('topicName') or ''
        if name:
            out.append(f'\n【话题】{name}\n')

    for key, value in node.items():
        if key in ('text', 'speakerName'):
            continue
        if isinstance(value, (dict, list)):
            walk(value, out)


def fetch(title, force=False):
    slug = title.replace('/', '__')
    raw_path = OUT_RAW / f'{slug}.json'
    txt_path = OUT_TXT / f'{slug}.txt'
    if not force and raw_path.exists() and txt_path.exists():
        return title, 'skip'

    q = urllib.parse.quote(title, safe='')
    article = get(f'{BASE}/articles/by-title?title={q}')
    if not article or 'article' not in article:
        return title, 'no-article'
    art = article['article']
    rev = get(f"{BASE}/revisions/{art['currentRevisionId']}")
    if not rev or 'revision' not in rev:
        return title, 'no-revision'

    revision = rev['revision']
    out = [f'# {title}\n']
    walk(revision['contentJson'], out)
    text = re.sub(r'[ \t]+\n', '\n', ''.join(out))
    text = re.sub(r'\n{3,}', '\n\n', text).strip() + '\n'

    data = {'article': art, 'revision': revision, 'text': text}
    raw_path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    txt_path.write_text(text, encoding='utf-8')
    return title, 'ok'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--title', action='append', default=[],
                        help='只抓指定标题，可重复；默认抓 sitemap 里的全部 Baker 页')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    titles = args.title or baker_titles()
    print('titles', len(titles), flush=True)
    if args.dry_run:
        for title in titles:
            print(title)
        return

    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for title, status in ex.map(lambda t: fetch(t, args.force), titles):
            done += 1
            if status != 'ok':
                print(status.upper(), title, flush=True)
            elif done % 25 == 0:
                print('progress', done, flush=True)
    print('done', done, flush=True)


if __name__ == '__main__':
    main()
