# 共享连续位移场路线引用

路线目录：methods/shared_field。主模型为纯磁场逐帧第529轮，完整开发评价101条；等域等序列RMSE2.822 µT，池化RMSE4.034 µT。

独立论文：**Magnetic Supervision of Soft Deformation through a Shared Continuous Displacement Field**。中文：**共享连续位移场中的磁场监督柔性形变学习**。

- [英文独立稿](paper/Shared_Field_main_en.pdf) · [中文独立稿](paper/Shared_Field_main_zh.pdf)
- [英文补充](paper/Shared_Field_supplement_en.pdf) · [中文补充](paper/Shared_Field_supplement_zh.pdf)
- [源码](source) · [最终529统计](results/final529.json) · [组件比较](results/matched274.json)
- [联合方法英文稿](../../papers/joint/Magnetic_Supervision_main_en.pdf) · [总引用规则](../../CITATION.md)

涉及共享位移表示、175探针运动、固定支撑、纯磁场学习或所用弱教师依赖时，引用本独立稿与实际仓库提交；涉及两条实现的共同磁监督框架时同时引用联合稿。作者、单位与真实论文DOI待研究者填写，不编造出版信息。尚未创建的建议Git标签不是实际引用版本。

本路线不继承显式模型的97序列口径或实测GIF身份。两条实现提供互补证据，不能由不同协议的误差直接判定结构胜负。
