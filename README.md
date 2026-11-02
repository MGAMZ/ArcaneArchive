<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/motto-dark.svg">
    <img src="assets/motto-light.svg" alt="定不辱应龙之名" width="100%">
  </picture>
</p>

# Arcaive: The Arcane's Archive

对《明日方舟：终末地》干员诀（本名李织烟）的剧情考据仓。仓内保存森空岛终末地 wiki 的全站语料快照、fz.wiki 的剧情页、Baker 通信页与环带纪略、影片、物品、装备、武器、蚀刻章、词典、公告八类页面，以及在语料上完成的检索结果、结构化时间线与三份长篇报告。

> 警告：含《明日方舟：终末地》剧透

## 快速开始

语料已入库，解包后即可检索，不必联网。脚本把工作目录定为 `/tmp/skwiki`，`tools/` 下的程序都按这个路径读写。

```bash
mkdir -p /tmp/skwiki
tar xzf corpus/skland-endfield-wiki_2026-10-17.tar.gz -C /tmp/skwiki
cp tools/items_all.json /tmp/skwiki/
```

只读时间线时不必解包。

```bash
node -e "const {events}=require('./data/jue_timeline.json');console.log(events.length, events[0].title)"
```

重跑检索与证据汇总。

```bash
node tools/analyze.js
node tools/evidence.js
python3 tools/index.py
```

`tools/index.py` 直接读 `corpus/` 下四份压缩包，重建 `data/source_index.tsv`，不需要解包。

森空岛的采集脚本依赖 Playwright 与一份无头 Chromium。两者的程序路径写在 `harvest.js` 与 `bulk.js` 开头，换机器时改成该机上的路径。fz 的 `fetch_baker.py` 与 `fetch_fz.py` 只依赖 `requests`，直接调公开接口。

## 目录结构

- `assets/`：README 顶部的格言横幅
- `corpus/`：四层语料快照，森空岛、fz.wiki 剧情页、fz.wiki Baker 页与 fz.wiki 补抓的八个命名空间各一份
- `data/`：结构化时间线与合一出处索引
- `evidence/`：检索命中、语音抄录与图片文字转录
- `reports/`：三份考据报告
- `tools/`：采集、抽取、检索、索引与汇总脚本

## 数据结构

### 语料快照

语料分四层，各存一个压缩包，文件名带采集日。

`corpus/skland-endfield-wiki_2026-10-17.tar.gz` 解包后有 `raw/`、`txt/` 与 `data/` 三个目录。`raw/` 存条目详情接口的原样返回，`txt/` 存同名纯文本，两处的文件名都是条目号，共 2478 条。`data/` 存采集时截获的 14 份列表类接口。

`corpus/fzwiki-2026-10-27.tar.gz` 解包后有 `prts-raw/`、`prts-text/`、`story-raw/` 与 `story-text/` 四个目录，目录名写出内容类别与文件形态。`prts-raw/` 与 `prts-text/` 各 549 份，对应 PRTS 记录，前者是接口原样 JSON，后者是展开后的文本。`story-raw/` 与 `story-text/` 各 745 份，对应任务、干员与活动页面，`story` 指剧情类页面。文件名里的斜线改为双下划线，`story-text/任务__第二章__谈剑问迹.txt` 即页面路径 `任务/第二章/谈剑问迹`。

`corpus/fzwiki-baker-2026-11-02.tar.gz` 解包后有 `baker-raw/` 与 `baker-text/` 两个目录，各 242 份，对应 fz.wiki 的 Baker 命名空间。前者是接口原样 JSON，后者是按话题与消息顺序展开的文本。Baker 页覆盖事件群聊、干员频道、剧情角色频道与表情，文件名同样把斜线改为双下划线，`baker-text/Baker__事件__应龙特勤队.txt` 即页面路径 `Baker/事件/应龙特勤队`。

