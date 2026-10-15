#!/usr/bin/env python3
"""Hasilkan DDL untuk review DBA tanpa membuka koneksi DB."""
import argparse
from pathlib import Path
from sqlalchemy.dialects import postgresql, mysql, mssql, oracle, sqlite
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sqlalchemy.schema import CreateTable, CreateIndex
from nor_id.skema_portabel import metadata

DIALEK={'postgresql':postgresql.dialect,'mysql':mysql.dialect,
        'mariadb':__import__('sqlalchemy.dialects.mysql.mariadb',fromlist=['MariaDBDialect']).MariaDBDialect,
        'mssql':mssql.dialect,'oracle':oracle.dialect,'sqlite':sqlite.dialect}

def ddl(jenis):
    d=DIALEK[jenis]()
    awal=(f'-- RPI 0.4 skema baru {jenis}. Pratinjau DBA; BUKAN migrasi database existing.\n'
          '-- Periksa tipe data, koneksi, batas indeks, dan foreign key sebelum produksi.\n\n')
    tables='\n\n'.join(str(CreateTable(t).compile(dialect=d))+';' for t in metadata.sorted_tables)
    indexes='\n'.join(str(CreateIndex(i).compile(dialect=d))+';' for t in metadata.tables.values() for i in t.indexes)
    return awal+tables+'\n\n'+indexes+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dialek',choices=sorted(DIALEK),required=True)
    p.add_argument('--output',type=Path);args=p.parse_args()
    result=ddl(args.dialek)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(result,encoding='utf-8')
    else: print(result)
