#!/usr/bin/env python3
"""Retain native alpha edge controls and complete-plane primary comparisons."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('cjxl', type=Path)
p.add_argument('djxl', type=Path)
p.add_argument('replay', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--transpose', action='store_true')
p.add_argument('--require-exact', action='store_true')
a = p.parse_args()
a.output.mkdir(exist_ok=False)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
versions = []
for name in ['cjxl', 'djxl']:
    path = getattr(a, name)
    result = subprocess.run([str(path), '--version'], capture_output=True)
    text = (result.stdout + result.stderr).decode()
    (a.output / (name + '-version.log')).write_text(text)
    assert result.returncode == 0 and 'v0.12.0 a7a9c78' in text
    versions.append(dict(tool=name, path=str(path), sha256=sha(path), version=text))
identity = dict(native_tools=versions, replay_sha256=sha(a.replay), transposed=a.transpose)
(a.output / 'identity.json').write_text(json.dumps(identity, indent=2) + '\n')
rows = []
cases = [(2049, 2048, window) for window in [0, 256, 64, 16, 8, 4, 1]]
cases += [(2049, 257, 4), (2049, 259, 4), (2049, 1025, 4)]
cases += [(257, 256, 0), (257, 256, 16), (129, 128, 0), (17, 16, 0), (9, 8, 0)]
for width, height, window in cases:
    if a.transpose: width, height = height, width
    out = a.output / f'{width}x{height}-window{window}'
    out.mkdir()
    source = out / 'input.pam'
    with source.open('xb') as file:
        file.write(f'P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n'.encode())
        for y in range(height):
            row = bytearray()
            for x in range(width):
                alpha = ((y * 17 + x * 29) if a.transpose else (x * 17 + y * 29)) % 256 if window == 0 or (x >= width - window and y >= height - window) else 0
                row.extend([64, 128, 192, alpha])
            file.write(row)
    commands = [[str(a.cjxl), str(source), str(out / 'native.jxl'), '-d', '1', '-e', '3', '--responsive=1', '--num_threads=1', '--alpha_distance=25'], [str(a.djxl), str(out / 'native.jxl'), str(out / 'native.pfm'), '--output_extra_channels', '--num_threads=1']]
    for i, command in enumerate(commands):
        with (out / f'native-{i}.log').open('xb') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    command = [str(a.replay), str(out / 'native.jxl'), str(out / 'native.pfm-ec1.pfm'), str(out / 'primary')]
    with (out / 'primary.log').open('xb') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    summary_path = out / 'primary/summary.txt'
    assert summary_path.is_file(), 'decoder did not complete the comparison; inspect primary.log'
    summary = dict(line.split('=') for line in summary_path.read_text().splitlines())
    count = int(summary['mismatches'])
    assert (result.returncode == 0) == (count == 0)
    row = dict(width=width, height=height, window=window, source_sha256=sha(source), stream_sha256=sha(out / 'native.jxl'), stream_bytes=(out / 'native.jxl').stat().st_size, mismatches=count, exit_code=result.returncode)
    rows.append(row)
    (a.output / 'results.partial.json').write_text(json.dumps(rows, indent=2) + '\n')
    print(json.dumps(row), flush=True)
(a.output / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')

if a.require_exact:
    assert all(row['mismatches'] == 0 for row in rows), 'retained native alpha differences'
