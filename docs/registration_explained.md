# Registration in this project

Registration estimates a transformation that brings corresponding anatomy into alignment. Resampling evaluates an already chosen transformation on a requested grid. Matching shape or affine does not prove two images contain corresponding anatomy.

## 1. Histology-to-MRI reconstruction

Histological sections are two-dimensional samples of tissue that has been cut, mounted and stained. Their shape can change, sections may be torn, and stain contrast differs from MRI. Blockface photographs and ex vivo MRI provide three-dimensional references. Coarse block placement is followed by local deformation estimation. The historical repository contains those stages; this project does not execute them because it does not download the full specimens. See [Mancini et al., 2020](https://doi.org/10.1038/s41598-020-69163-z) and [Casamitjana et al., 2022](https://doi.org/10.1016/j.media.2021.102265).

## 2. Atlas-to-subject registration

Here the source is an already assembled anatomical atlas and the target is an individual MRI. A transformation accounts for global pose and local shape differences. The official NextBrain tool combines its anatomical prior with scan intensity information in a Bayesian segmentation. It is richer than copying the MNI template labels onto a patient. See [NextBrain](https://doi.org/10.1038/s41586-025-09708-2) and the [official segmentation instructions](https://freesurfer.net/fswiki/HistoAtlasSegmentation).

Write a forward map as `y = T(x)` from atlas to subject. To assign values on the target grid, a pull resampler usually evaluates the source at `T⁻¹(y)`. Confusing these directions displaces the labels. Physical coordinates use the affine: `[x,y,z,1]ᵀ = A [i,j,k,1]ᵀ`.

## 3. Label propagation

Once the transformation is known, labels can be transferred to another image. Use nearest-neighbour interpolation for hard labels; linear interpolation creates non-integer mixtures of identifiers. Intensities can use linear interpolation. Probability channels can use continuous interpolation, followed by checks for nonnegative values and normalization including background. Compose transforms and resample once when possible to limit aliasing.

Volumes measured in a warped standard-space image can change with the warp. For patient volumetry, count labels on the native segmentation grid using physical voxel volume, or apply a justified Jacobian correction. Do not treat template counts as patient measurements.

## 4. Longitudinal registration

Repeated scans from one participant should use an unbiased within-person reference and consistent segmentation/QC. Asymmetric registration to a baseline scan can bias estimated change. Split all scans of one participant into the same train, calibration or test set. Cross-sectional age differences mix age, cohort and selection effects; they are not individual aging rates.

## What was actually aligned here

The MNI atlas is converted from LAS storage to RAS display without changing physical locations. Optional FSL MNI152 T1 overlays use the same declared template coordinate frame; grid resampling alone is not presented as estimated registration. The synthetic experiment uses known inverse integer translations on stylized ellipsoids. These are ground-truth transforms from the generator, not a successful registration of real MRI. A second condition deliberately leaves residual translation error to show how spatial probabilities and entropy change.

QC should include orientation markers, world-coordinate agreement, boundaries of selected anatomy, inverse consistency, and deformation plausibility. A positive Jacobian and visual agreement are useful checks, but neither alone establishes correct fine-grained correspondence.
