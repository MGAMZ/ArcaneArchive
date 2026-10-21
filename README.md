<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/motto-dark.svg">
    <img src="assets/motto-light.svg" alt="定不辱应龙之名" width="100%">
  </picture>
</p>

# Arcaive: The Arcane's Archive

对《明日方舟：终末地》干员诀（本名李织烟）在森空岛终末地 wiki 全站文本的爬取与分析

> 警告：含《明日方舟：终末地》剧透

## 目录结构

- `诀-剧情交集全量考据.md`：字如其名
- `assets/`：README 顶部的格言横幅
- `corpus/`：全站语料快照
- `evidence/`：检索命中、语音抄录与图片文字转录
- `tools/`：采集、抽取、检索与汇总脚本

## 数据来源

https://wiki.skland.com/endfield

2026-10-17采集得：终末地百科 2288 条、游戏攻略辑 53 条、情报档案库 137 条。

## 启动

基于 Node.js 运行

```bash
mkdir -p /tmp/skwiki
tar xzf corpus/skland-endfield-wiki_2026-10-17.tar.gz -C /tmp/skwiki
cp tools/items_all.json /tmp/skwiki/
node tools/analyze.js
node tools/evidence.js
```

| 脚本 | 作用 |
|---|---|
| `harvest.js` | 打开站点首页，记录全部成功返回的 wiki 接口 JSON |
| `bulk.js` | 按条目清单逐条抓取详情接口，并调用 `extract.js` 生成可读文本 |
| `extract.js` | 把详情接口返回的块结构转换为带章节标记的纯文本 |
| `analyze.js` | 在全部文本中检索诀的三种词形，输出命中位置与所在板块 |
| `evidence.js` | 把命中结果整理为证据文件，并补上词条交叉引用一节 |
| `images.js` | 清点某个条目中的全部图片地址及其所在板块 |
| `dlimg.js` | 按板块下载承载文本的图片，供视觉转录使用 |

## 版权与致谢

游戏文本、图片与角色设定版权归鹰角网络所有。wiki 条目由森空岛及其编辑者贡献。
本仓是非商业性质的玩家考据，不主张对游戏素材的任何权利。
如有侵权请随时联系 312065559@qq.com
