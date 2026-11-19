#!/usr/bin/env python3
"""Temporarily select wide modular storage for an exact-byte diagnostic replay."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('stream', type=Path)
p.add_argument('native', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
a.output.mkdir(exist_ok=False)
root = Path(__file__).resolve().parent.parent
path = root / 'jxl/src/frame/mod.rs'
source = path.read_bytes()
old = b'if self.file_header.image_metadata.modular_16bit_sufficient {'
assert source.count(old) == 1
wide = source.replace(old, b'if false { // diagnostic: use wide storage for the unchanged stream')
(a.output / 'before.rs').write_bytes(source)
(a.output / 'wide.rs').write_bytes(wide)
rows = []
try:
    path.write_bytes(wide)
    for label, features in [('simd', 'all-simd'), ('scalar', '')]:
        command = [sys.executable, str(root / 'scripts/alpha_plane_replay_evidence.py'), str(a.stream), str(a.native), str(a.output / label), features]
        result = subprocess.run(command, cwd=root)
        rows.append(dict(label=label, command=command, exit_code=result.returncode))
        (a.output / 'results.partial.json').write_text(json.dumps(rows, indent=2) + '\n')
finally:
    path.write_bytes(source)
    assert path.read_bytes() == source
    (a.output / 'restored.json').write_text(json.dumps(dict(restored=True, sha256=hashlib.sha256(source).hexdigest())) + '\n')
(a.output / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
sys.exit(1 if any(row['exit_code'] for row in rows) else 0)
