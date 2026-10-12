"""Generate the report from actual saved results, never anticipated outcomes."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import pandas as pd
from .common import sha256, write_json

def table(frame, columns):
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for row in frame[columns].to_dict("records"):
        lines.append("| " + " | ".join(f"{row[c]:.4f}" if isinstance(row[c], float) else str(row[c]) for c in columns) + " |")
    return "\n".join(lines)

def generate_report(root):
    root = Path(root)
    load = lambda name: json.loads((root / "results" / name).read_text())
    m, p, n, preflight = [load(name) for name in ["atlas_metadata.json", "synthetic_probability_summary.json", "SYNTHETIC_normative_summary.json", "official_preflight.json"]]
    volumes = pd.read_csv(root / "results/tables/region_volumes.csv")
    issues = pd.read_csv(root / "results/tables/label_validation_report.csv")
    unpaired = volumes.merge(issues[issues.status != "ok"][["label_id","status"]],on="label_id")
    metrics = pd.DataFrame(n["test_metrics"])
    figures = sorted((root / "results/figures").glob("*.png"))
    overlay = (root / "results/figures/atlas_T1_overlay.png").exists()
    alignment = load("reference_alignment.json") if overlay else None
    tests_path = root / "results/logs/pytest.xml"
    test_message = "Not recorded; run pytest before claiming validation."
    test_summary = None
    if tests_path.exists():
        tree = ET.parse(tests_path).getroot()
        suites = list(tree.iter("testsuite"))
        totals = {k: sum(int(s.attrib.get(k,0)) for s in suites) for k in ["tests","failures","errors","skipped"]}
        test_summary = totals
        test_message = f"{totals['tests']} tests; {totals['failures']} failures, {totals['errors']} errors, {totals['skipped']} skipped. See results/logs/pytest.xml."
    reference_text = (f"FSL MNI152 1 mm T1 reference downloaded from the official standard-data package. Its native grid matches the atlas: **{alignment['atlas_native_grid_matches']}**. Display uses RAS and {alignment['display_alignment']}. No estimated registration was performed between them.\n\n![Aligned T1 overlay](results/figures/atlas_T1_overlay.png)" if overlay else "T1 overlay unavailable in this saved run. No unrelated reference grid was substituted.")
    report = f"""# NextBrain research report

Prepared from executed outputs on 12 October 2026. **This is a partial reproduction using the distributed MNI derivative, with separate synthetic teaching experiments. It is not a reproduction of every experiment in the Nature paper.**

## 1. Research objective

Inspect a detailed anatomical atlas, quantify its template regions, explain registration and probability construction, and implement an interpretable demonstration of age-dependent volume modelling. The project provides a practical foundation for discussing a potential University of Girona PhD.

## 2. What NextBrain is

