# Physics-prior-guided temporal deformation estimation for soft magnetic tactile sensing

## Abstract

Soft magnetic tactile sensing should recover the changing shape of the compliant body and the motion of its embedded magnets, rather than only a contact-point trajectory. We address sparse magnetic observations, high-dimensional deformation and history dependence with a joint state estimator driven solely by causal magnetic history. A recurrent network generates ordinary-node displacements and the poses of 25 magnets. Fixed geometry and magnetic-field models provide structural priors, model-generated weak references support geometric learning, and measured magnetic fields train the state mapping to the physical device. The method does not require an exact inverse solution of a high-fidelity material and contact model; inference requires neither commanded coordinates, tip identity nor CAD. Replay of real experimental sequences displays estimated three-dimensional deformation, magnet motion and corresponding field reconstruction. Across 97 complete development sequences and 233791 jointly valid native time points, the selected model achieves magnetic RMSE of 4.139 µT, MAE of 2.440 µT and absolute-residual P95 of 8.577 µT. Matched-age comparisons with unchanged physics support joint adaptation to measured inputs and targets. The outcome is a temporal deformation state that can be generated, displayed and checked against measured fields; its three-dimensional display is not a calibrated measurement of deformation accuracy.

Keywords: soft magnetic tactile sensing; temporal deformation estimation; physics prior; magnetic history; observation consistency.

## 1 Introduction

Soft magnetic tactile sensors read the field induced by magnetic elements moving inside compliant material, enabling sensing through opaque encapsulation and occluded contact [1]. The central difficulty is recovering a time-varying, high-dimensional compliant state from a few Hall channels. A tip-center trajectory cannot describe local body deformation, and the pose of one magnet does not represent the motion of the entire magnet array and silicone. We ask whether deployable magnetic-history inputs can jointly generate three-dimensional body deformation and embedded-magnet states while allowing those states to be checked against real observations.

Making an exact inverse solution of high-fidelity physics a deployment prerequisite places material parameters, contact conditions and simulation-to-device mismatch in the upfront modeling stage. We instead use physics-prior-guided learning: fixed models retain device geometry, magnet motion and the field observation relation, while a recurrent network learns the history-to-state mapping. Model-generated geometry is a weak reference, whereas measured magnetic fields constrain observation consistency. Prior work has investigated magnetic-to-simulated-deformation mappings [2] and tactile simulation transfer [6]. Our focus is the realization and evaluation of temporal compliant geometry, magnet poses and field explanation within the same state, not a novelty claim for generic components.

Complete deformation measurement also requires clear spatial coverage. A contacting tip occludes the contact region; the Hall board and support restrict backside observation; and external surface measurement does not automatically establish internal material-point correspondence. Specialized optical structures can measure visible regions [7], but our device has no complete per-node deformation ground truth. We therefore separate temporal shape display from magnetic replay: the former shows what the estimator actually generates, and the latter tests whether those states explain a measurable real signal. Evaluation uses complete sequences and their native clocks, rather than substituting a few attractive frames for aggregate evidence.

## 2 Physics-prior-guided temporal state estimation

### 2.1 Causal magnetic-history encoding

Five tri-axial Hall units provide 15 magnetic channels. The input comprises fields relative to the unloaded baseline, 15 validity flags and the native time interval, giving 31 dimensions. A 64-dimensional GRU [3] retains history dependence:

\[
\mathbf x_t=[\mathbf b_t/s_B,\mathbf v_t,\Delta t_t]\in\mathbb R^{31},\qquad
\mathbf h_t=\operatorname{GRU}_{\theta}(\mathbf x_t,\mathbf h_{t^-}).
\]

The training scale is fixed at 104.11355991798682 µT. Invalid readings are not treated as zero field. Hidden state resets at sequence onset, an explicit reset or a change in baseline identity. Inference uses only magnetic history, validity, time and the unloaded baseline; commanded XYZ, tip identity, CAD and weak-reference labels are not inputs. The recurrent state is phenomenological memory of historical response, not an identified material constant.

### 2.2 One state generates compliant deformation and magnet motion

