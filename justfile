# Run these through the caller's run-heavy wrapper.
hlg-ootf-native source build output binary:
    python3 scripts/hlg_ootf_oracle.py --binary {{quote(binary)}} {{quote(source)}} {{quote(build)}} {{quote(output)}}

hlg-near-unity-check:
    cargo test --locked -p jxl --lib hlg_near_unity_ -- --test-threads=1
    cargo test --locked -p jxl --no-default-features --lib hlg_near_unity_ -- --test-threads=1

hlg-near-unity-broad-check:
    cargo test --locked -p jxl --lib -- --test-threads=1
    cargo test --locked -p jxl --no-default-features --lib -- --test-threads=1
    cargo clippy --locked -p jxl --all-features --lib --tests -- -D warnings
    cargo fmt -p jxl --check

# Focus broad checks on the changed color kernel and mounted XYB stage.
hlg-near-unity-affected-check:
    cargo test --locked -p jxl --lib -- color:: render::stages::xyb --test-threads=1
    cargo test --locked -p jxl --no-default-features --lib -- color:: render::stages::xyb --test-threads=1
    cargo clippy --locked -p jxl --all-features --lib --tests -- -D warnings
    cargo fmt -p jxl --check

global-squeeze-check:
    cargo test --locked -p jxl --test global_squeeze_grid -- --test-threads=1
    cargo test --locked -p jxl --no-default-features --test global_squeeze_grid -- --test-threads=1

decoder-fault-check fault output:
    python3 scripts/decoder_fault_evidence.py {{quote(fault)}} {{quote(output)}}
