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

# Explicit caller-provisioned stream/native plane, with a fresh output directory.
alpha-native-replay stream native output features:
    python3 scripts/alpha_plane_replay_evidence.py {{quote(stream)}} {{quote(native)}} {{quote(output)}} {{quote(features)}}

alpha-wide-storage-attribution stream native output:
    python3 scripts/alpha_storage_attribution.py {{quote(stream)}} {{quote(native)}} {{quote(output)}}

alpha-edge-native-cases cjxl djxl replay output:
    python3 scripts/alpha_edge_native_cases.py {{quote(cjxl)}} {{quote(djxl)}} {{quote(replay)}} {{quote(output)}}

squeeze-next-border-check:
    cargo test --locked -p jxl --lib squeeze_next_average_ -- --test-threads=1
    cargo test --locked -p jxl --no-default-features --lib squeeze_next_average_ -- --test-threads=1
    cargo clippy --locked -p jxl --all-features --lib --tests --example squeeze_alpha_replay -- -D warnings
    cargo fmt -p jxl --check

squeeze-next-border-evidence output:
    python3 scripts/hlg_ootf_evidence.py Cargo.toml {{quote(output)}} --package jxl --filter squeeze_next_average_

squeeze-next-border-fault direction output:
    python3 scripts/squeeze_border_fault_evidence.py {{quote(direction)}} {{quote(output)}}
