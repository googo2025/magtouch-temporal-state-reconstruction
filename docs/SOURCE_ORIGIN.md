# 两份物理模块的来源说明

代码内容和有限公开检索支持“项目专用、自主实现经典方法”的判断，未发现直接复制公开库的证据；这不是法律作者身份或零借用代码的证明。项目所有者已确认两份源码属于项目原创并许可MIT公开。

`rigid_mesh.py`负责归档Hex8几何、普通节点位移与25个磁片六自由度运动的映射，包含欧拉旋转一阶／二阶导数、稀疏Jacobian和几何Hessian链式项。它是专用几何和运动学模块，不是完整硅胶本构、接触或力平衡求解器。欧拉旋转和链式法则是经典方法，稀疏矩阵与旋转表示使用[SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.transform.Rotation.html)。

`fast_magnetic.py`通过圆电流环的完全椭圆积分表达与轴向Gauss–Legendre求积计算有限圆柱外场，再做磁片姿态变换、叠加和传感器读出。它调用[SciPy椭圆积分](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.ellipk.html)和[NumPy求积节点](https://numpy.org/doc/stable/reference/generated/numpy.polynomial.legendre.leggauss.html)，这些基础数值实现不是项目自写。文件头自述独立实现，仍只是作者声明。

有限对照中，[Magpylib官方轴向圆柱源码](https://raw.githubusercontent.com/magpylib/magpylib/main/src/magpylib/_src/fields/field_BH_cylinder.py)采用无量纲端点的Bulirsch cel表达，接口和实现流程与本项目的轴向求积／K和E环场实现不同。此差异只支持这一个对照，不排除来自其他未索引来源的借用。六次限定检索没有取得可证明直接复制的匹配；检索无结果不证明原创。

建议表述：项目自主实现的几何／刚体运动与有限圆柱磁场计算模块，基于经典物理公式和NumPy／SciPy数值工具。不要表述为两套全新物理理论或所有数值算法从零原创。若需更强的作者来源证明，应补首版提交、设计推导和代码生成／改编记录。
