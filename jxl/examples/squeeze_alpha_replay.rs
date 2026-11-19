// Copyright (c) Imazen LLC.
// Use of this source code is governed by a BSD-style license in LICENSE.
//! Compare a complete caller-selected alpha plane against retained native PFM.
use jxl::api::{
    Event, JxlDataFormat, JxlDecoder, JxlDecoderOptions, JxlOutputBuffer, JxlPixelFormat,
};
use jxl::image::{Image, Rect};
use std::io::{BufRead, Read, Write};

fn main() {
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    assert_eq!(
        args.len(),
        3,
        "stream.jxl native-alpha.pfm new-output-directory"
    );
    let out = std::path::Path::new(&args[2]);
    std::fs::create_dir(out).unwrap();
    let bytes = std::fs::read(&args[0]).unwrap();
    let mut native = std::io::BufReader::new(std::fs::File::open(&args[1]).unwrap());
    let mut line = String::new();
    native.read_line(&mut line).unwrap();
    assert_eq!(line.trim(), "Pf");
    line.clear();
    native.read_line(&mut line).unwrap();
    let shape: Vec<usize> = line
        .split_whitespace()
        .map(|v| v.parse().unwrap())
        .collect();
    assert_eq!(shape.len(), 2);
    let (width, height) = (shape[0], shape[1]);
    line.clear();
    native.read_line(&mut line).unwrap();
    let scale: f32 = line.trim().parse().unwrap();
    assert_eq!(scale.abs(), 1.0);
    let mut native_bytes = Vec::new();
    native.read_to_end(&mut native_bytes).unwrap();
    assert_eq!(native_bytes.len(), width * height * 4);
    let mut decoder = JxlDecoder::new(JxlDecoderOptions::default());
    let mut input = bytes.as_slice();
    let mut color: Option<Image<f32>> = None;
    let mut alpha: Option<Image<f32>> = None;
    let mut frames = 0;
    let mut mismatches = 0;
    let mut journal = std::fs::File::create(out.join("differences.tsv")).unwrap();
    writeln!(journal, "x\ty\tprimary\tnative\tprimary_code\tnative_code").unwrap();
    loop {
        let mut output = color.as_mut().zip(alpha.as_mut()).map(|(color, alpha)| {
            [color, alpha]
                .into_iter()
                .map(|image| {
                    let size = image.size();
                    JxlOutputBuffer::from_image_rect_mut(
                        image
                            .get_rect_mut(Rect {
                                origin: (0, 0),
                                size,
                            })
                            .into_raw(),
                    )
                })
                .collect::<Vec<_>>()
        });
        let event = decoder
            .process(&mut input, output.as_deref_mut(), None)
            .unwrap();
        drop(output);
        match event {
            Event::BasicInfo => {
                assert_eq!(decoder.basic_info().unwrap().size, (width, height));
                let format = decoder.current_pixel_format().unwrap().clone();
                assert_eq!(format.extra_channel_format.len(), 1);
                let channels = format.color_type.samples_per_pixel();
                decoder
                    .set_pixel_format(JxlPixelFormat {
                        color_type: format.color_type,
                        color_data_format: Some(JxlDataFormat::f32()),
                        extra_channel_format: vec![Some(JxlDataFormat::f32())],
                    })
                    .unwrap();
                color = Some(Image::new((width * channels, height)).unwrap());
                alpha = Some(Image::new((width, height)).unwrap());
            }
            Event::FrameHeader => {}
            Event::FrameComplete { .. } => {
                frames += 1;
                let alpha = alpha.as_ref().unwrap();
                let mut raw = std::fs::File::create(out.join("primary-alpha.f32le")).unwrap();
                for y in 0..height {
                    for (x, &actual) in alpha.row(y).iter().enumerate() {
                        let offset = ((height - 1 - y) * width + x) * 4;
                        let word = native_bytes[offset..offset + 4].try_into().unwrap();
                        let expected = if scale > 0.0 {
                            f32::from_be_bytes(word)
                        } else {
                            f32::from_le_bytes(word)
                        };
                        assert!(actual.is_finite() && expected.is_finite());
                        raw.write_all(&actual.to_le_bytes()).unwrap();
                        let a = (actual * 255.0).round() as i64;
                        let b = (expected * 255.0).round() as i64;
                        if a != b {
                            mismatches += 1;
                            writeln!(journal, "{x}\t{y}\t{actual:?}\t{expected:?}\t{a}\t{b}")
                                .unwrap();
                        }
                    }
                }
            }
            Event::Complete => break,
            Event::NeedMoreInput { .. } => assert!(!input.is_empty(), "truncated stream"),
        }
    }
    journal.flush().unwrap();
    assert_eq!(frames, 1);
    std::fs::write(
        out.join("summary.txt"),
        format!("width={width}\nheight={height}\nmismatches={mismatches}\n"),
    )
    .unwrap();
    assert_eq!(
        mismatches, 0,
        "complete alpha plane; retained differences.tsv"
    );
}
