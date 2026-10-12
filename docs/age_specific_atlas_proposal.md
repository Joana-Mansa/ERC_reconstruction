# Proposed age-specific NextBrain study

This is a proposed extension, not a result or a claim about a particular Girona laboratory's current project. Detailed anatomy, age-conditioned spatial probabilities, and regional normative trajectories answer different questions.

## Research question

Does accounting for age-dependent anatomy improve segmentation calibration and region-specific interpretation beyond one age-independent anatomical prior? Evaluate that question independently from whether regional volume varies with age.

## Cohort and measurements

Acquire an authorized multi-site MRI cohort with recorded age, sex, intracranial volume, scanner/site, health criteria and, where possible, repeat scans. Prespecify exclusions and document recruitment and age coverage. Run the version-pinned official segmentation in native space, retain its QC, and audit tiny structures and systematic failures. A healthy normative cohort must be defined explicitly; a mixed dementia cohort is not automatically a normal reference.

Segmentation does not create histological ground truth. High-resolution manual labels or independent expert assessment are needed to test accuracy. Preserve the original atlas label definitions and distinguish aggregate parent regions from their component parcels.

## Spatial probability model

Build an unbiased common frame, inspect atlas-to-subject registration and propagate native labels into that frame with nearest neighbours. For age `a`, a simple local estimate is

`P(L=k | x,a) = sum_i w_i(a) 1[L_i_aligned(x)=k] / sum_i w_i(a)`.

Weights can come from an age kernel or predefined bins. Include background so probabilities sum to one. Compare multiple smoothing widths using held-out subjects, and report effective sample size across age. Spatial probabilities combine anatomical variation, segmentation error and registration error; entropy does not isolate those mechanisms.

Age-specific templates can also be built from anatomy, but avoid circular evaluations where the same subjects construct and test the atlas. Smooth transitions across age are preferable to abrupt discontinuities. Validate sensitivity to registration regularization and examine atrophy-related warps and Jacobians.

## Regional normative model

Measure volumes on native grids. Model `V | age, sex, ICV, site` with interpretable splines or a location-scale distribution. Estimate both expected value and individual variability. Scanner effects and head size can otherwise masquerade as age effects. A z score uses conditional individual SD, not the standard error of the fitted mean.

Use subject-group train/calibration/test splits, a held-out site, and prospective replication. Inspect interval coverage, bias and residual scale within age/site/sex strata. Compare with a simple quadratic baseline, and treat non-Gaussian tails explicitly if needed. Hundreds of correlated labels require multiplicity control when testing biological hypotheses.

## Longitudinal extension

Use repeated MRI to distinguish within-person change from differences between people of different ages. A mixed-effects model can represent subject-specific intercepts/slopes; longitudinal registration should avoid favoring the baseline. Estimate measurement repeatability before interpreting small changes. All visits of a participant remain within one data split.

## Connection to your background

Histology-to-MRI reconstruction connects to your experience with 2D-to-3D registration. A useful first study would compare how uncertainty in correspondence changes apparent age-specific spatial probabilities and volume trajectories. Then test whether better registration actually improves independent anatomical validation, rather than only increasing apparent overlap.

## Relevant reading

- [Casamitjana et al., NextBrain, Nature 2025](https://doi.org/10.1038/s41586-025-09708-2): anatomical framework and existing aging analysis. Its aging analysis already models age-dependent location and scale; age modelling itself is not new.
- [Casamitjana et al., Medical Image Analysis 2022](https://doi.org/10.1016/j.media.2021.102265): multimodal histology registration.
- [Bethlehem et al., Brain charts, Nature 2022](https://doi.org/10.1038/s41586-022-04554-y): lifespan modelling reference.
- [PCNtoolkit](https://github.com/predictive-clinical-neuroscience/PCNtoolkit): normative modelling implementation and protocols.

Before calling this a Girona PhD proposal, compare it with the advertised project's actual aims and discuss cohort access, validation data, expected compute and supervisors' priorities.
