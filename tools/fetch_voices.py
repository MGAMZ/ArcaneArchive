"""按干员页抓取角色语音，无损转码为 FLAC 并写角色层索引。

干员页里每条语音是一张 `endfieldCardCharacterArchive__voice` 卡片，带场景名、中文文本与
四种语言的音频地址。脚本取页面、下载选定语言的音频、转成 FLAC，写入 `work/voices/<角色>/`，
索引记顺序、场景、解锁条件、文本与音频相对路径。已存在的音频跳过，中断后可直接重跑。

```bash
python3 tools/fetch_voices.py --character 诀
python3 tools/fetch_voices.py --character 诀 --lang all
```
"""
import argparse
import datetime
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

import requests

import corpus
import extract_fz

BASE = 'https://api.fz.wiki/api/v1'
PAGE_RAW = corpus.ROOT / 'work/fzwiki/story-raw'
PAGE_TEXT = corpus.ROOT / 'work/fzwiki/story-text'
OUT = corpus.ROOT / 'work/voices'
LANGS = {'zh': 'Chinese', 'en': 'English', 'ja': 'Japanese', 'ko': 'Korean'}

SESSION = requests.Session()
SESSION.headers.update({'User-Agent': 'ArcaneArchive-research/1.0 (lore archival)'})


def load_page(name):
    """干员页原样 JSON。工作目录里没有就从接口取，并补一份展开文本。"""
    path = PAGE_RAW / f'干员__{name}.json'
    if not path.exists():
        title = f'干员/{name}'
        art = SESSION.get(f'{BASE}/articles/by-title', params={'title': title}, timeout=40)
        art.raise_for_status()
        article = art.json()['article']
        rev = SESSION.get(f"{BASE}/revisions/{article['currentRevisionId']}", timeout=40)
        rev.raise_for_status()
        revision = rev.json()['revision']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'article': article, 'revision': revision}, ensure_ascii=False),
                        encoding='utf-8')
        PAGE_TEXT.mkdir(parents=True, exist_ok=True)
        (PAGE_TEXT / f'干员__{name}.txt').write_text(
            extract_fz.expand('story', revision['contentJson']), encoding='utf-8')
    return json.loads(path.read_text(encoding='utf-8'))


def voice_cards(content):
    """按页面先后顺序取出语音卡片的数据。"""
    cards = []

    def walk(node):
        if isinstance(node, dict):
            attrs = node.get('attrs') or {}
            if attrs.get('itemType') == 'endfieldCardCharacterArchive__voice':
                cards.append(attrs['data'])
            for value in node.values():
                if isinstance(value, (dict, list)):
                    walk(value)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(content)
    return cards


def fetch_audio(url, path):
    """下载 wav 并转成 FLAC。文件已存在则跳过。"""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    wav = path.with_suffix('.wav')
    res = SESSION.get(url, timeout=180)
    res.raise_for_status()
    wav.write_bytes(res.content)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(wav),
                    '-compression_level', '8', str(path)], check=True)
    wav.unlink()


def seconds(path):
    res = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                          '-of', 'csv=p=0', str(path)],
                         check=True, capture_output=True, text=True)
    return round(float(res.stdout.strip()), 2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--character', required=True, help='干员名，与页面标题 `干员/<名>` 一致')
    parser.add_argument('--lang', default='zh', choices=[*LANGS, 'all'], help='配音语言，默认中文')
    args = parser.parse_args()
    langs = list(LANGS) if args.lang == 'all' else [args.lang]

    data = load_page(args.character)
    cards = voice_cards(data['revision']['contentJson'])
    root = OUT / args.character

    entries = []
    for order, card in enumerate(cards, 1):
        scene = card['scene'].replace('/', '／')
        entries.append({
            'order': order,
            'scene': card['scene'],
            'unlock': card.get('unlockHint', ''),
            'text': card['text'],
            'files': {code: f'audio/{code}/{order:03d}_{scene}.flac' for code in langs},
        })

    def grab(pair):
        entry, card = pair
        durations = {}
        for code in langs:
            path = root / entry['files'][code]
            fetch_audio(card['audioUrls'][LANGS[code]], path)
            durations[code] = seconds(path)
        return durations

    with ThreadPoolExecutor(max_workers=8) as ex:
        for entry, durations in zip(entries, ex.map(grab, zip(entries, cards))):
            entry['seconds'] = durations

    index = {
        'character': args.character,
        'page': f'干员/{args.character}',
        'revision': data['revision']['id'],
        'source': 'https://www.fz.wiki/wiki/' + quote(f'干员/{args.character}'),
        'collected': datetime.date.today().isoformat(),
        'audio': {'format': 'flac', 'languages': langs},
        'voices': entries,
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n',
                                     encoding='utf-8')
    size = sum(p.stat().st_size for p in root.rglob('*.flac'))
    print(f'{args.character}: {len(entries)} 条，{"、".join(langs)}，{size / 1048576:.1f} MB',
          flush=True)


if __name__ == '__main__':
    main()