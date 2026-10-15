#!/usr/bin/env python3
"""Create reproducible local multi-format release assets and checksums."""
import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path

from validate import ROOT, check, read_csv
from build_sqlite import build
from export_json import export


def create_release(root: Path = ROOT, output: Path | None = None) -> dict:
    if output is None:
        output = root / 'dist'
    problems, stats = check(root)
    if problems:
        raise ValueError('\n'.join(problems))
    output.mkdir(parents=True, exist_ok=True)
    sqlite = output/'pekerjaan-indonesia.sqlite3'
    json_file = output/'occupations.json'
    csv_file = output/'occupations.csv'
    build(sqlite, root)
    export(root, json_file)
    sectors = {r['sector_id']: r['sector_name']
               for r in read_csv(root/'data/reference/sectors.csv')}
    with csv_file.open('w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(('occupation_id', 'name', 'aliases', 'sector_id', 'sector_name',
                         'record_status', 'source_id'))
        for r in sorted(read_csv(root/'data/occupations.csv'),
                        key=lambda item: item['occupation_id']):
            writer.writerow((r['occupation_id'], r['preferred_name_id'],
                             r['alternative_names'], r['sector_id'],
                             sectors[r['sector_id']], r['record_status'], r['source_id']))
    # Ekspor tambahan dengan kolom dan berkas berbahasa Indonesia.
    pekerjaan_lokal = [
        {
            'id_pekerjaan':r['occupation_id'],
            'nama_pekerjaan':r['preferred_name_id'],
            'nama_alternatif':r['alternative_names'],
            'id_sektor':r['sector_id'],
            'nama_sektor':sectors[r['sector_id']],
            'status_data':{'draft':'draf','reviewed':'ditinjau','published':'dipublikasikan','archived':'diarsipkan'}[r['record_status']],
            'sumber_id':r['source_id']
        }
        for r in sorted(read_csv(root/'data/occupations.csv'),key=lambda r:r['occupation_id'])
    ]
    keluaran_pekerjaan = (output/'pekerjaan.csv',output/'pekerjaan.json')
    with keluaran_pekerjaan[0].open('w',encoding='utf-8',newline='') as f:
        penulis=csv.DictWriter(f,fieldnames=list(pekerjaan_lokal[0]))
        penulis.writeheader();penulis.writerows(pekerjaan_lokal)
    keluaran_pekerjaan[1].write_text(json.dumps(pekerjaan_lokal,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    tambahan = {}
    for nama in ('jabatan_nasional','wilayah_administratif','upah_minimum',
                 'statistik_upah','kompetensi_jabatan','kelas_gaji','pemetaan_jabatan_kbji','pemetaan_internasional'):
        sumber = root / 'data' / f'{nama}.csv'
        tujuan_csv = output / f'{nama}.csv'
        tujuan_json = output / f'{nama}.json'
        shutil.copyfile(sumber, tujuan_csv)
        tujuan_json.write_text(json.dumps(read_csv(sumber), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        tambahan[nama] = (tujuan_csv, tujuan_json)
    semua_file = (sqlite, json_file, csv_file) + keluaran_pekerjaan + tuple(f for pair in tambahan.values() for f in pair)
    manifest = {
        'version': '0.4.0',
        'catalog_status': 'curated_draft_not_official',
        'counts': stats,
        'files': {
            f.name: {'sha256': hashlib.sha256(f.read_bytes()).hexdigest(),
                     'size_bytes': f.stat().st_size}
            for f in semua_file
        },
        'source_of_truth': 'Git CSV',
        'nama_proyek': 'Registri Pekerjaan Indonesia',
        'catatan_upah': 'Katalog upah belum tersedia hingga sumber terverifikasi diperoleh.',
    }
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
                                         encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    print(json.dumps(create_release(output=args.output), indent=2))
