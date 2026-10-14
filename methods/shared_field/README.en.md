# Shared Continuous Displacement Field Route

Frozen main model: **pure-field framewise epoch 529**. This route tests whether one spatial function generating material and magnet motion supplies a common magnetic-supervision path without the weak displacement teacher examined.

A 21-input zero-state GRU32 step joins three nominal coordinates for a 35→64→64→3 network. The same function moves 175 probes over 25 magnets; differences and orthogonalization construct poses for fixed physical readout. Distance support enforces the fixed surface, while finite observations do not identify each spatial point independently.

- [Paper entry](paper/README.md) · [Citation](CITATION.md)
- [Source](source) · [Complete 101-sequence final529 summaries](results/final529.json)
- [Matched 274 components](results/matched274.json) · [Complete learning scalars](results/learning_histories.json)
- [Frozen tip-holdout extension](results/tip_holdout_extension.json)
- [English joint paper](../../papers/joint/Magnetic_Supervision_main_en.pdf) · [Chinese joint paper](../../papers/joint/Magnetic_Supervision_main_zh.pdf)

Across 101 DEV sequences, equal-domain equal-sequence RMSE is 2.822 µT, pooled RMSE 4.034 µT and MAE 1.811 µT. Matched-budget comparisons support learning without the examined teacher. Sets, masks and normalization differ from explicit states and do not permit a 97/101 structural leaderboard.

The independent bilingual shared-field research paper is available in the paper directory, developing coupling, support, teacher dependence and component evidence. The joint paper retains the common framework argument. The physical GIF belongs to explicit epoch 138 and is not shared epoch 529 hardware validation.

[Independent English paper](paper/Shared_Field_main_en.pdf) · [Chinese paper](paper/Shared_Field_main_zh.pdf) · [English supplement](paper/Shared_Field_supplement_en.pdf) · [Chinese supplement](paper/Shared_Field_supplement_zh.pdf)
