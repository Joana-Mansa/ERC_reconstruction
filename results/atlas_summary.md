# Atlas inspection

Hard-label MNI152 template; no subject measurements or voxelwise probabilities.

- Shape: [182, 218, 182]; orientation: ['L', 'A', 'S'].
- Spacing: [1.0, 1.0, 1.0] mm; voxel volume: 1.0 mm³.
- Nonbackground labels: 496 (expected 496; pass: True).
- Hemisphere counts: {'left': 248, 'right': 248}.
- Matched bilateral pairs: 244; unpaired bases: [68, 209, 303, 365, 409, 444, 506, 567].
- Labelled template volume: 1578.096 mL.
- Validation issue rows: 8.

Equal hemisphere counts do not guarantee identical surviving structures.
All nonbackground classes are included, including white matter and labelled ventricular spaces.
Internal ctx-rh fragments do not override the outer prefix and numeric offset.

## Largest template regions

| Region | mL |
|---|---:|
| Left-white_matter_of_forebrain | 295.644 |
| Right-white_matter_of_forebrain | 290.655 |
| Left-molecular_layer_of_pva | 35.183 |
| Right-molecular_layer_of_pva | 33.847 |
| Left-granular_cell_layer_of_pva | 33.250 |
| Right-ctx-rh-superiorfrontal | 32.538 |
| Right-granular_cell_layer_of_pva | 32.102 |
| Left-ctx-rh-superiorfrontal | 29.320 |
| Left-ctx-rh-rostralmiddlefrontal | 25.080 |
| Right-ctx-rh-rostralmiddlefrontal | 24.567 |