The readout generates a 23352-dimensional joint state: 23202 ordinary-node displacement components and 150 pose components for 25 magnets, each with three translations and three rotations. Ordinary-node displacements generate compliant geometry, while nodes belonging to each magnet share a shape-preserving transformation. This local rigid approximation applies only to individual magnets of 5 mm diameter and 1 mm thickness; neither silicone nor the full array is treated as rigid. Displacements use millimeters, rotations use radians and the original fixed output scaling. The nominal mesh contains 13010 nodes.

Magnet poses from that same state enter a fixed field mapping:

\[
\widehat{\mathbf b}_t=H(\mathbf p_t)
=\sum_{m=1}^{25}\mathbf B_m(\mathbf c_{m,t},\mathbf R_{m,t};\mathcal G,\mathcal M)-\mathbf B_0.
\]

Fixed quantities include device geometry, Hall layout and magnetization parameters. Cylindrical-magnet fields use 24-point thickness quadrature and elliptic integrals, with an established axisymmetric-field basis [4]. The physical model constrains the state-to-observation relation. There is no independent field-output head bypassing magnet states, and inference does not perform an exact inverse solution of high-fidelity contact simulation.

### 2.3 Weak geometric references and measured-observation constraints

Model geometry supplies weak references, while measured fields require estimated magnet states to explain real responses. These constitute the implemented composite objective:

\[
\mathcal L=\operatorname{MSE}((\widehat{\mathbf b}-\mathbf b^{\rm target})/s_B)
+\operatorname{MSE}((\widehat{\mathbf u}-\mathbf u^{\rm weak})/0.5\mathrm{mm})
+\operatorname{MSE}((\widehat{\mathbf c}-\mathbf c^{\rm weak})/0.5\mathrm{mm})
+0.1\operatorname{MSE}(\widehat{\mathbf R}-\mathbf R^{\rm weak}).
\]

The field depends directly on magnet poses, not ordinary-node displacement:

\[
H(\mathbf d,\mathbf p)=H(\mathbf p),\qquad
\frac{\partial H}{\partial\mathbf d}=0.
\]

Ordinary deformation consequently also relies on weak geometric references and shared representations. Low magnetic error alone does not establish uniqueness or accuracy of every node displacement. Weak references need not be high-accuracy deformation labels of the real device, but reasonable geometry, sensor layout and a field mapping remain necessary. Using approximate physics does not relax numerical computation, units, baseline or validity requirements.

![Joint temporal state and physical observation path](../../figures/method_en.png)

Figure 1. Joint state estimation and physical observation path. A shared forward path generates compliant displacements and magnet poses from magnetic history, then reconstructs the field through a fixed physical mapping. Offline model-generated weak references enter training only, not deployment inputs. Ordinary nodes and magnet poses have different observation roles; shape preservation of individual magnets does not imply rigidity of the compliant body.

## 3 Experimental protocol

Table 1. Data roles at the complete-sequence level

| Data role | Sequences | Purpose |
| --- | ---: | --- |
| Parameter fitting | 346 | Update model parameters |
| Internal TRAIN monitoring | 16 | Check model weak-reference consistency |
| Development validation | 97 | Complete measured-field evaluation and selection |

The 362 TRAIN sequences contain 4343 existing valid weak-reference slots. The 97 development sequences span small-flat, hemisphere and original-round seen shape domains: 234195 native time points, 233791 jointly valid five-Hall points and 3506865 magnetic scalars. Sequence roles are separated, but development data have been used for selection and display and are not a sealed blind test. Aggregate RMSE uses all jointly valid native scalars:

\[
\operatorname{RMSE}_B=\sqrt{\frac{\sum_{j,t,c}m_{jt}(\widehat b_{jtc}-b_{jtc})^2}{15\sum_{j,t}m_{jt}}}.
\]

Training uses the original composite objective and AdamW [5], with model-reference pretraining followed by measured-field adaptation. Low-learning-rate continuation uses 1×10⁻⁴ and weight decay of 1×10⁻⁴. Evaluation ends at epoch 160; epoch 138 is selected by field RMSE over all 97 development sequences. Late training loss decreases without corresponding validation improvement, so neither training loss nor the integer endpoint establishes full convergence. Complete curves and matched-age optimizer comparisons are supplied in the supplement rather than expanded into per-epoch narrative.

