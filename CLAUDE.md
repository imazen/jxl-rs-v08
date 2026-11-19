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

Grayscale default/minimal source-code recovery and restored-fault checks pass;
the instrumented propagation expression covers 5/5 mapped regions without
diagnostics. Strict all-feature library/test Clippy and format pass. The full
primary library campaign remains incomplete and platform verdicts are separate.

The coarser-grid next-average border view is repaired in50c65e45. Original
native/encoder streams reproduce the same sixteen wrong alpha codes in scalar
and SIMD builds before the repair; wide storage alone does not repair them.
Default/minimal complete-plane controls now pass, including both storage widths,
both rendering pipelines and37-byte chunks. Strict all-feature library/test/
example lint and formatting pass. Restored horizontal/vertical offset faults both fail at runtime; the exact
source restores afterward. The completed profile observes20/20 view regions
and6/6 caller-window regions; broader scheduling/allocator failures are outside
that fraction. Default/minimal Shuttle and the final ordinary/lint continuation
pass with the existing full-stream harness's ten-million-step scheduler budget.
Fresh-platform verdicts remain separate. [Border contract](docs/SQUEEZE_BORDER_VIEWS.md).
