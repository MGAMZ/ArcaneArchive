<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/motto-dark.svg">
    <img src="assets/motto-light.svg" alt="定不辱应龙之名" width="100%">
  </picture>
</p>

# Arcaive: The Arcane's Archive

对《明日方舟：终末地》干员诀（本名李织烟）的剧情考据仓。仓内存放森空岛与 fz.wiki 的语料快照，以及在语料上整理的出处索引、时间线与考据报告。

> 警告：含《明日方舟：终末地》剧透

## 快速开始

森空岛一层的脚本把工作目录写成了 `/tmp/skwiki`，先解包并放好条目清单。

```bash
mkdir -p /tmp/skwiki
tar xzf corpus/skland-endfield-wiki_*.tar.gz -C /tmp/skwiki
cp tools/items_all.json /tmp/skwiki/
```

fz 三层的检索与索引直接读 `corpus/` 下的压缩包，时间线也能直接读，都不必解包。

```bash
node -e "const {events}=require('./data/jue_timeline.json');console.log(events.length, events[0].title)"
```

重跑检索、证据汇总与索引。

```bash
node tools/analyze.js
node tools/evidence.js
python3 tools/scan_fz.py
python3 tools/index.py
```

`tools/index.py` 重建 `data/source_index.tsv`。`analyze.js` 与 `evidence.js` 的产物写在 `/tmp/skwiki`，其中 `evidence_mentions.txt` 需要复制进 `evidence/`。

## 数据

语料分四层，各存一份带采集日的压缩包。

- `corpus/skland-endfield-wiki_<采集日>.tar.gz`：森空岛终末地 wiki 的全站条目，含条目详情接口的原样 JSON、同名纯文本与采集时截获的列表接口。
- `corpus/fzwiki-<采集日>.tar.gz`：fz.wiki 的 PRTS 记录与任务、干员、活动页面。
- `corpus/fzwiki-baker-<采集日>.tar.gz`：fz.wiki 的 Baker 命名空间，游戏内通讯软件的事件群聊与干员频道。
- `corpus/fzwiki-supplement-<采集日>.tar.gz`：fz.wiki 的环带纪略、影片、物品、装备、武器、蚀刻章、研报词典与游戏动态。

`*-raw/` 存接口原样 JSON，`*-text/` 存展开后的纯文本，森空岛一层对应的目录名是 `raw/` 与 `txt/`。纯文本保留原页层级，图片只留 `[image]` 占位，图上的文字另见 `evidence/ocr_transcripts.md`。

`data/source_index.tsv` 把四层合到一张表，列依次为 `source`、`key`、`title`、`category`、`corpus`、`member`、`url`。时间线每条证据的 `source` 与 `id` 就是前两列，凭这两列可以找到包内路径与原页面地址。

`data/jue_timeline.json` 的 `events` 分世界史、武陵区域史与诀个人史三层，每条含 `year`、`year_label`、`title`、`summary`、`jue_link`、`evidence` 与 `confidence`。`confidence` 分 A、B、C 三级，分级标准写在 `meta` 里。

`evidence/` 存检索命中、语音抄录与图片文字转录，`reports/` 存考据报告与一份人工择选的时间线。

快照冻结于采集日。判断站内没有某条内容时，以 `corpus/` 里最新一批为准，历次采集与取舍见 [history.md](history.md)。

## 脚本

| 文件 | 作用 |
|---|---|
| `harvest.js` | 打开森空岛首页，记录全部 wiki 接口返回，得到列表接口与条目目录 |
| `bulk.js` | 按条目清单逐条抓详情，调用 `extract.js` 生成纯文本 |
| `extract.js` | 把详情接口的块结构转成带章与板块标记的纯文本 |
| `analyze.js` | 在森空岛文本里检索三种词形，剔除技能名与常用词造成的误命中 |
| `evidence.js` | 把命中整理成证据文件，补上词条交叉引用一节 |
| `index.py` | 由四份压缩包生成合一出处索引 |
| `fetch_baker.py` | 按 `baker_titles.txt` 的清单抓取 Baker 命名空间 |
| `fetch_fz.py` | 按命名空间前缀抓取页面与影片字幕，可离线重展开文本 |
| `extract_fz.py` | 按页面形态把原样 JSON 展开成文本 |
| `scan_fz.py` | 在 fz 三层检索三种词形，产出 `evidence/fz_mentions.txt` 与未提名候选表 |
| `images.js` | 清点条目里的图片地址与所在板块 |
| `dlimg.js` | 按板块下载承载文字的图片 |
| `items_all.json` | 森空岛条目清单，字段为条目号、标题、分类与语言 |
| `baker_titles.txt` | Baker 页标题清单，`fetch_baker.py` 的输入 |

## 更新语料

森空岛一层依赖 Playwright 与一份无头 Chromium，两者的路径写在 `harvest.js` 与 `bulk.js` 开头，换机器时先改。抓取前清空 `/tmp/skwiki/raw` 与 `/tmp/skwiki/txt`，脚本会跳过已存在的条目。

```bash
node tools/harvest.js
node tools/bulk.js
tar czf "corpus/skland-endfield-wiki_$(date +%F).tar.gz" -C /tmp/skwiki raw txt data
```

条目清单 `tools/items_all.json` 不由采集脚本生成，需要从 `data/` 里的条目目录接口整理出来，再复制到 `/tmp/skwiki/` 供 `bulk.js`、`analyze.js` 与 `evidence.js` 使用。

fz 的 Baker 层与补抓层由 Python 脚本抓取，产物写在 `tmp/fzwiki/`。

```bash
python3 tools/fetch_fz.py
python3 tools/fetch_baker.py
```

剧情层的 PRTS 记录与任务、干员、活动没有采集脚本。补抓的页面按 `prts-raw/`、`story-raw/` 一类目录放好后，用 `extract_fz.py` 展开。

```bash
python3 tools/extract_fz.py prts-raw prts-text
python3 tools/extract_fz.py story-raw story-text
```

打包 fz 各层时带上 `--hard-dereference`，三个包各自打包。WSL 挂载的 Windows 盘会给不同文件复用 inode，普通 `tar` 会把一部分 `*-text` 成员存成指向 `*-raw` 里某个 JSON 的硬链接，解出来是别人的正文。

```bash
tar czf "corpus/fzwiki-$(date +%F).tar.gz" --hard-dereference --sort=name -C tmp/fzwiki prts-raw prts-text story-raw story-text
```

新包入库后改 `tools/index.py` 与 `tools/scan_fz.py` 顶部的包名，`index.py` 表头与 `evidence.js` 开头那句里的采集日一并改，然后重建索引，按需重跑检索与更新报告，并在 `history.md` 记一条。

## 已知缺口

- 剧情演出里的语音、镜头与分支走向没有转写。任务页给的是台词与选项，影片页给的是简体中文字幕。
- 图片上的文字只转录了诀页与个别干员页。
- 物品、装备与武器只收简介与 flavor 文字，属性、材料与套组数值表没有转成文本。
- 只写职务、不写名字的文字可能漏检，检索命中后仍需逐页判读。

## 版权与致谢

游戏文本、图片与角色设定版权归鹰角网络所有。wiki 条目由森空岛及其编辑者贡献。
本仓是非商业性质的玩家考据，不主张对游戏素材的任何权利。
如有侵权请随时联系 312065559@qq.com