**Original publication:** NextBrain supplies histology-informed anatomical detail and a Bayesian MRI segmentation tool. The [paper](https://doi.org/10.1038/s41586-025-09708-2) reports roughly 10,000 sections from five hemispheres and 333 regions per hemisphere. Those are publication findings, not measurements repeated here.

The [interactive atlas](https://github-pages.ucl.ac.uk/NextBrain/) is a useful anatomical companion. The small [MNI derivative](https://github.com/compneurobilbao/nextbrain-mni-atlas) is one segmentation of a reference template. This project analyzes that derivative.

## 3. Anatomical atlas versus probabilistic atlas

A hard-label image stores one integer category per voxel. Integer 48 is an identifier, not a probability or an ordered measurement. A probability atlas instead stores a distribution over anatomical categories at each location. In the teaching experiment,

`P(L=k | x) = (1/N) sum_i 1[L_i_aligned(x)=k]`.

All categories, including background, must sum to one. A maximum-probability map keeps only the winning category and discards uncertainty. Original NextBrain priors and the simulated empirical frequencies are conceptually related but are not the same data or construction method.

## 4. How NextBrain was constructed

**Original method:** digitized histology was reconstructed in MRI-referenced 3D space, delineated and combined into a probabilistic anatomical representation. The companion model combines spatial priors and image intensities to segment new MRI. The historical reconstruction scripts remain in this fork; they were not run on raw specimens here. Background on acquisition and reconstruction is provided by [Mancini et al., 2020](https://doi.org/10.1038/s41598-020-69163-z) and [Casamitjana et al., 2022](https://doi.org/10.1016/j.media.2021.102265).

## 5. Role of image registration

Registration establishes anatomical correspondence; resampling evaluates that correspondence on a voxel grid. Their roles must remain distinct. A physical coordinate is obtained from the NIfTI affine, rather than guessed from array indices. Hard labels use nearest neighbours. An intensity image can use linear interpolation. Read [registration_explained.md](docs/registration_explained.md) for histology-to-MRI reconstruction, atlas-to-subject registration, label propagation and longitudinal alignment.

## 6. Dataset and software used in this reproduction

Actual inputs were the pinned MNI hard-label NIfTI and LUT (commit `27826640aa5d1644e135d8be99ae25194352428c`), plus a separately generated probability experiment and a separately generated age/volume table. No private patient images or large histological datasets were used. Provenance, SHA256 values and notices are in [data/provenance.json](data/provenance.json) and [data_and_license_review.md](docs/data_and_license_review.md).

The analyses ran with Python 3.10 in an isolated environment, NumPy, pandas, SciPy, NiBabel, matplotlib, scikit-learn and pytest. Direct dependencies and the complete resolved environment are recorded. The new package is independent of historical reconstruction dependencies.

{reference_text}

## 7. Atlas inspection results

**Directly reproduced public-data results:**

| Property | Observed |
|---|---|
| Dimensions | {m['shape']} |
| Storage orientation | {m['orientation']} |
| Display orientation | RAS, neurological convention |
| Voxel spacing | {m['voxel_spacing_mm']} mm |
| Storage type | {m['storage_dtype']} |
| Nonbackground regions | {m['nonbackground_regions']}; expected-count check = {m['expected_count_passed']} |
| Hemisphere counts | {m['hemisphere_counts']} |
| Bilateral pairs with both regions present | {m['matched_bilateral_pairs']} |
| Validation issue rows | {m['validation_issue_rows']} |

Every observed label has a LUT entry in this run. Eight labels lack the opposite-side counterpart; equal side totals do not imply identical surviving structures. These were reported, not forced into symmetric pairs:

{table(unpaired,['label_id','name','status'])}

The outer Left/Right prefix and numeric offset determine hemisphere. Inherited internal `ctx-rh` text in some names does not override them. LUT colours are reused; colour alone cannot uniquely identify all 496 labels.

## 8. Regional volume analysis

For region k, `V_k = n_k × |det(A_3×3)|` mm³ and `V_k/1000` mL. The determinant correctly handles anisotropic or sheared voxel grids. Here each voxel occupies {m['voxel_volume_mm3']:.3f} mm³.

The total labelled template volume is **{m['nonbackground_volume_ml']:.3f} mL**. This includes all nonbackground classes, including labelled white matter and ventricular spaces; it is not a grey-matter-only measurement. Median region volume is **{volumes.volume_ml.median():.4f} mL**, and the smallest is **{volumes.volume_ml.min():.4f} mL**. Some one-voxel structures have very limited spatial support at this resolution.

{table(volumes.nlargest(5,'volume_ml'),['name','volume_ml','voxel_count'])}

These are **atlas-template volumes**, not individual patient volumes. Left/right differences cannot establish population asymmetry. Missing-side labels are excluded from the bilateral scatter rather than replaced with zero.

![Largest template regions](results/figures/largest_20_regions.png)
![Matched left and right regions](results/figures/left_right_volumes.png)

## 9. Visual findings

![Three anatomical views](results/figures/atlas_three_view.png)

The cortical parcels, large forebrain white-matter classes and detailed subcortical/cerebellar components are visible. Many small labels are only a few voxels and cannot be resolved comfortably in a whole-brain slice. The distribution spans orders of magnitude:

![Volume distribution](results/figures/region_volume_histogram.png)

![Selected name-matched structures](results/figures/selected_structures.png)

Selected structures are illustrative LUT-name searches. For example, hippocampal components include CA fields, dentate layers and subiculum; amygdala and thalamic searches may include transition areas or pathways. They are **not complete, validated masks of the entire parent structure**. Exact selected labels are exported for inspection. Visual inspection demonstrates intelligible orientation and layout, not validated anatomical accuracy against histology.

## 10. Probabilistic atlas demonstration

**Synthetic results:** {p['subjects']} stylized 3D maps contain bilateral medial-temporal ellipsoids inside a brain-shaped support. Shape and translation variation are simulated with seed {p['seed']}. Known inverse integer translations return maps to a common grid without cropping. This is ground-truth alignment, not a learned clinical registration algorithm.

![Synthetic probabilities](results/figures/SYNTHETIC_probability_demo.png)

Normalization maximum error is {p['normalization_max_error']:.6g}. Entropy `H(x) = -sum_k P_k(x) log₂(P_k(x))` is low where assignments agree and high at variable boundaries. Mean entropy on the same union of simulated ROI supports is {p['good_mean_entropy_roi_support_bits']:.4f} bits with correct alignment and {p['poor_mean_entropy_same_roi_support_bits']:.4f} bits with residual translation errors.

![Synthetic registration uncertainty](results/figures/SYNTHETIC_registration_uncertainty.png)

This example illustrates a measurement mechanism: poor correspondence can inflate uncertainty. It supplies no evidence about real population variation. Original sparse-map inspection is an optional separate pathway, tested on a sparse fixture but not run on downloaded original NextBrain probabilities.

## 11. Official segmentation experiment or setup limitations

**Not executed.** CPU was selected by the user and is supported by current documentation. Missing prerequisites, rather than GPU capacity, blocked the official run: {'; '.join(preflight['blockers'])}. Ubuntu and Ubuntu-24.04 WSL were also inspected at their PATH and standard installation locations. No verified installed version or runtime resource requirement was available.

The [CPU setup guide](docs/official_segmentation_setup.md) and executable Python runner verify installed help before using named arguments, preserve logs, run hemispheres sequentially and provide output QC. No system software was installed and no license registration was submitted. No official runtime, patient segmentation or clinical volume result is claimed.

## 12. Age-dependent modelling demonstration

**Synthetic results:** {n['participants']} simulated participants, ages sampled between 20 and 90, have three arbitrarily scaled regional volumes. These values were not derived from the MNI labels or real people. The feasibility search did not establish a readily obtainable authorized regional-volume table without authentication; that bounded finding is documented separately.

Subjects were split into {n['split_subjects']['train']} training, {n['split_subjects']['calibration']} calibration and {n['split_subjects']['test']} test participants. A quadratic expected volume was fitted on training subjects. Six age bins of calibration residuals estimate SD, followed by a log-linear positive SD curve. Mean and variance estimation do not use test outcomes. Subject grouping also keeps repeated observations together if later supplied.

`z = (observed volume - expected volume at age) / estimated conditional SD`.

The shaded interval is an approximate **individual** range `mean ± 1.96 SD`, assuming Gaussian residuals. It is not a regression mean confidence interval. It omits parameter uncertainty and is not guaranteed to have exact nominal coverage. Test ages outside the common training/calibration age range have scores withheld.

![Synthetic age trajectories](results/figures/SYNTHETIC_age_trajectories.png)

{table(metrics,['region','evaluated_test_rows','rmse_ml','z_mean','z_sd','coverage_95'])}

![Synthetic held-out deviations](results/figures/SYNTHETIC_deviation_scores.png)

Coverage is imperfect, especially for the simulated caudate; passing implementation tests does not mean the fitted intervals are calibrated for every region. Age-bin QC and example individuals are saved. The simulation is cross-sectional. Inferring within-person aging would require repeated scans and a longitudinal model. The original NextBrain publication already includes age-dependent location/scale modelling; this teaching baseline does not reproduce those fits or claim that age modelling is a new extension.

## 13. Limitations

- This analyzes one hard-label template, not a cohort or all the original paper's findings.
- Fine structures at 1 mm can be fragile to interpolation, discretization and registration. Missing-side labels remain missing.
- Name searches are transparent but do not substitute for an anatomical hierarchy.
- Original probability channels, raw histology and official patient segmentation were not reproduced.
- Synthetic shape/volume variation has no clinical or biological evidential status.
- The age model omits sex, head size and scanner effects, uses a small calibration set and ignores parameter uncertainty.
- Source licenses are recorded separately; downloading public files does not establish unrestricted redistribution rights.
- Tests cover {test_message} They check computational invariants, not clinical validity. Windows execution was verified; a complete Linux pipeline run has not yet been verified.

## 14. Possible extensions for a University of Girona PhD

The next substantive step is an authorized MRI cohort with measured ages, official native-space segmentation and independent QC. Compare an age-independent prior with smoothly age-conditioned spatial probabilities, while controlling registration error and site effects. Develop regional normative models separately, evaluate held-out subjects/sites, and use repeated scans to study within-person change. The [age-specific proposal](docs/age_specific_atlas_proposal.md) distinguishes these questions and outlines validation. [Brain charts](https://doi.org/10.1038/s41586-022-04554-y) and [PCNtoolkit](https://github.com/predictive-clinical-neuroscience/PCNtoolkit) provide further methodological context. Align this proposal with the actual advertised Girona project before claiming institutional fit.

## References

1. Casamitjana et al. *A probabilistic histological atlas of the human brain for MRI segmentation.* Nature 648, 678–685 (2025). [DOI](https://doi.org/10.1038/s41586-025-09708-2).
2. Mancini et al. *A multimodal computational pipeline for 3D histology of the human brain.* Scientific Reports 10, 13839 (2020). [DOI](https://doi.org/10.1038/s41598-020-69163-z).
3. Casamitjana et al. *Robust joint registration of multiple stains and MRI for multimodal 3D histology reconstruction.* Medical Image Analysis 75, 102265 (2022). [DOI](https://doi.org/10.1016/j.media.2021.102265).
4. Bethlehem et al. *Brain charts for the human lifespan.* Nature 604, 525–533 (2022). [DOI](https://doi.org/10.1038/s41586-022-04554-y).
5. [Public MNI atlas](https://github.com/compneurobilbao/nextbrain-mni-atlas), [original reconstruction code](https://github.com/acasamitjana/ERC_reconstruction), [official FreeSurfer documentation](https://freesurfer.net/fswiki/HistoAtlasSegmentation), [interactive NextBrain atlas](https://github-pages.ucl.ac.uk/NextBrain/). Consulted 12 October 2026.
"""
    (root / "NEXTBRAIN_RESEARCH_REPORT.md").write_text(report,encoding="utf-8")
    status = f"""# Project status

## Implemented and executed

Phases 1–4: isolated Python environment, immutable atlas acquisition with provenance, NIfTI/LUT validation, physical volumes, bilateral comparison, atlas figures and an explicitly synthetic probability experiment. Phase 6: synthetic age model with independent subject training/calibration/test sets. Phases 7–8: report, explanations, proposal, tests and start guide. Phase 5: environment investigation and executable CPU setup/QC pathway only.

## Execution evidence

- `python scripts/run_research.py all`: atlas, synthetic probability, synthetic age modelling and official CPU preflight completed.
- `python scripts/run_research.py download --reference`: optional official FSL reference acquisition; overlay available in saved results: **{overlay}**.
- `python -m pytest -q --junitxml=results/logs/pytest.xml`: {test_message}
- Source sparse loader: fixture-tested only, not executed against the full original atlas.
- Official `mri_histo_atlas_segment_fireants`: not executed because prerequisites are absent.

## Downloaded data

{table(pd.DataFrame(json.loads((root/'data/provenance.json').read_text())['assets']),['path','bytes','sha256'])}

No private data or full histological datasets were downloaded. External raw data, archive caches, environments and licenses are excluded from Git. Synthetic NIfTIs and tables are identified by SYNTHETIC filenames.

## Generated figures ({len(figures)})

""" + "\n".join(f"- [{f.name}](results/figures/{f.name})" for f in figures) + f"""

## Scientific observations

Observed {m['nonbackground_regions']} regions, {m['matched_bilateral_pairs']} bilateral pairs, {m['validation_issue_rows']} unpaired label rows, no missing LUT entries; total labelled template volume {m['nonbackground_volume_ml']:.3f} mL. These are template-only results. Synthetic probabilities normalize exactly in this run. Simulated residual alignment increases entropy. Synthetic held-out individual interval coverage varies by region and is reported without claiming clinical validity.

## Outstanding work and exact blockers

- Official CPU inference: {'; '.join(preflight['blockers'])}. WSL checks did not find a standard installation. System installation and license registration were outside authorized execution rules.
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

Activate the venv first (Windows: `.venv\\Scripts\\Activate.ps1`; Linux: `source .venv/bin/activate`). `requirements-lock.txt` records the complete tested dependency resolution; `requirements.txt` pins direct dependencies. Internet is needed only for the source/reference download. `all` reuses existing files, checks hashes, and regenerates our result files. It does not install FreeSurfer or run official inference.
"""
    (root / "PROJECT_STATUS.md").write_text(status,encoding="utf-8")
    write_json(root / "results/output_manifest.json", dict(tests=test_summary, files=[dict(path=f.relative_to(root).as_posix(),sha256=sha256(f),bytes=f.stat().st_size) for f in sorted((root / "results").rglob("*")) if f.is_file() and f.name != "output_manifest.json"]))
