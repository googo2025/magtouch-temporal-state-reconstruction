# 引用范围 Citation scopes

本仓库承载共同磁场监督框架及两条实现路线。代码仓库保持一个，科学论述和结果归属按范围引用；两条路线提供相互补充的证据，不被拆成互相否定的方法。

| 使用范围 | 当前论文或资料 | 代码与结果归属 |
| --- | --- | --- |
| 统一方法及两结构互补论证 | Physical Structure-Guided Magnetic Supervision for Soft Deformation Estimation | [联合稿](papers/joint/Magnetic_Supervision_main_en.pdf)与[共同框架](framework/README.md) |
| 显式节点／磁片状态、实测适应或实物演示 | Physics-prior-guided temporal deformation estimation for soft magnetic tactile sensing；必要时同时引联合方法稿 | [显式路线引用](methods/explicit_state/CITATION.md)，固定第138轮 |
| 共享连续场、共同位移函数、无弱教师学习 | Magnetic Supervision of Soft Deformation through a Shared Continuous Displacement Field；共同框架另引联合稿 | [共享路线引用](methods/shared_field/CITATION.md)，固定纯磁场逐帧第529轮 |

引用代码或结果时，同时注明实际公开仓库URL、路线目录和锁定提交SHA或已发布版本。仓库地址提供共同入口，目录确定引用哪条路线，固定版本确定实际复现哪套代码和结果。

当前独立显式稿与联合稿为项目科研稿，学术作者、单位、通讯信息及正式论文DOI尚待项目提供。本包没有捏造作者、DOI、期刊接收或尚未创建的Git标签。共享独立中英研究稿已收录；其作者、单位及正式出版信息同样待提供。

建议以后分别冻结`explicit-state-epoch138-v1`与`shared-field-epoch529-v1`路线版本，联合稿则记录使用的两套版本及共同仓库提交。这些名称目前是发布建议；实际引用以真正发布的提交、标签和出版信息为准。

GitHub可在仓库根目录识别本`CITATION.md`并提供引用入口；未来补齐作者与正式出版信息后可增加机器可读引用。参见[GitHub引用文件说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files)。
