# Project status

## Implemented and executed

Phases 1–4: isolated Python environment, immutable atlas acquisition with provenance, NIfTI/LUT validation, physical volumes, bilateral comparison, atlas figures and an explicitly synthetic probability experiment. Phase 6: synthetic age model with independent subject training/calibration/test sets. Phases 7–8: report, explanations, proposal, tests and start guide. Phase 5: environment investigation and executable CPU setup/QC pathway only.

## Execution evidence

- `python scripts/run_research.py all`: atlas, synthetic probability, synthetic age modelling and official CPU preflight completed.
- `python scripts/run_research.py download --reference`: optional official FSL reference acquisition; overlay available in saved results: **True**.
- `python -m pytest -q --junitxml=results/logs/pytest.xml`: 31 tests; 0 failures, 0 errors, 0 skipped. See results/logs/pytest.xml.
- Source sparse loader: fixture-tested only, not executed against the full original atlas.
- Official `mri_histo_atlas_segment_fireants`: not executed because prerequisites are absent.

## Downloaded data

| path | bytes | sha256 |
|---|---|---|
| data/source_atlas/nextbrain_wholebrain_MNI152_1mm.nii.gz | 586329 | 0fd00a035070d26cf848c6bb4b36d409ab1bb355c9186f0e1faba6793d54bdab |
| data/source_atlas/nextbrain_wholebrain_MNI152_1mm_lut.txt | 28183 | f2c2353fdf703a2afb6c4c3026383aeb8c8cd922ca83fd9d3c5add90adcd6896 |
| data/source_atlas/README.md | 4780 | f9bae95e66dfe5a355a4a85f7182fb04869aa501f3c7e003c671cfed664eeeb6 |
| data/reference/MNI152_T1_1mm.nii.gz | 10963667 | d1f03e160c2548592a01d98d44d7e0ffa8a8ef58bc9b07d26369e214ba170edb |

No private data or full histological datasets were downloaded. External raw data, archive caches, environments and licenses are excluded from Git. Synthetic NIfTIs and tables are identified by SYNTHETIC filenames.

## Generated figures (14)

- [atlas_axial.png](results/figures/atlas_axial.png)
- [atlas_coronal.png](results/figures/atlas_coronal.png)
- [atlas_sagittal.png](results/figures/atlas_sagittal.png)
- [atlas_T1_overlay.png](results/figures/atlas_T1_overlay.png)
- [atlas_three_view.png](results/figures/atlas_three_view.png)
- [largest_20_regions.png](results/figures/largest_20_regions.png)
- [left_right_volumes.png](results/figures/left_right_volumes.png)
- [region_volume_histogram.png](results/figures/region_volume_histogram.png)
- [selected_structures.png](results/figures/selected_structures.png)
- [SYNTHETIC_age_trajectories.png](results/figures/SYNTHETIC_age_trajectories.png)
- [SYNTHETIC_deviation_scores.png](results/figures/SYNTHETIC_deviation_scores.png)
- [SYNTHETIC_multiple_subjects.png](results/figures/SYNTHETIC_multiple_subjects.png)
- [SYNTHETIC_probability_demo.png](results/figures/SYNTHETIC_probability_demo.png)
- [SYNTHETIC_registration_uncertainty.png](results/figures/SYNTHETIC_registration_uncertainty.png)

## Scientific observations

Observed 496 regions, 244 bilateral pairs, 8 unpaired label rows, no missing LUT entries; total labelled template volume 1578.096 mL. These are template-only results. Synthetic probabilities normalize exactly in this run. Simulated residual alignment increases entropy. Synthetic held-out individual interval coverage varies by region and is reported without claiming clinical validity.

## Outstanding work and exact blockers

- Official CPU inference: Official FreeSurfer command not on PATH; No license at FS_LICENSE or FREESURFER_HOME/license.txt; Original atlas_simplified probability files unavailable. WSL checks did not find a standard installation. System installation and license registration were outside authorized execution rules.
- Full original probabilistic-atlas analysis and histological reconstruction: source files not downloaded; loader alone is not a reproduction.
- Real-cohort normative validation: no suitable directly verified no-authentication age-plus-regional-volume table obtained during the bounded feasibility search. Synthetic demonstration used by explicit task fallback.
- Linux end-to-end validation: implementation is portable but was executed on Windows only.
- GitHub publication status is recorded separately in `docs/publication_status.md` after an actual push attempt.

## Reproduce

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python scripts/run_research.py download --reference
python scripts/run_research.py all
python -m pytest -q --junitxml=results/logs/pytest.xml
python scripts/run_research.py report
```

Activate the venv first (Windows: `.venv\Scripts\Activate.ps1`; Linux: `source .venv/bin/activate`). `requirements-lock.txt` records the complete tested dependency resolution; `requirements.txt` pins direct dependencies. Internet is needed only for the source/reference download. `all` reuses existing files, checks hashes, and regenerates our result files. It does not install FreeSurfer or run official inference.
