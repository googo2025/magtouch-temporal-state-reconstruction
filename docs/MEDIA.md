# 最终模型回测媒体

## 紧凑半球展示 · 5×回放 / Compact hemispherical presentation

| 语言 | 完整三维形变与波形视频 | 动态图 |
| --- | --- | --- |
| 中文 | [1600×1000 MP4](../media/compact/final138_compact_hemisphere_zh_5x.mp4) | [1200×750 GIF](../media/compact/final138_compact_hemisphere_zh_5x.gif) |
| English | [1600×1000 MP4](../media/compact/final138_compact_hemisphere_en_5x.mp4) | [1200×750 GIF](../media/compact/final138_compact_hemisphere_en_5x.gif) |

此版对应上表展示样本7和论文半球序列。实验时间跨度90.8908927 s；5× MP4播放18.178180 s，GIF约18.19 s。两者完整保留80个保存状态，不补中间形变。MP4采用微秒PTS（舍入不超过500 ns，末帧1 µs），GIF采用百分之一秒延时（舍入不超过5 ms，末帧10 ms）；保持画面不代表在两保存时刻之间估计了新状态。

表面配色改为**位移模长/mm**，全79个有效保存状态及中英版本使用同一0至5.106820 mm色标；旧原生视频的带符号u_z色标保持原样。两种颜色量不可当作相同指标。磁片仅用固定材质色。XYZ范围、等比例、视角及位移倍率1保持；无实测形变GT，不增加训练或模型推理。磁场波形保留全部3092原生行/3091有效行及无效断线，黑色实测、橙色重建，竖线显示当前保存状态。

新两视频各80帧全解码及时钟检查、两GIF全部80帧读回核对已通过；160帧程序化文字边界/重叠检查及10张关键原尺寸画面实际审阅通过，未声称全部160帧人工逐张审阅。[展示与验收记录](../data/compact_media_presentation.json)。

以下均来自最终138轮模型。中文和英文是同一科学输出的语言版本；左右为柔性估计和同模型磁片状态两种视图，不是两个模型比较。

| 展示样本 | 中文原生视频 | English native video |
| --- | --- | --- |
| 1 | [中文](../media/native/sequence_01_zh.mp4) | [English](../media/native/sequence_01_en.mp4) |
| 2 | [中文](../media/native/sequence_02_zh.mp4) | [English](../media/native/sequence_02_en.mp4) |
| 3 | [中文](../media/native/sequence_03_zh.mp4) | [English](../media/native/sequence_03_en.mp4) |
| 4 | [中文](../media/native/sequence_04_zh.mp4) | [English](../media/native/sequence_04_en.mp4) |
| 5 | [中文](../media/native/sequence_05_zh.mp4) | [English](../media/native/sequence_05_en.mp4) |
| 6 | [中文](../media/native/sequence_06_zh.mp4) | [English](../media/native/sequence_06_en.mp4) |
| 7 | [中文](../media/native/sequence_07_zh.mp4) | [English](../media/native/sequence_07_en.mp4) |
| 8 | [中文](../media/native/sequence_08_zh.mp4) | [English](../media/native/sequence_08_en.mp4) |
| 9 | [中文](../media/native/sequence_09_zh.mp4) | [English](../media/native/sequence_09_en.mp4) |

每条序列只有80个保存形变槽，其中79个有效、1个UNKNOWN灰色名义状态。磁场观测保持完整原生时钟，几何不是逐原生磁场帧都有保存；不插值补造q，不二次缩放q，不放大形变。九个展示样本共用XYZ毫米比例、范围、视角和uz色标，位移倍率1。没有实测形变GT、CAD触头或命令轨迹叠加。

首页[中文GIF](../media/final138_3d_preview_zh.gif)和[English GIF](../media/final138_3d_preview_en.gif)仅为展示样本1的已渲染像素裁块。GIF时钟最大绝对舍入4.883ms，末帧保持10ms，总38.130s；对应原生MP4最大时钟舍入500ns，末帧1µs，总38.119988s。不同格式的时钟精度不能混称。

已有18视频的80帧全解码与原生时钟验收复用，累计72张关键PNG曾按原尺寸审阅；不是全部1440帧人工逐张检查。原libx264宏块率／级别警告保留，不宣称全部播放器兼容。打包没有重新解码、编码或生成任何媒体。


## 实物按压视频预览 / Physical pressing preview

首页新增 [最终显式138实物演示GIF](../media/measured/final138_real_demo_3x.gif)。实验者直接确认运行第138轮显式节点／磁片状态模型。原片段25.787333 s、1280×720、30 fps；GIF为800×450、52帧、3×、8.670 s，保留完整过程和同一摄像画面，未插值、拟时移或改变形变倍率。256色GIF会量化颜色；原MP4在作者处保留，本次仅公开无声GIF。

The homepage adds a physical pressing demonstration of the final explicit epoch-138 model, directly confirmed by the experimenter. The complete 25.787333 s source is sampled into a 52-frame, 800×450 GIF at 3x speed, lasting 8.670 s. The same camera view is retained without interpolation, fitted time shift or deformation amplification. GIF palette and centisecond time quantization apply. The original MP4 is retained by the authors; this increment publishes only the silent GIF.

该片段与原保存半球序列是不同实验，不计入97／101条回测分母。它支持实物运行与在线形变显示的定性结论，不单独计算毫米形变误差或响应时延。详细元数据见 [demonstration.json](../media/measured/demonstration.json)。