The main deformation and replay figures use the same preregistered hemisphere display sequence and saved final-model outputs. Geometry is shown only at saved native times, without interpolating a complete geometric trajectory. Field replay retains the full native clock, validity and baseline. Hall3 XYZ is a fixed main-text display subset; all 15-channel evaluation and further full waveforms remain in aggregate statistics and the supplement. No gain, baseline or time shift is fitted.

## 4 Results

### 4.1 Three-dimensional deformation and magnet states driven by magnetic history

Figure 2 presents the principal output: magnetic history from a real touching sequence is converted to changing compliant-surface displacements and 25 magnet states, rather than merely a tip XYZ trajectory. Four saved states share the same model, XYZ millimeter scale, view and color scale, with displacement factor 1. Spatial ordinary-node displacement and magnet translation and rotation all arise from one joint state.

![Estimated three-dimensional deformation during a real experimental sequence](../../figures/deformation_en.png)

Figure 2. Estimated states of the preregistered hemisphere sequence at 2.539, 62.839, 73.658 and 90.891 s. Gray denotes nominal geometry, color denotes estimated vertical displacement, and black outlines denote magnets from the same state. The times are the first valid saved slot, the existing maximum estimated-displacement slot, the existing maximum sampled-field-residual slot and the last slot. Coordinates, view, the common color scale over all nine sequences and displacement factor are unchanged. This is estimated deformation, not measured deformation ground truth.

The temporal views make spatial deformation and embedded-magnet motion inspectable outputs. They are not a plot of commanded tip motion, and no command or tip geometry drives inverse inference. Magnets can move differently; the compliant body is not rigidified as a whole. A native-clock animation allows inspection of successive saved states, without claiming that geometry has been saved at every native time point.

### 4.2 Real magnetic replay and aggregate performance

Figure 3 connects the states in Figure 2 to a measurable signal through measured fields, physical reconstruction and raw residuals from the same real sequence. The left column checks magnitude, sign and dynamic following; the right retains errors rather than showing only overlapping traces. Replay inputs and outputs come from native experimental records, not idealized simulated waveforms.

![Magnetic replay and residuals from the same real sequence](../../figures/field_replay_en.png)

Figure 3. Complete native Hall3 XYZ replay for the hemisphere sequence in Figure 2. Black is measured field, blue is final-model reconstruction through the fixed physical mapping, and the right column is reconstructed minus measured field. The sequence has 3092 native points and 3091 jointly valid points, with no fabricated missing values. The fixed Hall3 display subset does not alter the aggregate denominator covering all 15 channels.

Table 2. Final-model magnetic replay over all development sequences

| Evaluation scope | Sequences | Jointly valid points | RMSE µT | MAE µT |
| --- | ---: | ---: | ---: | ---: |
| All development sequences | 97 | 233791 | 4.139 | 2.440 |
| Small flat | 30 | 49151 | 1.984 | 1.443 |
| Hemisphere | 52 | 126419 | 4.749 | 2.731 |
| Original round | 15 | 58221 | 4.062 | 2.648 |

The final model has native-scalar absolute-error P95 of 8.577 µT, equal-sequence macro RMSE of 2.803 µT and sequence-RMSE P95 of 6.573 µT. All 97 sequences remain in aggregate statistics; one displayed sequence cannot replace them. Error scales differ across seen shape domains, and residuals remain around local extrema and recovery. These magnetic metrics are not deformation accuracy in millimeters.

### 4.3 Measured adaptation with unchanged physical priors

To test whether the method relies solely on the generating model, four combinations continue for five epochs from the same pretrained state, changing only the source of magnetic inputs and reconstruction targets. Physics, architecture, weak references and scoring denominators remain fixed. Matched-age results are shown in Table 3.

Table 3. Input and supervision source comparison with one physical model

