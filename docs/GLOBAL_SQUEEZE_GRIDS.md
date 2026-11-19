# Global inverse-squeeze intermediates

A valid modular channel can grow beyond one group while both inverse-squeeze
inputs still occupy global buffers. The intermediate keeps the maximum grid
kind of its inputs. A later coded LF or HF residual introduces its own grid
when it participates in the inverse transform. Output size alone does not
identify that transition. Part 1 G.4.2 governs coded channel placement;
intermediate inverse buffers are not additional coded HF channels.

The previous scheduler promoted such intermediates to HF. On a 2x16449 Gray8
stream with 128-pixel groups, a global input has vertical shift 8 while its
inverse output has shift 7. An HF view of the input has height `128 >> 8 = 0`;
reading it panics at the image row bound. The transposed case has the same
problem along the other axis. Both retained fixtures reproduce that panic
on the pinned 0.8.0 source before the repair.

The text fixtures and independently retained source tiles come from Imazen's
zenjxl-decoder repair `0ad1a3e639315a26965021ee45fbcd1eb6017d84`, reused under
this repository's BSD license. Their original production encoder and native
v0.12 geometry/pixel controls are recorded under
[encoder issue 144](https://github.com/imazen/jxl-encoder/issues/144).
The regression compares every grayscale code and opaque alpha byte in both
orientations. Default and minimal builds pass after the propagation repair.
No integer output tolerance is substituted for exact source samples.

`just global-squeeze-check` runs both configurations. The evidence runner
retains exact source, executable and completed profile identities. The fault
runner restores the old grid promotion and requires the actual row-bound
panic rather than accepting build failure as a reproduced defect. Mutation,
region and platform qualification retain separate verdicts. This selected
schedule does not establish every legal squeeze schedule or full conformance.

Restoring the old promotion reproduces both row-bound panics after the repair.
Exact executable
`1117bb0bb12aaac430fdfff6e2aabf400bee263272b626a4cd9f55c31a270f77`
and completed profile
`9f2b50988f0133146b0aa3e472c8d8506877e8f929641cf7bbf52ee1e068931f`
cover 5/5 mapped propagation regions, without LLVM mapping diagnostics.
The earlier integration run was not instrumented and supplies pixel evidence
only; its missing profile was not accepted as coverage. The source region
fraction excludes other transform arms, allocation and scheduling decisions.
