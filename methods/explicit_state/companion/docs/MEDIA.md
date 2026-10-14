# 最终模型回测媒体

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
