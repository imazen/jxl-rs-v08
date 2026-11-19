# Inverse-squeeze next-average border views

A finer output tile can consume averages from a coarser input grid. The next
average comes from that grid's packed border. Its perpendicular coordinate
must retain the current tile's offset: horizontal squeeze selects the matching
rows, and vertical squeeze selects the matching columns. The packed border's
four-sample axis remains unchanged. Both i16 and i32 storage use the same view.

The previous caller passed the entire border and read from its perpendicular
origin. An independently encoded native v0.12 control and an encoder stream
both reproduce sixteen wrong alpha codes at 2049x2048/alpha distance25, starting
at (2044,2040): primary155 versus native154. Scalar and SIMD builds agree on
the wrong result. Forcing wide storage does not remove it. This is a border
view defect, rather than a demonstrated integer-width or SIMD arithmetic defect.

Selecting the matching border slice removes every code mismatch in both full
streams and a sparse native control in default and minimal builds. Thirty
native controls cover both orientations, full/restricted alpha patterns,
LF/HF boundaries and small negative controls; all complete alpha planes agree.
These selected controls do not establish every legal squeeze schedule.

The permanent fixtures are native v0.12 streams represented as hexadecimal
text, with their complete decoded alpha codes compressed as text run lengths.
Alpha is deliberately lossy; the expectation is the native decoder's delivered
plane, not the uncompressed source. The horizontal stream is2639bytes, SHA256
`fc328f5061ba6ac2885e88e4f5ac56514c3f538ad3f330587bb8b99c446af010`;
the transposed stream is2698bytes, SHA256
`fb9b647764156a878a8ae544ece1d5e54f932a81e9edfb8b9345300ed3d32fb7`.
Their raster is constant RGB64/128/192 and zero alpha except a4x4 lower-right
window from the retained `(17*x + 29*y) mod256` pattern, transposed with the image.
The native commands select distance1, effort3, responsive1, alpha distance25
and one worker. All tools are pinned v0.12.0 a7a9c78.

The regression checks complete color rendering and every native alpha code
with both storage widths, both rendering pipelines, and whole/37-byte input
chunks. Packed-border component controls check both orientations, nonzero
perpendicular offsets, short extents and absent borders. Default and minimal
runs pass; strict all-feature library/test/example Clippy and scoped formatting
pass (`issue144-queue60-v1`,83seconds, peakRSS1.00GiB, minimum available18076MiB).
These are test-wrapper resource observations, not decoder performance.
Restored-fault sensitivity, exact region mapping and fresh platform CI remain
separate qualification steps. No public API, encoded bytes, tolerance or
established expectation changes.

Supporting records under the encoder issue144 artifact directory:
`primary-alpha-q55-*` (failing scalar/SIMD complete planes),
`primary-alpha-q56-wide-attribution-v1` (unchanged result and exact source restore),
`primary-alpha-q58-*` (fixed complete planes),
`primary-alpha-q59-{horizontal,vertical}-v1` (native controls), and
`primary-alpha-fixtures-v1` (text-fixture provenance).
