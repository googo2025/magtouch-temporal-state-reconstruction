# 模型实现与复现边界 / Model implementation and limits

`source/model/ra_q_autograd.py`是最终138轮沿用的精确网络与解码器源码：31维输入、64维GRU状态、线性q输出，以及固定几何和外部磁场映射。q中平移为毫米、Euler角为弧度；`q_unit_scale`中的0.1仅在网络输出处应用，已保存q不得再乘0.1。编码按reset切断历史。

`source/model/objectives.py`提取了同一固定父模块的特征、损失和完整原生评价函数；函数体未改变，移除了私有路径、数据载入器及自动训练控制器。物理损失采用至多64个原生索引，弱几何目标不是实测形变真值。完整评价磁场保留原生时钟与全部有效时刻。普通柔性位移不直接进入磁场映射，磁片位姿进入。

这里只公开实现与已有汇总结果。调用这些函数仍需经授权的器件几何、磁化/传感器参数、基线、完整输入、弱参考和模型状态。本仓库不提供这些受限数组或权重，也不提供原私有控制器；因此不是一键训练/推理交付或完整fresh训练复现。静态语法与来源检查不等于新的科学数值验收。当前观察到的版本列表不是原训练环境锁定证明。

The exact adapter contains the inherited GRU-to-q model and fixed decoder. The shared objective/evaluation helpers retain their original function bodies; private loaders and operational controllers are excluded. Authorized geometry, parameters, baseline, arrays, weak references and model state are required to execute them. None are supplied or converted into another format to evade restrictions. No new training, inference, field calculation or geometric computation was performed for this publication checkout. The two physics files alone carry the explicit MIT grant; these additional implementation files retain project rights.
