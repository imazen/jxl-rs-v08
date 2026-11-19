# Changelog

## [Unreleased]

### QUEUED BREAKING CHANGES

### Fixed

- Keep inverse-squeeze intermediates global when both inputs are global,
  recovering tall and transposed grayscale streams without row-bound panics.

- Apply HLG OOTF outside the pinned v0.12 unity deadband, including near-unity
  exponents at 255-nit white; retain the 0.8.0 public API.
