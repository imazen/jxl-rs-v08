# Pinned decoder control

This checkout keeps the jxl 0.8.0 API/source baseline. Do not substitute a newer
upstream version when validating the pinned encoder dependency.

## Known Bugs

The former HLG 0.1 OOTF deadband loses a visible near-unity correction at
255-nit white. The SIMD candidate and reference helpers now match v0.12's
closed 0.01 deadband. Kernel and complete-file controls pass in default/minimal
builds; broad/platform/region qualification remains in progress.
[Contract and evidence](docs/HLG_OOTF_CONTRACT.md).

The pinned 0.8 source also promotes a global inverse-squeeze intermediate to
HF from output size alone. Both tall/transposed retained fixtures panic before
repair and recover every gray/alpha byte afterward in default/minimal builds.
[Grid contract](docs/GLOBAL_SQUEEZE_GRIDS.md). Mutation/regions/platforms remain
separately qualified; the interrupted full library campaign is incomplete.
