# Official NextBrain segmentation: CPU execution path

The user explicitly selected CPU when GPU resources are insufficient. GPU availability is not the blocker here. Native Windows has no verified official executable; Ubuntu and Ubuntu-24.04 WSL checks found no executable on PATH or installation in the inspected standard locations. No license at the checked environment/default locations or original atlas_simplified files were available. No official segmentation was attempted or fabricated. WSL currently exposes approximately 7.6 GiB RAM; the host has about 15.65 GiB and an RTX 3050 with 6144 MiB VRAM. Sufficient runtime memory has not been established for the absent software.

The current [official instructions](https://freesurfer.net/fswiki/HistoAtlasSegmentation) support CPU. Their command has **named arguments**. The MNI atlas repository documents an older positional invocation from its generation environment; do not interchange them.

## Prerequisites to arrange on Linux or WSL

1. Install a compatible current FreeSurfer development build following [official installation instructions](https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall). This project does not install system-level software.
2. Obtain your own free license through that page, set `FS_LICENSE` or place it under `FREESURFER_HOME`, and never commit it.
3. Source `SetUpFreeSurfer.sh` in that shell. Verify build stamp and save `mri_histo_atlas_segment_fireants --help` for the installed version.
4. Follow the installed wrapper's download instructions for [atlas_simplified.zip](https://ftp.nmr.mgh.harvard.edu/pub/dist/lcnpublic/dist/Histo_Atlas_Iglesias_2023/atlas_simplified.zip). It expects `size.npy` and `label_*.npz` in `FREESURFER_HOME/python/packages/ERC_bayesian_segmentation/atlas_simplified`. Follow any additional model-download prompts, including the current preprocessing tool's model requirement. These files were not downloaded here.
5. Use an authorized 3D MRI. The optional downloaded FSL MNI152 T1 is a legal educational template example under its terms, **not a patient's scan**. For individual segmentation use a cohort's authorized T1 and respect its access agreement.

## Executable CPU workflow

From the repository root in the prepared Linux environment:

```bash
python3 -m venv .venv-linux
source .venv-linux/bin/activate
pip install -r requirements.txt
python scripts/run_research.py preflight
python scripts/run_research.py official \
  --input data/reference/MNI152_T1_1mm.nii.gz \
  --output results/official/mni_cpu --threads 4
```

The wrapper checks license existence and atlas files, verifies the installed help, and runs left then right sequentially with `--device cpu`. It refuses to overwrite existing segmentations. This setup path is implemented but has not been validated end-to-end with an installed FreeSurfer. If a particular release changes options, the help check fails before inference; adapt only after inspecting that release's documentation.

The underlying named-argument pattern, once verified on the installed version, is:

```bash
mri_histo_atlas_segment_fireants --i INPUT_SCAN --o OUTPUT_DIRECTORY \
  --device cpu --side left --mode invivo --threads 4
mri_histo_atlas_segment_fireants --i INPUT_SCAN --o OUTPUT_DIRECTORY \
  --device cpu --side right --mode invivo --threads 4
```

The Python runner records runtime, build, input checksum, command configuration, return codes and per-hemisphere logs. After success it validates actual NIfTI outputs, recomputes native-grid volumes and creates nearest-neighbour label overlays on the input MRI. Inspect `QC_REPORT.md`, `quality_control.json` and the overlays manually. Do not assume 496 labels: the original hemisphere output uses the original label identifiers and a different resolution from the MNI derivative.

If RAM is insufficient, the documented `--skip` option can reduce estimation memory, but changes must be recorded and validated. Do not claim that a 6 GB GPU or a 16 GB host guarantees success. CPU execution can be slow; monitor memory and save logs. More RAM on an approved server is a later option, not a paid resource requested by this project.

## Original probability-map pathway

`probability.load_source_sparse_probability` reads one `label_*.npz` as scipy COO rows of a flattened C-order volume with dimensions from `size.npy`, matching the inspected FreeSurfer source. The CLI can inspect one authorized local map:

```bash
python scripts/run_research.py source-probability \
  --source-directory /authorized/atlas_simplified \
  --source-file label_001.npz \
  --output results/source_probability_summary.json
```

The filename is not assumed to be the anatomical identifier. Obtain the official mapping and affine before interpreting a channel or overlaying it. A complete probability-normalization check needs all channels, including background. This optional loader was tested using a synthetic sparse fixture only; it is not a reproduced analysis of the full source probability atlas.
