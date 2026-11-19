#!/usr/bin/env python3
"""Restore a perpendicular border-offset fault and require completed runtime failure."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('direction',choices=['horizontal','vertical']);p.add_argument('output',type=Path)
a=p.parse_args();a.output.mkdir(exist_ok=False);root=Path(__file__).resolve().parent.parent
path=root/'jxl/src/frame/modular/transforms/step.rs';source=path.read_bytes()
old=b'origin: (0, average.origin.1),' if a.direction=='horizontal' else b'origin: (average.origin.0, 0),'
assert source.count(old)==1;fault=source.replace(old,b'origin: (0, 0),')
(a.output/'fixed.rs').write_bytes(source);(a.output/'fault.rs').write_bytes(fault)
try:
 path.write_bytes(fault)
 subprocess.run([sys.executable,str(root/'scripts/hlg_ootf_evidence.py'),str(root/'Cargo.toml'),str(a.output/'runtime'),'--package','jxl','--filter','squeeze_next_average_','--expect-failure'],check=True)
 text=(a.output/'runtime/test.log').read_text();assert 'native alpha (' in text and 'perpendicular_tile_offset' in text and 'FAILED' in text
finally:
 path.write_bytes(source);assert path.read_bytes()==source
 (a.output/'restored.json').write_text(json.dumps(dict(restored=True,sha256=hashlib.sha256(source).hexdigest()))+'\n')
(a.output/'verdict.json').write_text(json.dumps(dict(actual_exit_code=json.loads((a.output/'runtime/identity.json').read_text())['exit_code'],restored=True))+'\n')
