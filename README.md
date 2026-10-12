# NextBrain research reproduction

Start with [START_HERE.md](START_HERE.md), [the executed research report](NEXTBRAIN_RESEARCH_REPORT.md) and [PROJECT_STATUS.md](PROJECT_STATUS.md).

This fork preserves the original reconstruction pipeline below and adds an independent, CPU-compatible Python project. It analyzes the public MNI hard-label atlas and keeps synthetic probability/age experiments explicitly separate from public-data results. It does not claim a completed official patient segmentation or reproduce every result of the original paper.

## Quick start

Python 3.10–3.13 (executed here with 3.10). Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/run_research.py download --reference
.\.venv\Scripts\python.exe scripts/run_research.py all
.\.venv\Scripts\python.exe -m pytest -q --junitxml=results/logs/pytest.xml
.\.venv\Scripts\python.exe scripts/run_research.py report
```

Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_research.py download --reference
python scripts/run_research.py all
python -m pytest -q --junitxml=results/logs/pytest.xml
python scripts/run_research.py report
```

`--reference` downloads an optional 187 MB official FSL standard-data package, verifies its checksum and extracts only the matching MNI152 T1. Skip it for an atlas-only analysis. `all` uses pinned atlas files, generates CSV/JSON/PNG/NIfTI results and checks official CPU prerequisites; it never starts FreeSurfer inference. Existing source files are not modified. Repeated runs overwrite only this project's generated outputs.

The script entry point works without installing the historical reconstruction environment. For an optional console command, `pip install -e .` installs only `nextbrain_research`, then `nextbrain-research all` is equivalent. The direct dependency pins and fully resolved `requirements-lock.txt` are separate so the tested environment can be reconstructed.

## Project layout

```text
src/nextbrain_research/  new analysis package
scripts/run_research.py portable analysis entry point
tests/                  physical volume, label integrity, probability and leakage tests
docs/                   registration, data/license review, CPU setup, research proposal
data/source_atlas/      untouched external atlas (ignored in Git)
data/reference/         external MNI T1 (ignored in Git)
data/synthetic/         explicitly simulated datasets and NIfTIs
data/processed/         reserved for later processed data (ignored in Git)
results/figures/        generated publication-resolution PNGs
results/tables/         volumes, validation and synthetic model scores
results/logs/           execution and test evidence
```

Use actions `atlas`, `probability`, `normative`, `preflight` or `report` independently. `--root PATH` redirects the project inputs/results. `official --input ... --output ... --threads 4` is a later CPU-only official run after installing prerequisites; see [the exact setup workflow](docs/official_segmentation_setup.md). Source probability maps have their own opt-in loader, not a fabricated conversion from hard labels.

## Interpretation and licensing

Regional counts are **template volumes**, not patient measurements. Synthetic datasets contain no real participants and have no clinical evidential value. Statistical prediction intervals describe estimated individual variability, not confidence in the regression mean. The new code follows the retained GPL-3.0 license; third-party data retain their own terms. Source downloads, licenses and environment files are excluded from Git. See [the provenance and license review](docs/data_and_license_review.md).

The atlas, probability demonstration and age models were executed on Windows. Linux commands are provided but the full Linux analysis pipeline has not been executed here. Original histology reconstruction remains a distinct, much larger workflow.

---

# Original NextBrain reconstruction pipeline

This repository contains the scripts for 3D histology reconstruction.



<p align="left">
<img src="https://github.com/acasamitjana/ERC_reconstruction/blob/main/webpage/gif-EX9-19.gif?raw=true" alt="drawing" width="350"/>
</p>

## Data
You can download the project's data here: doi.org/10.5522/04/24243835. More details about the data acquisition can be found in [1]

## Code
The 3D reconstruction code is place in the _scripts_ directory and is organised as follows:
* **Initialisation**: Matlab code used to initialize the linear reconstruction via stack of blockface photographs
* **Linear step**: it contains several scripts to run the linear registration step between all blocks and the MRI. It is used to accomodate all blocks in the 3D space minimising both the overlap and separation between blocks. The final outcome is the matching MRI slice to each of the histology sections (LFB and H&E)
* **Non-linear step**: this non-linear step is used to refine the alignment between each MRI and histological slices (LFB and H&E) such that the overall reconstruction is accurate and smooth. More details about this step can be found in [2]
* **Reconstruction**: final reconstruction scripts that read the results from the previous steps and original data to compute the final reconstruction avoiding multiple resampling steps.
* **Pipeline**: scripts running the whole 3D reconstruction pipeline for each case

### Pre-processing
This Matlab code is used to initialize the linear reconstruction via stack of blockface photographs. Some of the manual work has already been done. This folder contains a README file with more instructions about the data used and the processing steps.
Main scripts:

1. _RegisterCutfaceToBlockfaceAllRegions.m_: registers the face of each block to the top/bottom blockface photo stack.
2. _InitializeWithCutPhotos*.m_: independent scripts for each structure (cerebrum, cerebellum and brainstem) that use information from previous steps to initialize the location of each block.
3. _createDownsampleGapBlocks.m_: registerts LFB sections to the corresponding blockface photo to generate initial LFB blocks.

### Linear reconstruction
The goal is to slice the MRI volume so that each LFB and H&E sections have their equivalent MRI slice. For that, we run a hieararchical linear registration algorithm to accomodate each LFB block in a single ``LFB volume'' that closely matches the MRI volume. Each MRI voxel is assigned to a given block by using a distance transform to deal with ambiguities

Main scripts:
1. _train_BT.py_: compute affine parameters for each block.
2. _predict_BT.py_: compute the aligned LFB blocks.
3. _generate_block_masks_easy.py_: assign an histology block to each MRI voxel.
4. _generate_virtual_MRI_blocks.py_: re-slice the MRI according to each block.
5. _generate_slices.py_: prepare MRI, LFB and H&E sections to for non-linear reconstruction. The different operations include resampling at a given resolution (typically 0.1mm) and independent linear alignment of each histology section to their MRI counterpart.

### Non-linear reconstruction
The remaining difference between each MRI, LFB and H&E section is non-linear. We run the ST3 algorithm presented in [2] to compute the final deformation field for each histology section.  The inverse deformation is used to propagate freesurfer parcellations to the manual delineations of the cortex on the LFB sections. If, for whatever reason, a block is not processed through the pipeline, we compute the registration from the linear alignment to the MRI.

1. _initialize_graph.py_: compute pairwise intermodal registration (MRI, LFB and H&E) and between neighbouring MRI slices.
2. _solve_st.py_: solve the ST3 algorithm given the pairwise registrations from step 1.
3. _group_flow.py_: compute the final deformation field for each histology section as the concatenation of affine and non-linear deformation fields.
4. _mosaic_registration_missing_block.py_: final registration of un-processed blocks (typically due to small number of sections or tissue, such that the most inferior brain-stem blocks)
5. _propagate_aparc.py_: propagate freesurfer parcellation from MRI to histology.
6. _merge_cortical_labels.py_: merge subocrtical labels with cortical parcellation.



## Bibliography
[1] Mancini, Matteo, et al. "A multimodal computational pipeline for 3D histology of the human brain." Scientific reports 10.1 (2020): 13839.

[2] Casamitjana, Adrià, et al. "Robust joint registration of multiple stains and MRI for multimodal 3D histology reconstruction: Application to the Allen human brain atlas." Medical image analysis 75 (2022): 102265.
