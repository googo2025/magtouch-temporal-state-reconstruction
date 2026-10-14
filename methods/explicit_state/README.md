# 显式节点与磁片状态路线

固定主模型：**第138轮**。主要命题是在保留物理结构和模型弱几何参考时，实测磁场输入与监督如何使生成关系适应实物。

31维输入经GRU64生成联合状态，普通节点位移与25片磁片位姿分别读出。磁场损失直接依赖磁片位姿；普通节点仍由弱几何参考和共享历史表示约束。该路线的价值包括固定来源对照、完整97序列磁场回测和最终模型的实物形变显示。

- [独立中文论文](companion/paper/soft_magnetic_tactile_core_zh.pdf) · [独立英文论文](companion/paper/soft_magnetic_tactile_core_en.pdf)
- [中文补充](companion/paper/soft_magnetic_tactile_supplement_zh.pdf) · [英文补充](companion/paper/soft_magnetic_tactile_supplement_en.pdf)
- [论文入口及未来独立稿位置](paper/README.md) · [路线引用说明](CITATION.md)
- [模型源码](source) · [最终138统计](results/final138.json) · [来源对照](results/source_adaptation.json)
- [实物GIF](media/final138_real_demo_3x.gif) · [原79文件伴随资料](companion)

97条开发序列的池化磁场RMSE4.139 µT、MAE2.440 µT。开发集参与选模；低磁场误差不直接给出全部普通节点的实测位移精度。实物演示的模型身份已由实验者确认属于第138轮，不归属于共享529路线。

与[共享场路线](../shared_field/README.md)的关系是互补：这里检验固定状态表示下的实测适应，共享路线检验共同位移表示及不依赖所用弱教师的学习。联合论证见[联合论文](../../papers/joint/Magnetic_Supervision_main_zh.pdf)。
