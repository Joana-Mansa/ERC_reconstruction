# Data, provenance, and license review

Reviewed 12 October 2026. Original reconstruction code and LICENSE.txt are retained. The new Python package is distributed under the repository's GPL-3.0 terms. External datasets do not acquire that license by being downloaded.

| Resource | What was checked | Decision |
|---|---|---|
| [MNI hard atlas](https://github.com/compneurobilbao/nextbrain-mni-atlas) | Pinned commit `27826640aa5d1644e135d8be99ae25194352428c`; NIfTI and LUT exist; repository has no explicit LICENSE | Analyze locally, retain immutable source, exclude raw downloads from Git. Do not claim GPL applies to these data. Confirm reuse terms with maintainers before redistributing source assets. |
| [ERC reconstruction](https://github.com/acasamitjana/ERC_reconstruction) | Actual config, dataset, scripts, src, utils and webpage directories; LICENSE.txt is GPL-3.0 | Preserve historical MATLAB/Python reconstruction; new package is independent. No histological source datasets downloaded. |
| [Original paper](https://doi.org/10.1038/s41586-025-09708-2) | Open-access article; CC BY-NC-ND 4.0 | Cite and explain the methods; do not copy or adapt its figures. All project figures are newly generated. Article terms are not automatically the terms of linked datasets. |
| [FSL standard data package](https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/public/noarch/) | Official package, 187.2 MB; SHA256 from package index | Optional download for noncommercial educational use; extract only MNI152_T1_1mm and any packaged license notices, exclude raw reference/archive from Git. Consult [FSL terms](https://fsl.fmrib.ox.ac.uk/fsl/docs/license.html). |
| [Official NextBrain files](https://freesurfer.net/fswiki/HistoAtlasSegmentation) | Wrapper uses atlas_simplified/size.npy and label_*.npz; actual source uses scipy sparse COO flattened rows | Separate single-map loader implemented and fixture-tested; original probability atlas not downloaded. License and label/geometry metadata must accompany later use. |

Checksums, URLs, asset sizes and source commit are recorded in `data/provenance.json`. `sha256` describes actual local file bytes. `canonical_sha256` normalizes CRLF to LF for source text only, so Git's Windows line-ending conversion does not break validation against the pinned raw Git blob. Binary NIfTI checks are byte-exact. The original source files are never rewritten to normalize them. Derived statistics and original research visualizations are distinguished from downloaded source assets. This review records observed notices; it does not establish an unrestricted license for the MNI derivative.

## Real age-and-volume data search

The search sought subject ages plus measured regional volumes, clear reuse terms, and a directly obtainable small table without authentication. This was a feasibility search, not an exhaustive systematic review.

| Candidate | Evidence | Why it was not used |
|---|---|---|
| [OASIS](https://sites.wustl.edu/oasisbrains/) | Official site provides request/access and data-use terms; cohort includes cognitive impairment | Access/terms and healthy-subject selection require further work. A convenient authorized regional-volume table was not established. |
| [HCP Aging / AABC](https://www.humanconnectome.org/study/hcp-lifespan-aging/data-releases) | Official site offers IDPs but requires BALSA registration and agreement | Does not meet the no-authentication criterion. |
| [OpenBHB](https://baobablab.github.io/bhb/) | Official site links imaging data through IEEE DataPort | No directly verified licensed age-plus-regional-volume table was obtained. |
| [IXI](https://brain-development.org/ixi-dataset/) | Public MRI and demographics, CC BY-SA 3.0 | MRI/demographics alone are not measured NextBrain regional volumes. Segmentation would be a separate analysis. |
| [PCNtoolkit](https://github.com/predictive-clinical-neuroscience/PCNtoolkit) | Open modelling code and protocols | A software license does not supply unrestricted rights to all training cohorts. |

**Decision:** use the explicitly simulated `data/synthetic/SYNTHETIC_age_volumes.csv`. No age is inferred from an image, and no real participant data are published. No claim is made that suitable open regional-volume datasets do not exist. The implementation exposes data validation, subject-group splitting, fitting and prediction functions for later authorized tables; the default CLI deliberately runs only the labelled simulation.
