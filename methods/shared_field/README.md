# 共享连续位移场路线

固定主模型：**纯磁场逐帧第529轮**。主要命题是同一个空间函数生成材料位移与磁片运动，能否使磁场监督通过共同参数学习无需弱位移教师的状态表示。

21维输入经零前态GRU32单步编码，与三维名义坐标连接后经35→64→64→3空间网络查询位移。25片共175个探针由同一函数生成运动，局部差分与正交化构造磁片位姿，再通过固定物理读出重建磁场。距离支撑约束固定面；有限观测仍不保证每个空间点独立可辨识。

- [当前共享路线的论文入口](paper/README.md) · [路线引用说明](CITATION.md)
- [源码](source) · [529轮完整101序列统计](results/final529.json)
- [共同274轮组件比较](results/matched274.json) · [完整学习曲线标量](results/learning_histories.json)
- [原冻结触头留出扩展](results/tip_holdout_extension.json)
- [当前中文联合论文](../../papers/joint/Magnetic_Supervision_main_zh.pdf) · [英文联合论文](../../papers/joint/Magnetic_Supervision_main_en.pdf)

101条开发序列的等域等序列RMSE2.822 µT、池化RMSE4.034 µT、MAE1.811 µT。共同预算对照支持无需本实验所用弱位移教师的学习。输入、评分掩码和归一化口径与显式路线不同，不据97／101汇总直接判定结构胜负。

共享场独立中英文研究稿已收录于本路线paper目录，完整论证表示耦合、支撑构造、教师依赖及组件实验；联合稿保留共同方法的互补论证。现有实物GIF属于显式138，不冒作共享529的实机验收。

[独立中文正文](paper/Shared_Field_main_zh.pdf) · [独立英文正文](paper/Shared_Field_main_en.pdf) · [中文补充](paper/Shared_Field_supplement_zh.pdf) · [英文补充](paper/Shared_Field_supplement_en.pdf)
