# Explicit Node and Magnet State Route

Frozen main model: **epoch 138**. This route tests measured adaptation of generated relations while retaining physical structure and weak model geometry.

A 31-input GRU64 reads out ordinary-node displacement and 25 magnet poses. Magnetic loss directly depends on poses; ordinary nodes retain weak geometry and common-history constraints. Evidence includes fixed-source comparisons,97-sequence replay and physical operation of the final model.

- [Independent English paper](companion/paper/soft_magnetic_tactile_core_en.pdf) · [Chinese paper](companion/paper/soft_magnetic_tactile_core_zh.pdf)
- [English supplement](companion/paper/soft_magnetic_tactile_supplement_en.pdf) · [Chinese supplement](companion/paper/soft_magnetic_tactile_supplement_zh.pdf)
- [Paper entry](paper/README.md) · [Citation](CITATION.md)
- [Source](source) · [Final138 summaries](results/final138.json) · [Source adaptation](results/source_adaptation.json)
- [Physical GIF](media/final138_real_demo_3x.gif) · [Byte-exact 79-file companion](companion)

Across 97 DEV sequences, pooled field RMSE is 4.139 µT and MAE 2.440 µT. DEV participated in selection; magnetic error is not direct dense measured displacement accuracy. Physical demonstration is directly confirmed as epoch 138 and is not attributed to shared epoch 529.

The [shared-field route](../shared_field/README.en.md) complements measured adaptation with coupled representation and learning without the examined weak teacher. See the [joint paper](../../papers/joint/Magnetic_Supervision_main_en.pdf).
