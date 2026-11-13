# ArcaneArchive

我是诀（李织烟）厨。这个仓用来收纳一切与诀有关的材料，也用来写考据报告。游戏还在更新，仓里只跟最新一版，旧语料不留。

工作前请阅读以下指南：
1. /mnt/f/mgam_repos/prompts/annotations.md
2. /mnt/f/mgam_repos/prompts/good_words.md
3. /mnt/f/mgam_repos/prompts/PaperWriting.md

## 仓里有什么

- `corpus/` 四层语料快照，森空岛全站、fz.wiki 剧情、fz.wiki Baker、fz.wiki 补抓各一份压缩包。
- `data/source_index.tsv` 四层唯一的出处表。报告里的每条引文都要凭 `source` 与 `id` 在这里查到原文。
- `data/jue_timeline.json` 时间线，出处与索引同一套编号。
- `evidence/` 检索命中、语音抄录与图片文字转录。
- `reports/` 考据报告与人工择选的时间线。
- `tools/` 采集、展开、检索与索引脚本，职责见 README。

判断站内没有某条内容时，以 `corpus/` 里最新一批为准。

## 文档分工

- `README.md` 只讲是什么、怎么跑、怎么更新。不写剧情结论，不写采集沿革，不写行数、页数、条目数这类能从数据算出来的数字。
- `history.md` 按采集日记语料层的变化，只写代码与快照看不出来的采集行为，以及当时放弃的源与字段。新条目放最前，一次采集一条。
- `reports/` 放结论。结论出现在 README 里就是放错了地方。
- 本文件与 README、`history.md` 冲突时，以本文件为准。

## 不许做的事

- 引文必须是语料原文的逐字子串。站内没有的说法就删，或标明取自站外，不软化、不补写。
- 不保留旧快照。新一批入库时替换旧包，`history.md` 记一句上一批停在哪天即可。
- 不动 README 顶部的横幅、一级标题、剧透警告、版权段与联系邮箱。
- 不写「本次」「此前」「补采」「改为」这类只在对比上一版时才成立的句子。文档与注释只描述现在。
- 不把过程写进文档。删掉一句后读者仍能完成他手上的事，这句就该删。
- 汇报先给结论与依据，不铺执行步骤，不写客套开场与总结段。
- 只改被点名的文件。看到别处的废话、过时说明，先报告，不顺手重写。

## 改采集或索引时

- 包名固定在 `tools/corpus.py` 里，换快照时改这一处。
- 同一次改动里同步 README 的更新语料一节与 `history.md`。
- 打包各层必须带 `--hard-dereference`，否则文本会变成指向 JSON 的硬链接。
- 条目清单由 `corpus/` 里的三份目录接口现读，Baker 标题由接口按前缀列举。

## 交付前

- `python3 tools/index.py` 重建索引，产物应与仓内文件逐字相同。
- `python3 tools/analyze.py` 只打印命中概况。
- `python3 tools/evidence.py`、`python3 tools/scan_fz.py` 重跑，产物应与仓内证据文件逐字相同。
- 文档里的命令先跑通再写。
