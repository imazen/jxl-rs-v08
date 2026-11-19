#!/usr/bin/env python3
"""Freeze small native streams and complete decoded alpha codes as text."""
import argparse
import array
import hashlib
import json
from pathlib import Path
import struct
import sys
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('horizontal',type=Path);p.add_argument('vertical',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();a.output.mkdir(exist_ok=False);rows=[]
for name,cell in [('horizontal',a.horizontal),('vertical',a.vertical)]:
 data=(cell/'native.jxl').read_bytes();hextext='\n'.join(data.hex()[i:i+96]for i in range(0,len(data)*2,96))+'\n'
 with (cell/'native.pfm-ec1.pfm').open('rb')as file:
  assert file.readline().strip()==b'Pf';width,height=map(int,file.readline().split());scale=float(file.readline());assert abs(scale)==1
  samples=array.array('f');samples.frombytes(file.read());assert len(samples)==width*height
 if (scale>0)==(sys.byteorder=='little'):samples.byteswap()
 runs=[];last=None;count=0
 for y in range(height-1,-1,-1):
  for value in samples[y*width:(y+1)*width]:
   code=round(value*255.0);assert -32768<=code<=32767 and abs(value*255-code)<0.001
   if code!=last and last is not None:runs.append((count,last));count=0
   count+=1;last=code
 runs.append((count,last));assert sum(n for n,_ in runs)==width*height
 rle=f'{width}\t{height}\n'+''.join(f'{count}\t{code}\n'for count,code in runs)
 for suffix,text in [('jxl.hex',hextext),('alpha.rle',rle)]:
  path=a.output/f'squeeze_border_{name}.{suffix}';path.write_text(text)
  assert path.stat().st_size<30000, 'keep larger generated data outside git'
 rows.append(dict(name=name,width=width,height=height,stream_sha256=hashlib.sha256(data).hexdigest(),stream_bytes=len(data),rle_runs=len(runs),text_bytes=len(hextext)+len(rle),native_plane_sha256=hashlib.sha256((cell/'native.pfm-ec1.pfm').read_bytes()).hexdigest()))
(a.output/'provenance.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
