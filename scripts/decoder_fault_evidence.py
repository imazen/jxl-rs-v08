#!/usr/bin/env python3
"""Restore one historical decoder fault and require its retained regression failure."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('fault',choices=['hlg','global-squeeze']);p.add_argument('output',type=Path)
a=p.parse_args();a.output.mkdir(exist_ok=False);root=Path(__file__).resolve().parent.parent
if a.fault=='hlg':
 relative='jxl/src/color/tf.rs';source=(root/relative).read_text()
 old='''exp
        .abs()
        .gt(D::F32Vec::splat(d, 0.01))
        .if_then_else_f32(mult, D::F32Vec::splat(d, 1.0))'''
 assert old in source
 fault=source.replace(old,'D::F32Vec::splat(d, 0.1).gt(exp.abs()).if_then_else_f32(D::F32Vec::splat(d, 1.0), mult)')
 script='hlg_ootf_evidence.py';diagnostics=['complete native HLG','native HLG row']
else:
 relative='jxl/src/frame/modular/transforms/meta_apply.rs';source=(root/relative).read_text()
 begin=source.index('                // Grid placement belongs to the coded input channels.')
 end=source.index('            }',begin)
 fault=source[:begin]+'                let mut grid_kind = buffer_info[buf_in[0]]\n                    .grid_kind\n                    .max(buffer_info[buf_in[1]].grid_kind);\n                if grid_kind == ModularGridKind::None\n                    && !buffer_info[*buf_out].info.is_meta_or_small(frame_header.group_dim())\n                {\n                    grid_kind = ModularGridKind::Hf;\n                }\n                buffer_info[*buf_out].grid_kind = grid_kind;\n'+source[end:]
 script='global_squeeze_evidence.py';diagnostics=['assertion failed: row < self.num_rows']
path=root/relative
(a.output/'fixed.rs').write_text(source);(a.output/'fault.rs').write_text(fault)
try:
 path.write_text(fault)
 subprocess.run([sys.executable,str(root/'scripts'/script),str(root/'Cargo.toml'),str(a.output/'runtime'),'--package','jxl','--expect-failure'],check=True)
 text=(a.output/'runtime/test.log').read_text()
 for expected in diagnostics:assert expected in text,expected
finally:
 path.write_text(source);assert path.read_text()==source
 (a.output/'restored.json').write_text(json.dumps(dict(restored=True,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))+'\n')
(a.output/'verdict.json').write_text(json.dumps(dict(exit_code=0,restored=True))+'\n')
