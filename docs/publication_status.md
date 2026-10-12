# GitHub publication

Requested destination: https://github.com/Joana-Mansa/ERC_reconstruction

Research branch: `codex/nextbrain-research`. Original reconstruction code is preserved; source atlas downloads, reference MRI, caches, environment and license files are excluded.

The research implementation was pushed successfully on 12 October 2026. First implementation commit: `19ffd3e`.

- [Research branch](https://github.com/Joana-Mansa/ERC_reconstruction/tree/codex/nextbrain-research)
- [Start guide](https://github.com/Joana-Mansa/ERC_reconstruction/blob/codex/nextbrain-research/START_HERE.md)
- [Research report](https://github.com/Joana-Mansa/ERC_reconstruction/blob/codex/nextbrain-research/NEXTBRAIN_RESEARCH_REPORT.md)

Local final validation: **32 tests passed**, fresh pinned source acquisition and cross-checkout provenance validation passed, and 14 figures were generated. The complete core analysis also ran in an empty local result folder.

[Ubuntu and Windows GitHub Actions checks](https://github.com/Joana-Mansa/ERC_reconstruction/actions/runs/38233075420) both passed for analysis commit `772def8`. Those checks independently downloaded the atlas, regenerated results in empty folders, executed the test suite and generated the report. The optional FSL T1 reference/overlay was verified locally on Windows and deliberately excluded from CI. The actual remote result is stored in `results/ci_validation.json`.

No pull request was opened or branch merged. Official CPU segmentation remains blocked by the prerequisites documented in the project status. A first CI run exposed a cross-checkout text-provenance issue; that issue was fixed, regression-tested and verified by the successful run linked above.
