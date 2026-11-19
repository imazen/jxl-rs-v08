// Copyright (c) Imazen LLC.
// Use of this source code is governed by a BSD-style license in LICENSE.
//! Native complete-plane controls and packed next-average border views.
use super::*;
use crate::api::{JxlColorType, JxlDataFormat, JxlPixelFormat};
use crate::tests::decode::{DecodeParams, decode};
use crate::util::sync::RwLock;

fn run(check: fn()) {
    #[cfg(feature = "shuttle")]
    {
        let mut config = shuttle::Config::default();
        // Match the existing full-stream decoder harness's scheduler budget.
        config.max_steps = shuttle::MaxSteps::FailAfter(10_000_000);
        shuttle::Runner::new(shuttle::scheduler::RandomScheduler::new(1), config).run(check);
    }
    #[cfg(not(feature = "shuttle"))]
    check();
}

fn packed<T: ImageDataType>(storage: ModularStorage) {
    for vertical in [false, true] {
        for offset in [0, 3, 7] {
            for extent in [1, 3, 8] {
                let (width, height) = if vertical { (16, 4) } else { (4, 16) };
                let mut image = Image::<T>::new((width, height)).unwrap();
                for y in 0..height {
                    for x in 0..width {
                        image.row_mut(y)[x] = T::from_f64((100 * y + x) as f64);
                    }
                }
                let average = if vertical {
                    Rect {
                        origin: (offset, 11),
                        size: (extent, 2),
                    }
                } else {
                    Rect {
                        origin: (11, offset),
                        size: (2, extent),
                    }
                };
                let avg = RwLock::<Option<ModularChannel>>::new(None);
                let res = RwLock::<Option<ModularChannel>>::new(None);
                let border = RwLock::new(Some(image.into_raw()));
                let inputs = SqueezeInputs {
                    in_avg: avg.try_read().unwrap(),
                    in_res: res.try_read().unwrap(),
                    in_next_border: Some(border.try_read().unwrap()),
                    out_prev_border: None,
                };
                let actual = inputs.in_next_border(average, storage, vertical).unwrap();
                let actual = ImageRect::<T>::from_raw(actual);
                assert_eq!(
                    actual.size(),
                    if vertical { (extent, 4) } else { (4, extent) }
                );
                for y in 0..actual.size().1 {
                    for (x, sample) in actual.row(y).iter().enumerate() {
                        let expected = if vertical {
                            100 * y + x + offset
                        } else {
                            100 * (y + offset) + x
                        };
                        assert_eq!(
                            sample.to_f64(),
                            expected as f64,
                            "offset={offset}, extent={extent}, vertical={vertical}"
                        );
                    }
                }
            }
        }
    }
}

#[test]
fn squeeze_next_average_border_preserves_perpendicular_tile_offset() {
    run(|| {
        packed::<i16>(ModularStorage::I16);
        packed::<i32>(ModularStorage::I32);
    });
}

#[test]
fn squeeze_next_average_absent_border_remains_absent() {
    run(|| {
        let avg = RwLock::<Option<ModularChannel>>::new(None);
        let res = RwLock::<Option<ModularChannel>>::new(None);
        let border = RwLock::<Option<OwnedRawImage>>::new(None);
        for present in [false, true] {
            let inputs = SqueezeInputs {
                in_avg: avg.try_read().unwrap(),
                in_res: res.try_read().unwrap(),
                in_next_border: present.then(|| border.try_read().unwrap()),
                out_prev_border: None,
            };
            assert!(
                inputs
                    .in_next_border(
                        Rect {
                            origin: (0, 0),
                            size: (1, 1)
                        },
                        ModularStorage::I16,
                        false
                    )
                    .is_none()
            );
        }
    });
}

fn fixture(hex: &str, rle: &str) {
    let encoded: Vec<u8> = hex
        .split_whitespace()
        .flat_map(|line| {
            line.as_bytes()
                .chunks_exact(2)
                .map(|pair| u8::from_str_radix(std::str::from_utf8(pair).unwrap(), 16).unwrap())
        })
        .collect();
    let mut lines = rle.lines();
    let dimensions: Vec<usize> = lines
        .next()
        .unwrap()
        .split_whitespace()
        .map(|v| v.parse().unwrap())
        .collect();
    let (width, height) = (dimensions[0], dimensions[1]);
    let expected: Vec<i16> = lines
        .flat_map(|line| {
            let (count, value) = line.split_once('\t').unwrap();
            std::iter::repeat_n(
                value.parse::<i16>().unwrap(),
                count.parse::<usize>().unwrap(),
            )
        })
        .collect();
    assert_eq!(expected.len(), width * height);
    for wide in [false, true] {
        for simple in [false, true] {
            for chunk_size in [usize::MAX, 37] {
                let frames = decode::<f32>(
                    &encoded,
                    DecodeParams {
                        chunk_size,
                        use_simple_pipeline: simple,
                        disable_16bit_modular_buffers: wide,
                        pixel_format: Some(JxlPixelFormat {
                            color_type: JxlColorType::Rgb,
                            color_data_format: Some(JxlDataFormat::f32()),
                            extra_channel_format: vec![Some(JxlDataFormat::f32())],
                        }),
                        ..Default::default()
                    },
                )
                .unwrap();
                assert_eq!(frames.len(), 1);
                assert_eq!(frames[0].len(), 2);
                assert_eq!(frames[0][0].size(), (width * 3, height));
                assert_eq!(frames[0][1].size(), (width, height));
                for y in 0..height {
                    assert!(frames[0][0].row(y).iter().all(|v| v.is_finite()));
                    for (x, sample) in frames[0][1].row(y).iter().enumerate() {
                        assert!(sample.is_finite());
                        assert_eq!(
                            (sample * 255.0).round() as i16,
                            expected[y * width + x],
                            "native alpha ({x},{y}) wide={wide} simple={simple} chunk={chunk_size}"
                        );
                    }
                }
            }
        }
    }
}

#[test]
fn squeeze_next_average_complete_native_horizontal_alpha() {
    run(|| {
        fixture(
            include_str!("squeeze_border_horizontal.jxl.hex"),
            include_str!("squeeze_border_horizontal.alpha.rle"),
        )
    });
}

#[test]
fn squeeze_next_average_complete_native_vertical_alpha() {
    run(|| {
        fixture(
            include_str!("squeeze_border_vertical.jxl.hex"),
            include_str!("squeeze_border_vertical.alpha.rle"),
        )
    });
}
