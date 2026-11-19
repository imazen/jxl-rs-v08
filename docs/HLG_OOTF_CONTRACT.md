# HLG OOTF near unity

Part 1 clause E.1's HLG interpretation includes the intensity-dependent OOTF
when converting between scene and display light. The selected approximation
here matches unmodified libjxl v0.12.0 `HlgOOTF_Base`: only exponents in the
closed interval [-0.01, 0.01] use unity. The previous 0.1 cutoff also suppressed
nontrivial corrections. The cutoff is a reference implementation choice,
not a numeric threshold quoted from the format specification.

The native component observer evaluates the original v0.12 header without
reimplementing its OOTF. It records compiler arguments and source/header/ELF/table
hashes. The 78 positive-luminance vectors cover both signs, both deadband edges,
two luminance-weight sets and three swatches; table SHA256 is
`ef25c1c3c9adccb028f70b2bdcc4d4d2ac9355a9b1b6a5ee826b2eef84b02ae1`.
At exponent -0.09899998, the old kernels leave red 0.125 unchanged where the
native component returns 0.14388174. Both old Rust kernels fail this control.

The retained 124-byte file is a 9x3 RGB HLG F32 encode at 255-nit white,
represented as hexadecimal text. Its source swatch is [0.125, 0.25, 0.5].
Native v0.12 original-profile output is uniform at
[0.12495632469654083, 0.24998974800109863, 0.4999362528324127].
The released primary decoder returns
[0.13115248084068298, 0.2623854875564575, 0.5236957669258118] before repair.
The fixture/provenance files retain stream, native output and producer identities.
Every visible sample is checked against the native values; this is complete
file rendering, not header acceptance. Native component and pixel bounds are
separate and neither is changed to accept a failure.

`just hlg-near-unity-check` selects the controls explicitly in default and minimal
builds. Regenerate component observations only with an explicit pinned v0.12
source/build and a new executable path on an executable filesystem:
`just hlg-ootf-native <source> <build> <new-archive> <new-local-binary>`.
Builds and tests on shared hosts use the caller's resource wrapper.

The targeted source/reference changes preserve arithmetic outside the changed
cutoff and preserve the zero-luminance handling. Positive, interior swatches do
not qualify negative luminance, every HDR profile, external CMS behavior or all
platforms. The historical near-black HLG discrepancy remains a separate finding.
Kernel region execution and native platform results retain separate verdicts;
passing test counts are not coverage evidence.

This source is pinned to released jxl 0.8.0 commit
`9a08ca643fd2d01f803dd0be6a5bebc9cc11e597`. The actual production SIMD kernel and
its test references use the same corrected cutoff. Direct tests call every
available compiled descriptor; unavailable descriptors are not local evidence.
The complete-file and component controls pass in default and minimal builds.
The full library, strict lint/format and platform checks remain in progress.
The test rendering driver originates in Imazen's jxl-encoder test support and is
reused under this repository's BSD-3-Clause license.
