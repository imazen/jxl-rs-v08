//! Native HLG deadband vectors evaluated through actual SIMD kernels.
use super::*;
fn check<D: SimdDescriptor>(d: D) {
    d.call(|d| {
        for (index, line) in include_str!("hlg_ootf_v012.tsv").lines().enumerate() {
            let v: Vec<f32> = line.split('\t').map(|x| x.parse().unwrap()).collect();
            assert_eq!(v.len(), 10);
            let result = hlg_ootf_inner_vec(d, D::F32Vec::splat(d,v[0]),
                [v[1],v[2],v[3]].map(|x|D::F32Vec::splat(d,x)),
                [v[4],v[5],v[6]].map(|x|D::F32Vec::splat(d,x)));
            for (channel, output) in result.into_iter().enumerate() {
                let mut samples=vec![0.0;D::F32Vec::LEN];output.store(&mut samples);
                for observed in samples {
                    assert!(observed.is_finite() && (observed-v[7+channel]).abs()<=0.000002,
                        "native HLG row {index}, descriptor {d:?}, channel {channel}: {observed} vs {}, exponent {}",v[7+channel],v[0]);
                }
            }
        }
        for exponent in [-0.01_f32,0.0,0.01] {
            let values=[0.125_f32,0.25,0.5];
            let result=hlg_ootf_inner_vec(d,D::F32Vec::splat(d,exponent),
                [0.2126,0.7152,0.0722].map(|x|D::F32Vec::splat(d,x)),
                values.map(|x|D::F32Vec::splat(d,x)));
            for (channel, output) in result.into_iter().enumerate() {
                let mut samples=vec![0.0;D::F32Vec::LEN];output.store(&mut samples);
                assert!(samples.iter().all(|&x|x==values[channel]),"closed HLG deadband endpoint {exponent}");
            }
        }
    });
}
#[test]
fn hlg_near_unity_ootf_matches_native_on_available_tiers() {
    check(jxl_simd::ScalarDescriptor::new().unwrap());
    #[cfg(all(target_arch = "x86_64", feature = "sse42"))]
    if let Some(d) = jxl_simd::Sse42Descriptor::new() {
        check(d);
    }
    #[cfg(all(target_arch = "x86_64", feature = "avx"))]
    if let Some(d) = jxl_simd::AvxDescriptor::new() {
        check(d);
    }
    #[cfg(all(target_arch = "x86_64", feature = "avx512"))]
    if let Some(d) = jxl_simd::Avx512Descriptor::new() {
        check(d);
    }
    #[cfg(all(target_arch = "aarch64", feature = "neon"))]
    if let Some(d) = jxl_simd::NeonDescriptor::new() {
        check(d);
    }
    #[cfg(all(target_arch = "wasm32", feature = "simd128"))]
    if let Some(d) = jxl_simd::Simd128Descriptor::new() {
        check(d);
    }
}

fn hlg_fixture() -> Vec<u8> {
    include_str!("hlg_near_unity_255.jxl.hex")
        .split_whitespace()
        .flat_map(|line| {
            line.as_bytes()
                .chunks_exact(2)
                .map(|x| u8::from_str_radix(std::str::from_utf8(x).unwrap(), 16).unwrap())
        })
        .collect()
}

#[path = "hlg_decode_fixture.rs"]
mod decoded_frames;
#[test]
fn hlg_near_unity_complete_file_matches_native_original_signal() {
    let frames =
        decoded_frames::decode_current_frames(&hlg_fixture(), "HLG 255 nits native fixture");
    assert_eq!(frames.len(), 1);
    assert!(frames[0].1.is_empty());
    let pixels = &frames[0].0;
    assert_eq!(pixels.len(), 9 * 3 * 3);
    let expected = [
        f32::from_bits(0x3dffe91a),
        f32::from_bits(0x3e7ffd50),
        f32::from_bits(0x3efff7a5),
    ];
    for (i, &value) in pixels.iter().enumerate() {
        assert!(
            value.is_finite() && (value - expected[i % 3]).abs() <= 0.0001,
            "complete native HLG sample {i}: {value} vs {}",
            expected[i % 3]
        );
    }
}
