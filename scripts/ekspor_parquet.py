#!/usr/bin/env python3
"""Ekspor analitik opsional ke Parquet; butuh pip install -e '.[analitik]'."""
import argparse
from pathlib import Path
from validate import ROOT, check, read_csv
from build_release import create_release

DAFTAR = ('occupations','jabatan_nasional','wilayah_administratif','upah_minimum',
          'statistik_upah','pemetaan_jabatan_kbji','pemetaan_internasional')

def ekspor(output:Path, root=ROOT):
    errors,counts=check(root)
    if errors: raise ValueError('\n'.join(errors))
    try: import pyarrow as pa; import pyarrow.parquet as pq
    except ImportError as ex: raise RuntimeError("Install pyarrow: pip install -e '.[analitik]'") from ex
    output.mkdir(parents=True,exist_ok=True)
    files=[]
    for dataset in DAFTAR:
        rows=read_csv(root/'data'/f'{dataset}.csv')
        # Explicit schema for empty tables avoids fabricated records.
        if rows:
            table=pa.Table.from_pylist(rows)
        else:
            import csv
            with (root/'data'/f'{dataset}.csv').open(newline='',encoding='utf-8') as h:
                columns=next(csv.reader(h))
            table=pa.table({k:pa.array([],type=pa.string()) for k in columns})
        filename=output/f'{dataset}.parquet'
        pq.write_table(table,filename,compression='zstd')
        files.append(filename.name)
    return {'jumlah_dataset':len(files),'berkas':files,'peringatan':'Tipe dari CSV masih berupa string: konversi eksplisit sebelum agregasi numerik.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'dist/parquet');a=p.parse_args()
    print(ekspor(a.output))
