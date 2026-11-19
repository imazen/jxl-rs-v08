#!/usr/bin/env python3
"""Bind a complete alpha comparison to the exact decoder sources and executable."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('stream', type=Path)
p.add_argument('native', type=Path)
p.add_argument('output', type=Path)
p.add_argument('features')
a = p.parse_args()
a.output.mkdir(exist_ok=False)
root = Path(__file__).resolve().parent.parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
command = ['cargo', 'build', '--locked', '-p', 'jxl', '--example', 'squeeze_alpha_replay', '--no-default-features', '--features', a.features, '--message-format=json']
with (a.output / 'build.jsonl').open('x') as log, (a.output / 'build.log').open('x') as errors:
    subprocess.run(command, cwd=root, stdout=log, stderr=errors, check=True)
rows = [json.loads(line) for line in (a.output / 'build.jsonl').read_text().splitlines()]
executable, = [Path(row['executable']) for row in rows if row.get('reason') == 'compiler-artifact' and row.get('target', {}).get('name') == 'squeeze_alpha_replay' and row.get('executable')]
shutil.copy2(executable, a.output / 'replay-binary')
assert sha(executable) == sha(a.output / 'replay-binary')
sources = []
for path in sorted(root.rglob('*.rs')):
    if any(part in ['.git', '.jj', 'target'] for part in path.relative_to(root).parts):
        continue
    sources.append(dict(path=str(path.relative_to(root)), sha256=sha(path)))
for relative in ['Cargo.lock', 'Cargo.toml', 'jxl/Cargo.toml']:
    sources.append(dict(path=relative, sha256=sha(root / relative)))
identity = dict(build_command=command, source_parent=subprocess.check_output(['jj', 'log', '-r', '@-', '--no-graph', '-T', 'commit_id'], cwd=root, text=True), sources=sources, binary_sha256=sha(executable), stream_sha256=sha(a.stream), native_sha256=sha(a.native), features=a.features)
with (a.output / 'test.log').open('x') as log:
    child = subprocess.Popen([str(executable), str(a.stream), str(a.native), str(a.output / 'runtime')], cwd=root, stdout=log, stderr=subprocess.STDOUT)
    identity['pid'] = child.pid
    (a.output / 'identity.json').write_text(json.dumps(identity, indent=2) + '\n')
    code = child.wait()
identity['exit_code'] = code
identity['runtime_completed'] = (a.output / 'runtime/summary.txt').is_file()
(a.output / 'identity.json').write_text(json.dumps(identity, indent=2) + '\n')
print(json.dumps(dict(exit_code=code, runtime_completed=identity['runtime_completed'], binary_sha256=identity['binary_sha256'])))
sys.exit(code)