`corpus/fzwiki-supplement-2026-11-02.tar.gz` 解包后有八组 `*-raw/` 与 `*-text/` 目录，另有一份 `video-sub/`，共 2143 页：`chronicle` 环带纪略 4 页、`video` 影片剧情 79 页、`item` 物品 1329 页、`equip` 装备 278 页、`weapon` 武器 87 页、`medal` 蚀刻章 182 页、`report` 塔卫研报词典 38 页、`news` 游戏动态 146 页。目录名一律用英文类别名，页内路径仍按原样把斜线换成双下划线，`item-text/物品__干员信物__诀的信物.txt` 即页面路径 `物品/干员信物/诀的信物`。`video-sub/` 存接口给出的简体中文 `.ass` 字幕，`video-text/` 是按时间码展开的对白，同一页的不同角色变体各成一节。

重新打包 fz 各层时用 `tar czf <包名> --hard-dereference --sort=name -C tmp/fzwiki <目录…>`。本机 WSL 的 `/mnt/f` 会给不同文件复用 inode，普通 `tar` 会把一部分 `*-text` 成员误存成指向 `*-raw` 里某个 JSON 的硬链接（size 0），解出来是别人的正文。`--hard-dereference` 可避开，解包后的文本应与采集目录逐字节一致，打包后抽一页核对即可。

森空岛一层采集于 2026 年 10 月 17 日，fz 剧情一层采集于 2026 年 10 月 27 日，fz Baker 与补抓的八个命名空间采集于 2026 年 11 月 2 日，此后的游戏内容不在其中。

### 条目清单与合一索引

`tools/items_all.json` 是长度 2478 的数组，每条六字段：`itemId` 条目号，`name` 标题，`mainTypeId` 与 `subTypeId` 分类编号，`subName` 分类名，`lang` 语言。

`data/source_index.tsv` 把四层语料合到一张表里，共 6156 行，其中森空岛 2478 行、fz 剧情 1293 行、fz Baker 242 行、fz 补抓 2143 行。七列依次为 `source` 来源、`key` 编号或页面路径、`title` 标题、`category` 分类、`corpus` 压缩包名、`member` 包内路径、`url` 原页面地址。时间线里每条证据的 `source` 与 `id` 就是前两列，凭这两列可以在表中查到标题与原文位置。

### 文本格式

`txt/` 下每份文本用行首标记保留原页层级。`######## [章]` 是章名，`#### [板块]` 是板块名并附控件标识，`| 档案图片 | 档案内容 |` 一类是表格行，`【entry:2365x0】` 是指向其它条目的引用。图片位置只留 `[image]` 占位，图上的文字另见 `evidence/ocr_transcripts.md`。

Baker 文本不走上面的章/板块标记，每行以 `[发言人] 内容` 记录一条消息，`【话题】` 标记话题，`【选项】` 标记玩家选项，`[图片]` 与 `[表情]` 是占位。`baker-text/Baker__事件__应龙特勤队.txt` 里的 `[庄方宜] 诀只用三年时间就从候补成为了队长……` 即该页的一条消息。

补抓的八类各有自己的文本形态。`chronicle-text/` 保留原页的标题层级与表格行，`report-text/` 每个词条以 `### 词条名` 起头、后接 `【分类】` 与释义。`item-text/`、`equip-text/`、`weapon-text/`、`medal-text/` 只取文字字段，统一成 `【物品】`/`【装备】`/`【武器】`/`【蚀刻章】` 后的键值行：`【记述】` 是物品与装备的 flavor 原文，`【背景】` 是武器页的长篇背景，属性、材料与套组数值表都不收。`video-text/` 每页按角色变体分节，逐行写 `[时:分:秒.百分秒] 台词`，同一句连续重复的只留一次。`news-text/` 是公告与新闻的正文，日期写在标题里。

### 时间线数据

`data/jue_timeline.json` 由 `meta` 与 `events` 两键组成。`events` 现 38 条，`track` 分世界史、武陵区域史与诀个人史三层，编号前缀分别是 `W`、`L`、`J`。数组顺序大致按年份排列，编号不随之递增。

