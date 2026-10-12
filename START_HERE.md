# Start here

**NextBrain** links fine histological anatomy to MRI segmentation. This project inspected its public MNI hard-label derivative, produced template volume tables and anatomical plots, and ran two clearly synthetic demonstrations. It did not reconstruct the original specimens or produce a new patient segmentation.

## Inspect these three figures first

1. [Three anatomical views](results/figures/atlas_three_view.png): learn how the hard-label atlas is spatially organized.
2. [Synthetic probability demonstration](results/figures/SYNTHETIC_probability_demo.png): see what averaging aligned labels adds beyond a hard segmentation.
3. [Synthetic age trajectories](results/figures/SYNTHETIC_age_trajectories.png): distinguish an expected volume from individual variability.

Then read [the research report](NEXTBRAIN_RESEARCH_REPORT.md), [project status](PROJECT_STATUS.md), and the label validation CSV. The 496 labels include eight without an opposite-side partner; only 244 structures form matched bilateral pairs.

## Most important Python files

- `scripts/run_research.py`: one entry point for all analyses.
- `src/nextbrain_research/atlas.py`: lookup parsing, hemisphere validation and physical volume calculation.
- `src/nextbrain_research/probability.py`: synthetic alignment, probabilities, entropy and separate optional original sparse-map reader.
- `src/nextbrain_research/normative.py`: subject-group separation, age-dependent mean, conditional SD and held-out z scores.
- `src/nextbrain_research/official.py`: later official CPU execution and output QC when prerequisites are installed.

## Run again on Windows

From the repository folder in PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts/run_research.py all
.\.venv\Scripts\python.exe -m pytest -q --junitxml=results/logs/pytest.xml
.\.venv\Scripts\python.exe scripts/run_research.py report
```

On a fresh clone, first create a venv and install `requirements.txt`. Run `python scripts/run_research.py download --reference` once to obtain the optional FSL reference, then `all`. Linux activation and commands are in the README. The external source atlas and T1 are deliberately downloaded rather than embedded in Git.

## Study next

Read [registration_explained.md](docs/registration_explained.md) before interpreting atlas-to-patient transfer. Next, follow [official_segmentation_setup.md](docs/official_segmentation_setup.md) for CPU inference and [age_specific_atlas_proposal.md](docs/age_specific_atlas_proposal.md) for a possible research direction. Pay special attention to registration error, native versus warped volume, independent validation and the difference between cross-sectional age patterns and longitudinal change. Compare the proposal with the actual Girona PhD project's aims.
