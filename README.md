<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/motto-dark.svg">
    <img src="assets/motto-light.svg" alt="定不辱应龙之名" width="100%">
  </picture>
</p>

# Arcaive: The Arcane's Archive

对《明日方舟：终末地》干员诀（本名李织烟）的剧情考据仓。仓内保存一份森空岛终末地 wiki 的全站语料快照，以及在快照上完成的检索结果、结构化时间线与两份长篇报告。

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
```

采集脚本依赖 Playwright 与一份无头 Chromium。两者的程序路径写在 `harvest.js` 与 `bulk.js` 开头，换机器时改成该机上的路径。

## 目录结构

- `assets/`：README 顶部的格言横幅
- `corpus/`：森空岛全站语料快照
- `data/`：结构化时间线
- `evidence/`：检索命中、条目索引、语音抄录与图片文字转录
- `reports/`：两份考据报告
- `tools/`：采集、抽取、检索与汇总脚本

## 数据结构

### 语料快照

`corpus/skland-endfield-wiki_2026-10-17.tar.gz` 解包后有三个目录。`raw/` 存条目详情接口的原样返回，`txt/` 存同名纯文本，两处的文件名都是条目号，共 2478 条。`data/` 存采集时截获的 15 份列表类接口。快照采集于 2026 年 10 月 17 日，此后的游戏内容不在其中。

### 条目清单

`tools/items_all.json` 是长度 2478 的数组，每条六字段：`itemId` 条目号，`name` 标题，`mainTypeId` 与 `subTypeId` 分类编号，`subName` 分类名，`lang` 语言。报告里的「条目2372」就是这个 `itemId`，抓到 `txt/2372.txt` 即可读原文。

### 文本格式

`txt/` 下每份文本用行首标记保留原页层级。`######## [章]` 是章名，`#### [板块]` 是板块名并附控件标识，`| 档案图片 | 档案内容 |` 一类是表格行，`【entry:2365x0】` 是指向其它条目的引用。图片位置只留 `[image]` 占位，图上的文字另见 `evidence/ocr_transcripts.md`。

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

出处有两种形态。森空岛条目写成 `{"itemId":"2372","section":"档案库·中枢档案·宏山科学院","quote":"..."}`。fz 页面写成 `{"source":"fz","page":"任务/第二章/谈剑问迹","section":"剧情对白","quote":"..."}`。`quote` 一律是语料原文的逐字片段，报告里的每条引文都用它回查。

### 证据文件

| 文件 | 内容 |
|---|---|
| `evidence/item_index.tsv` | 2478 行，四列，依次为条目号、主分类、子分类、标题 |
| `evidence/evidence_mentions.txt` | 全语料中三种词形的命中，分叙事类、仅数值与攻略类、正文未提名但链接指向诀的条目三节 |
| `evidence/jue_voices_cn.txt` | 诀的中文语音逐句抄录，按语音类别分组 |
| `evidence/ocr_transcripts.md` | 诀页与个别干员页的图片文字转录，方法与范围写在文件开头 |

## 处理流程

采集分两步。先由 `harvest.js` 打开站点首页，把浏览器收到的 wiki 接口返回全部存成 JSON，得到条目清单。再由 `bulk.js` 按清单逐条打开详情页，等接口返回后交给 `extract.js` 转成文本，写成 `raw/` 与 `txt/` 的一对文件。

检索与汇总也分两步。`analyze.js` 在全部文本里找「诀」「李织烟」「织烟」三种词形，剔除技能名与常用词造成的误命中，输出命中位置与所在板块。`evidence.js` 把命中整理成三节证据文件，并补上「正文没提名字、只靠词条链接指过来」的那一类。

| 脚本 | 作用 |
|---|---|
| `harvest.js` | 打开站点首页，记录全部成功返回的 wiki 接口 JSON |
| `bulk.js` | 按条目清单逐条抓取详情接口，并调用 `extract.js` 生成纯文本 |
| `extract.js` | 把详情接口的块结构转换为带章与板块标记的纯文本 |
| `analyze.js` | 在全部文本中检索三种词形，剔除技能名与常用词的误命中 |
| `evidence.js` | 把命中结果整理为证据文件，并补上词条交叉引用一节 |
| `images.js` | 清点某个条目中的全部图片地址及其所在板块 |
| `dlimg.js` | 按板块下载承载文字的图片，供转录使用 |

## 数据来源与时效

森空岛 wiki 的语料采集于 2026 年 10 月 17 日，共 2478 条。fz.wiki 的语料采集于 2026 年 10 月 27 日，含 PRTS 记录 549 页、任务 572 页、干员 35 页、活动 138 页。fz 这一层只留在工作目录，没有入库，时间线里 21 条 fz 出处要回查时得先重跑采集。

快照冻结于采集日。凡「站内没有」一类判断，都以此日为界。

https://wiki.skland.com/endfield

https://www.fz.wiki/

## 站外对照

[萌娘百科-诀](https://mzh.moegirl.org.cn/index.php?title=%E8%AF%80)
[百度百科-诀](https://baike.baidu.com/item/%E8%AF%80/68217227?fromModule=lemma_sense-layer#viewPageContent)
[《明日方舟：终末地》WIKI-森空岛](https://wiki.skland.com/endfield/detail?mainTypeId=1&subTypeId=1&gameEntryId=1675&header=0)
[终末地WIKI-诀](https://www.fz.wiki/wiki/%E5%B9%B2%E5%91%98/%E8%AF%80)

## 已知缺口

PRTS 记录里有 192 页只有标题与分类，没有正文，编者尚未录入或原文只存在于游戏内图片。档案页的图片只对诀页与个别干员页做过转录，手写件与屏幕截图还有未读部分。剧情演出中的语音、镜头与分支没有转写，任务页给的是台词与选项。

## 版权与致谢

游戏文本、图片与角色设定版权归鹰角网络所有。wiki 条目由森空岛及其编辑者贡献。
本仓是非商业性质的玩家考据，不主张对游戏素材的任何权利。
如有侵权请随时联系 312065559@qq.com
