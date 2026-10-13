# 依赖与环境上下文

资料校验入口只使用Python标准库。仓库不捆绑数值库、字体、FFmpeg或其他二进制。

| 已记录上下文 | 观察到的版本 |
| --- | --- |
| 训练基础安装上下文 | torch 2.14.0，numpy 2.4.6，scipy 1.17.1，matplotlib 3.8.0，Pillow 12.2.0 |
| 已保存显示输出上下文 | numpy 2.4.6，scipy 1.17.1，matplotlib 3.10.8，Pillow 12.3.0 |
| 原视频编码工具 | FFmpeg 6.1.1，GPL配置，libx264 |

这些是已观察的安装元数据，不是原训练环境锁文件，也不是完整传递依赖清单。`requirements-display-observed.txt`仅记录显示模块的观察版本，不代表已验证全新环境安装或新的图片／媒体制作。

第三方许可各自适用：[PyTorch](https://github.com/pytorch/pytorch/blob/main/LICENSE)、[NumPy](https://numpy.org/doc/stable/license.html)、[SciPy](https://github.com/scipy/scipy/blob/v1.17.1/LICENSE.txt)、[Matplotlib](https://matplotlib.org/stable/project/license.html)、[Pillow](https://pillow.readthedocs.io/en/stable/about.html#license)、[FFmpeg](https://ffmpeg.org/legal.html)。这些链接及已保存的首notice审查不构成全部传递版权已闭合的声明。

原图使用的Noto字体软件适用SIL OFL 1.1，Debian打包条款另行区分；字体文件不在本包。Windows字体的可编辑嵌入元数据不等于字体软件可再分发，亦不捆绑。生成的论文和图像与字体软件本身分开处理。
