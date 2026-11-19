#!/usr/bin/env python3
# Copyright (c) Imazen LLC.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""Retain an HLG regression executable, complete source identity and actual verdict."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('manifest', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--package', choices=['zenjxl-decoder','jxl'], default='zenjxl-decoder')
p.add_argument('--no-default-features', action='store_true')
p.add_argument('--expect-failure', action='store_true')
p.add_argument('--filter', default='hlg_near_unity_', help='explicit libtest selection; default keeps the HLG controls')
a = p.parse_args()
root = a.manifest.resolve().parent
a.output.mkdir(exist_ok=False)
# Build scripts may be instrumented too; keep their profiles in the archive.
os.environ['LLVM_PROFILE_FILE'] = str(a.output / 'build-%p-%m.profraw')
os.utime(root / a.package / 'src/lib.rs', None)
command = ['cargo', 'test', '--locked', '--manifest-path', str(a.manifest),
           '-p', a.package, '--lib', '--no-run', '--message-format=json']
if a.no_default_features: command.append('--no-default-features')
with (a.output / 'build.jsonl').open('x') as log:
    subprocess.run(command, stdout=log, check=True)
artifacts = [json.loads(line) for line in (a.output / 'build.jsonl').read_text().splitlines()]
executables = [row['executable'] for row in artifacts if row.get('reason') == 'compiler-artifact'
               and row.get('target', {}).get('name') == a.package.replace('-', '_') and row.get('executable')]
assert len(executables) == 1
binary = Path(executables[0])
shutil.copy2(binary, a.output / 'test-binary')
def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()
sources = sorted({*root.glob('*/src/**/*.rs'), *root.glob('*/Cargo.toml'),
                  root / 'Cargo.toml', root / 'Cargo.lock',
                  *root.glob('*/src/color/hlg_ootf_v012.tsv'),
                  *root.glob('*/src/color/hlg_near_unity_255.jxl.hex'),
                  *root.glob('*/src/color/hlg_native_fixture.json'),
                  *root.glob('*/src/frame/modular/transforms/squeeze_border_*.jxl.hex'),
                  *root.glob('*/src/frame/modular/transforms/squeeze_border_*.alpha.rle')})
rows = []
for source in sources:
    target = a.output / 'source' / source.relative_to(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    rows.append(dict(path=str(source.relative_to(root)), sha256=digest(target)))
run_command = [str(binary), a.filter, '--nocapture', '--test-threads=1']
listed=subprocess.check_output([str(binary),a.filter,'--list'],text=True,env=dict(os.environ,LLVM_PROFILE_FILE=str(a.output/'probe.profraw')))
assert re.search(r'[1-9][0-9]* tests?',listed),listed
profile=a.output/'test.profraw'
env=dict(os.environ,LLVM_PROFILE_FILE=str(profile),CARGO_MANIFEST_DIR=str(root/a.package))
identity = dict(build_command=command, run_command=run_command,
                rustc=subprocess.check_output(['rustc', '-vV'], text=True),
                binary_sha256=digest(binary), sources=rows, exit_code=None, pid=None)
record = a.output / 'identity.json'
record.write_text(json.dumps(identity, indent=2))
with (a.output / 'test.log').open('x') as log:
    child = subprocess.Popen(run_command, stdout=log, stderr=subprocess.STDOUT, env=env)
    identity['pid'] = child.pid
    record.write_text(json.dumps(identity, indent=2))
    result = child.wait()
assert digest(binary) == identity['binary_sha256']
for row in rows:
    assert digest(root / row['path']) == row['sha256'], row['path']
identity['exit_code'] = result
identity['profile_sha256'] = digest(profile) if profile.exists() else None
identity['expected_exit_code'] = 101 if a.expect_failure else 0
identity['executed_tests'] = sum(int(passed)+int(failed) for passed,failed in re.findall(r'test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed;', (a.output / 'test.log').read_text()))
assert result != 0 or identity['executed_tests'] > 0, 'zero-test run is not evidence'
record.write_text(json.dumps(identity, indent=2))
label = 'HLG regression' if a.filter == 'hlg_near_unity_' else 'Decoder regression ' + a.filter
print(f'{label}: actual rc={result}, expected {identity["expected_exit_code"]}; exact ELF {identity["binary_sha256"]}', flush=True)
assert result == identity['expected_exit_code'], 'unexpected decoder verdict'
sys.exit(0)
