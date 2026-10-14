# 一个仓库 两条路线与论文引用

两条路线可以相对独立地组织和引用，其共同科研主张是磁场监督能够通过可测磁响应学习并检验难测状态关系。它们的区别在状态结构和监督路径，互补性由正式对照与实际输出支持。

| 科学范围 | 核心命题与证据 | 资源入口 | 论文位置 |
| --- | --- | --- | --- |
| 共同磁场监督方法 | 物理结构、实测关系辨识、状态磁响应检验组成同一闭环；不同结构与训练路径共同验证可行性和效果 | [框架](../framework/README.md) | [联合中文稿](../papers/joint/manuscript_zh.md)摘要、引言、2.1、4.4、5及6 |
| 显式状态路线 | 保留弱几何参考与固定物理读出，通过输入／目标来源对照检验实测适应；97序列回测和138实物显示 | [显式目录](../methods/explicit_state/README.md) | [显式独立稿](../methods/explicit_state/companion/paper/soft_magnetic_tactile_core_zh.pdf)；联合稿2.2、4.3 |
| 共享场路线 | 同一位移函数生成材料与磁片运动；支撑与合法方向构造；无弱位移教师学习及共同预算组件实验 | [共享目录](../methods/shared_field/README.md) | [共享独立中文稿](../methods/shared_field/paper/Shared_Field_main_zh.pdf)与[英文稿](../methods/shared_field/paper/Shared_Field_main_en.pdf)；联合稿2.3、2.5、2.6、4.4及补充 |

**共同验证并不是直接比较谁的RMSE更低。**显式来源实验检验实测适应，共享组件实验检验所用教师依赖；二者与形变时序、对应磁场回测及显式实物运行共同支撑方法论。97／101条开发范围、掩码、聚合与容量保持各自定义。

两条独立研究稿已分别归档，显式篇围绕实测适应及显式状态实现组织，共享篇围绕表示耦合与无需所用弱教师的学习组织。共同装置和基础框架可以共同引用；各自方法、证据、结果与复现版本分别对应，联合稿保留为两条实现的统一论证。

根目录[引用说明](../CITATION.md)负责共同入口，两路线各自[Citation](../methods/explicit_state/CITATION.md)与[Citation](../methods/shared_field/CITATION.md)负责具体归属。未来同一仓库的各路线发布版本各自列资源范围，引用固定提交／版本而不是把持续变化的首页当作唯一身份。GitHub发布基于标签，参见[官方版本说明](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)。

本仓库收录联合稿及两路线独立稿；共享独立稿含中英正文、补充与完整可编辑源稿。没有新建两个仓库、创建未声明标签或重新训练与回测。