| 字段 | 含义 |
|---|---|
| `id` | 事件编号 |
| `year` | 排序用年份，标注为约年的条目同样填一个数 |
| `year_label` | 正文年份写法，带「约」「之前」「之后」时 `year` 不是确证年份 |
| `track` | `world`、`wuling`、`jue` |
| `title` | 事件标题 |
| `summary` | 事件摘要 |
| `jue_link` | 该事件与诀的关系 |
| `evidence` | 出处数组 |
| `confidence` | A 为原文写明年份，B 为多条互证，C 为单条线索或站外资料 |

出处统一为六字段。森空岛条目写成 `{"source":"skland","id":"2372","title":"宏山科学院","category":"档案库","section":"档案库·中枢档案·宏山科学院","quote":"..."}`。fz 页面写成 `{"source":"fz","id":"任务/第二章/谈剑问迹","title":"谈剑问迹","category":"任务","section":"剧情对白","quote":"..."}`。`title` 与 `category` 与 `data/source_index.tsv` 一致，`quote` 一律是语料原文的逐字片段，报告里的每条引文都用它回查。

### 证据文件

| 文件 | 内容 |
|---|---|
| `evidence/evidence_mentions.txt` | 森空岛全语料中三种词形的命中，分叙事类、仅数值与攻略类、正文未提名但链接指向诀的条目三节 |
| `evidence/fz_mentions.txt` | fz 三层的三种词形命中，分点名命中、误命中与未提名的候选页三节 |
| `evidence/jue_voices_cn.txt` | 诀的中文语音逐句抄录，按语音类别分组 |
| `evidence/ocr_transcripts.md` | 诀页与个别干员页的图片文字转录，方法与范围写在文件开头 |

## 处理流程

采集分两步。先由 `harvest.js` 打开站点首页，把浏览器收到的 wiki 接口返回全部存成 JSON，得到条目清单。再由 `bulk.js` 按清单逐条打开详情页，等接口返回后交给 `extract.js` 转成文本，写成 `raw/` 与 `txt/` 的一对文件。

检索与汇总也分两步。`analyze.js` 在全部文本里找「诀」「李织烟」「织烟」三种词形，剔除技能名与常用词造成的误命中，输出命中位置与所在板块。`evidence.js` 把命中整理成三节证据文件，并补上「正文没提名字、只靠词条链接指过来」的那一类。

这两步只覆盖森空岛一层。fz 三层的同名检索由 `scan_fz.py` 单独完成，它直接读压缩包，不必解包，除点名命中之外还出一份未提名的候选页表，供人工判读。

索引单独一步。`index.py` 枚举四份压缩包里的成员，与条目清单的标题合并，写出 `data/source_index.tsv`。时间线的证据、报告的引文与这份索引用同一套编号，三者对得上。

fz.wiki 的 Baker 层由 `fetch_baker.py` 单独抓取。标题清单固化在 `tools/baker_titles.txt`，共 242 条；脚本按清单经公开接口取当前修订，按 `msg`、`choices`、`image` 等节点展开成 `[发言人] 内容` 的文本。

fz.wiki 补抓的八个命名空间由 `fetch_fz.py` 抓取。它按前缀向列表接口枚举标题，逐页取当前修订，`extract_fz.py` 再按页面形态选展开规则：环带纪略与公告走通用文档展开，物品、装备、武器、蚀刻章各取自己的卡片字段，研报词典按词条输出，影片另下简体中文 `.ass` 字幕并按时间码展开。`fetch_fz.py --rebuild-text` 不联网，只从已有的 `*-raw/` 重写文本，字幕也复用已下载的副本。

