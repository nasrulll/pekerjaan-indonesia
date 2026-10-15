#!/usr/bin/env python3
"""Impor CSV tervalidasi dan upsert transaksional, tanpa hapus, lintas enam mesin SQL.

Dry-run adalah default; gunakan --terapkan. --buat-skema hanya untuk DB BARU.
Untuk database eksisting jalankan migrasi yang sudah direview secara terpisah.
"""
import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from sqlalchemy import select, insert, update, inspect, event

from validate import ROOT, check, read_csv
from catalog_tables import COLUMNS
from load_postgres import TABLES
sys.path.insert(0, str(ROOT))
from nor_id.basis_data import buat_mesin, periksa_url
from nor_id.skema_portabel import metadata

HANYA_TANGGAL = {'last_reviewed','verified_at','tanggal_verifikasi','tanggal_mulai'}
HANYA_ANGKA = {'tahun','nilai_rupiah','jumlah_sampel','nilai_dasar_rupiah'}


def normalkan(nama, row):
    normalized = {}
    for kolom in COLUMNS[nama]:
        nilai = row[kolom]
        if nilai == '':
            normalized[kolom] = '' if kolom in ('alternative_names', 'notes') and nama in ('occupations','job_titles') else None
        elif kolom in HANYA_TANGGAL:
            normalized[kolom] = date.fromisoformat(nilai)
        elif kolom in HANYA_ANGKA:
            normalized[kolom] = int(nilai)
        else:
            normalized[kolom] = nilai
    return normalized


def impor(conn, root=ROOT):
    """Atomic import; caller starts transaction. Preserves unknown existing rows."""
    laporan = {}
    for nama, berkas, pks in TABLES:
        tabel = metadata.tables[nama]
        fields = pks.split(',')
        daftar = [normalkan(nama, r) for r in read_csv(root/'data'/berkas)]
        if nama in ('jabatan_nasional', 'wilayah_administratif'):
            # Foreign keys refer to their parent inside the same table.
            # Sort parents before children, independent of incoming CSV row order.
            key = (lambda r: r['id_jabatan']) if nama == 'jabatan_nasional' else (lambda r: (r['sistem_kode'], r['kode_wilayah']))
            parent = (lambda r: r['id_jabatan_induk']) if nama == 'jabatan_nasional' else (lambda r: (r['sistem_kode'],r['kode_induk']) if r['kode_induk'] else None)
            pending = {key(r):r for r in daftar}
            ordered = []
            while pending:
                ready = [k for k,r in pending.items() if not parent(r) or parent(r) not in pending]
                if not ready:
                    raise ValueError(f'Hierarki {nama} berputar atau tidak terurut')
                for k in ready:
                    ordered.append(pending.pop(k))
            daftar = ordered
        for item in daftar:
            kunci = [tabel.c[c] == item[c] for c in fields]
            sudah = conn.execute(select(tabel.c[fields[0]]).where(*kunci).limit(1)).first()
            if sudah:
                conn.execute(update(tabel).where(*kunci).values(**{c:v for c,v in item.items() if c not in fields}))
            else:
                conn.execute(insert(tabel).values(**item))
        laporan[nama] = len(daftar)
    alias_tabel = metadata.tables['occupation_aliases']
    for record in read_csv(root/'data/occupations.csv'):
        for alias in record['alternative_names'].split('|'):
            alias = alias.strip()
            if not alias:
                continue
            clause = (alias_tabel.c.occupation_id == record['occupation_id']) & (alias_tabel.c.alternative_name_id == alias)
            if not conn.execute(select(alias_tabel.c.alias_id).where(clause)).first():
                conn.execute(insert(alias_tabel).values(occupation_id=record['occupation_id'],alternative_name_id=alias))
    ext = metadata.tables['pemetaan_internasional']
    for record in read_csv(root/'data/pemetaan_internasional.csv'):
        row = dict(record)
        row['tanggal_verifikasi'] = date.fromisoformat(row['tanggal_verifikasi'])
        if not conn.execute(select(ext.c.id_pemetaan).where(ext.c.id_pemetaan == row['id_pemetaan'])).first():
            conn.execute(insert(ext).values(**row))
    laporan['pemetaan_internasional'] = len(read_csv(root/'data/pemetaan_internasional.csv'))
    return laporan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terapkan',action='store_true',help='Konfirmasi perubahan data')
    parser.add_argument('--buat-skema',action='store_true',help='Hanya untuk database baru/kosong')
    parser.add_argument('--url',help='URL database, atau RPI_DATABASE_URL')
    args = parser.parse_args()
    errors, counts = check(ROOT)
    if errors: parser.error('Dataset tidak valid:\n'+'\n'.join(errors))
    if not args.terapkan:
        print(json.dumps({'modus':'simulasi','jumlah':counts,'pesan':'Tidak menyentuh basis data. Tambahkan --terapkan.'},ensure_ascii=False))
        return
    url = args.url or os.getenv('RPI_DATABASE_URL')
    if not url: parser.error('--url atau RPI_DATABASE_URL wajib untuk penerapan')
    alamat = periksa_url(url,periksa_berkas=not args.buat_skema)
    mesin = buat_mesin(url,periksa_berkas=not args.buat_skema)
    try:
        with mesin.begin() as koneksi:
            if args.buat_skema:
                if inspect(koneksi).get_table_names():
                    raise RuntimeError('--buat-skema hanya untuk basis data kosong; jangan migrasi otomatis.')
                metadata.create_all(koneksi)
            else:
                existing = set(inspect(koneksi).get_table_names())
                missing = set(metadata.tables)-existing
                if missing:
                    raise RuntimeError('Migrasi diperlukan sebelum impor: '+', '.join(sorted(missing)))
            print(json.dumps({'modus':'diterapkan','jenis_database':alamat.get_backend_name(),
                              'jumlah':impor(koneksi)},ensure_ascii=False))
    finally:
        mesin.dispose()

if __name__ == '__main__': main()