| Magnetic input | Reconstruction target | RMSE µT | MAE µT |
| --- | --- | ---: | ---: |
| Generated | Generated | 13.636 | 7.758 |
| Generated | Measured | 19.090 | 10.758 |
| Measured | Generated | 22.833 | 13.235 |
| Measured | Measured | 9.144 | 5.763 |

Joint measured adaptation reduces field RMSE by 32.94% relative to generated-input/generated-target continuation, whereas either one-sided replacement degrades performance. Within this finite budget, fixed physics requires joint adaptation to real inputs and supervision; geometric proximity to generated references does not guarantee real observation performance. This supports the role of data adaptation with unchanged priors, not robustness to arbitrary physical-model errors. These results are not ranked against the differently aged final model.

## 5 Discussion

An engineering characteristic of the method is that deployment does not require an exact inverse solution of high-fidelity physics. Basic geometry, magnet motion and field relations provide interpretable structure; measured data train the state mapping to actual responses; and model geometry is only a weak prior. This reduces the need to make precise identification of the entire material and contact process a prerequisite, but does not remove physics. Incorrect layouts, magnetization directions or field mappings may still affect estimation. Without physical-parameter perturbation experiments, the conclusion is temporal state generation and real-field consistency under the fixed priors used here, not unchanged deformation accuracy under arbitrary low-accuracy models.

Shape display, geometric weak-reference comparison and field replay address output form, prior proximity and explanation of real observations, respectively. Because ordinary displacements do not directly enter the present field mapping, independent visible-region or magnet-pose references are still needed to strengthen high-dimensional deformation validation. The 97 sequences are exposed development data; one inherited seed does not establish multi-seed significance; and three seen shape domains do not demonstrate unseen-tip generalization. Final-model hardware latency and long-term reliability have not been independently accepted, so results from older deployed models are not mixed into this evaluation.

## 6 Conclusion

We realize joint three-dimensional compliant deformation and magnet-motion estimation driven only by causal magnetic history, connecting the same state to real experimental observations through a fixed physical field reconstruction. The central outcome is a temporal state chain that can be generated, displayed and replayed, rather than only a tip trajectory or an unconstrained field-output fit.

Across all 97 development sequences, magnetic RMSE is 4.139 µT, MAE is 2.440 µT and absolute-error P95 is 8.577 µT. Temporal shape views and real native waveforms show the concrete outputs, while matched-age comparisons with unchanged physics support joint measured adaptation. The method does not require an exact inverse solution of high-fidelity simulation. Its current evidence comprises estimated deformation and field observation consistency; measured dense-deformation accuracy requires independent reference validation.

## References

1. Bhirangi R, Hellebrekers T, Majidi C, Gupta A. ReSkin: versatile, replaceable, lasting tactile skins. PMLR 164:587–597, 2022. [Original paper](https://proceedings.mlr.press/v164/bhirangi22a.html).
2. Lin X, Lin G, Liu R, Wang A, Lou Y. MPM-based simulation and bounded-error compression of material points for magnetic tactile sensors. Frontiers in Robotics and AI 13:1817251, 2026. [Original paper](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2026.1817251/full).
3. Cho K, et al. Learning Phrase Representations using RNN Encoder–Decoder for Statistical Machine Translation. EMNLP:1724–1734, 2014. [Original paper](https://aclanthology.org/D14-1179/).
4. Derby N, Olbert S. Cylindrical Magnets and Ideal Solenoids. American Journal of Physics 78:229–235, 2010. [Author manuscript and publication identifiers](https://arxiv.org/abs/0909.3880).
5. Loshchilov I, Hutter F. Decoupled Weight Decay Regularization. arXiv:1711.05101, revised 2019. [Author manuscript](https://arxiv.org/abs/1711.05101).
6. Church A, Lloyd J, Hadsell R, Lepora NF. Tactile Sim-to-Real Policy Transfer via Real-to-Sim Image Translation. PMLR 164:1645–1654, 2022. [Original paper](https://proceedings.mlr.press/v164/church22a.html).
7. Yuan W, Dong S, Adelson EH. GelSight: High-Resolution Robot Tactile Sensors for Estimating Geometry and Force. Sensors 17(12):2762, 2017. [Original paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC5751610/).