| 脚本 | 作用 |
|---|---|
| `harvest.js` | 打开站点首页，记录全部成功返回的 wiki 接口 JSON |
| `bulk.js` | 按条目清单逐条抓取详情接口，并调用 `extract.js` 生成纯文本 |
| `extract.js` | 把详情接口的块结构转换为带章与板块标记的纯文本 |
| `analyze.js` | 在全部文本中检索三种词形，剔除技能名与常用词的误命中 |
| `evidence.js` | 把命中结果整理为证据文件，并补上词条交叉引用一节 |
| `index.py` | 由四份语料压缩包生成合一出处索引 |
| `fetch_baker.py` | 抓取 fz.wiki 的 Baker 命名空间，生成 `baker-raw/` 与 `baker-text/` |
| `baker_titles.txt` | 242 个 Baker 页标题清单，`fetch_baker.py` 的输入 |
| `fetch_fz.py` | 按命名空间前缀抓取 fz.wiki 页面与影片字幕，生成补抓包的 `*-raw/`、`*-text/` 与 `video-sub/` |
| `extract_fz.py` | 把 fz.wiki 接口原样 JSON 展开成文本，按页面形态分七套规则 |
| `scan_fz.py` | 在 fz 三层语料里检索三种词形，产出 `evidence/fz_mentions.txt` 与未提名候选表 |
| `images.js` | 清点某个条目中的全部图片地址及其所在板块 |
| `dlimg.js` | 按板块下载承载文字的图片，供转录使用 |

## 数据来源与时效

森空岛 wiki 的语料采集于 2026 年 10 月 17 日，共 2478 条，存于 `corpus/skland-endfield-wiki_2026-10-17.tar.gz`。fz.wiki 的剧情语料采集于 2026 年 10 月 27 日，含 PRTS 记录 549 页、任务 572 页、干员 35 页、活动 138 页，存于 `corpus/fzwiki-2026-10-27.tar.gz`。fz.wiki 的 Baker 语料采集于 2026 年 11 月 2 日，共 242 页，存于 `corpus/fzwiki-baker-2026-11-02.tar.gz`；同日的八个命名空间共 2143 页，存于 `corpus/fzwiki-supplement-2026-11-02.tar.gz`。四层都在仓内，按索引的 `corpus` 与 `member` 两列即可取到任意一条原文。

快照冻结于采集日。凡「站内没有」一类判断，都以此日为界。

https://wiki.skland.com/endfield

https://www.fz.wiki/

## 站外对照

[萌娘百科-诀（中等置信度）](https://mzh.moegirl.org.cn/index.php?title=%E8%AF%80)
[百度百科-诀 （中等置信度）](https://baike.baidu.com/item/%E8%AF%80/68217227?fromModule=lemma_sense-layer#viewPageContent)
[《明日方舟：终末地》WIKI-森空岛（最高置信度）](https://wiki.skland.com/endfield/detail?mainTypeId=1&subTypeId=1&gameEntryId=1675&header=0)
[终末地WIKI-诀（高置信度）](https://www.fz.wiki/wiki/%E5%B9%B2%E5%91%98/%E8%AF%80)

## 已知缺口

PRTS 记录 549 页里，12 页是分类索引，537 页是内容页，其中 89 页正文不足 200 字，多为只有一行图片说明或一句记录，编者尚未录入的部分与只存在于游戏内图片的部分无法从站内补。档案页的图片只对诀页与个别干员页做过转录，手写件与屏幕截图还有未读部分。剧情演出中的语音、镜头与分支没有转写，任务页给的是台词与选项，影片页给的是字幕。物品、装备与武器已全量抓取，但只收简介与 flavor 文字，属性、材料与套组数值表没有转成文本。

fz 三层的点名命中与未提名候选页都已逐页读过，但只写职务、不写名字的段落仍可能漏检。Baker 页的图片、表情与语音没有逐条还原，文本只留占位。

## 版权与致谢

游戏文本、图片与角色设定版权归鹰角网络所有。wiki 条目由森空岛及其编辑者贡献。
本仓是非商业性质的玩家考据，不主张对游戏素材的任何权利。
如有侵权请随时联系 312065559@qq.com
