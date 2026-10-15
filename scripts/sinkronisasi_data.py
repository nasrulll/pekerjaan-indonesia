#!/usr/bin/env python3
"""Perbarui data Git dari paket lokal terpercaya, diverifikasi checksum dan skema.

Tidak mengunduh publikasi pemerintah otomatis, tidak menetapkan status 'resmi'
secara otomatis, tidak menyentuh dataset kecuali --terapkan. Review manusia tetap wajib.
"""
import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from validate import ROOT, check

# Allowlist: file path is never accepted from manifest blindly.
DATA_FILES = ('occupations.csv','job_titles.csv','kbji_mappings.csv','jabatan_nasional.csv',
              'wilayah_administratif.csv','pemetaan_jabatan_kbji.csv','kompetensi_jabatan.csv',
              'upah_minimum.csv','statistik_upah.csv','kelas_gaji.csv','pemetaan_internasional.csv',
              'sources.csv','reference/sectors.csv','reference/employment_contexts.csv',
              'reference/kbji_major_groups.csv')

def periksa_paket(paket: Path):
    manifest_path=paket/'manifest-sumber.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    if not isinstance(manifest.get('berkas'),dict) or not manifest.get('asal_sumber') or not manifest.get('versi'):
        raise ValueError('Manifest memerlukan berkas, asal_sumber, dan versi')
    if not manifest['berkas']:
        raise ValueError('Paket tidak boleh kosong')
    for nama, digest in manifest['berkas'].items():
        if nama not in DATA_FILES: raise ValueError('Berkas tidak termasuk daftar izin: '+nama)
        if not isinstance(digest,str) or len(digest)!=64: raise ValueError('Checksum bukan SHA-256')
        path=paket/nama
        if not path.is_file() or path.is_symlink(): raise ValueError('Berkas sumber tidak ada/bukan file biasa')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError('Checksum tidak sesuai: '+nama)
    return manifest

def siapkan(paket: Path, *, terapkan=False, root=ROOT):
    manifest=periksa_paket(paket)
    with tempfile.TemporaryDirectory(prefix='rpi-validasi-') as tempat:
        calon=Path(tempat)/'calon'
        shutil.copytree(root/'data',calon/'data')
        for nama in manifest['berkas']:
            shutil.copyfile(paket/nama,calon/'data'/nama)
        problems,counts=check(calon)
        if problems: raise ValueError('Paket gagal validasi: '+'; '.join(problems[:15]))
        if terapkan:
            # Each replacement atomic at file level. Git review/commit remains responsibility
            # of operator; no implicit merge or deleting data. Restore from Git if interrupted.
            for nama in manifest['berkas']:
                dst=root/'data'/nama
                with tempfile.NamedTemporaryFile(dir=dst.parent, prefix='.rpi-', delete=False) as stream:
                    sementara=Path(stream.name)
                    stream.write((paket/nama).read_bytes())
                sementara.replace(dst)
        return {'modus':'diterapkan' if terapkan else 'simulasi',
                'berkas':list(manifest['berkas']), 'versi_paket':manifest['versi'],
                'asal_sumber':manifest['asal_sumber'],'jumlah':counts,
                'catatan':'Pemeriksaan format otomatis bukan bukti keabsahan substantif/salin ulang.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('paket',type=Path)
    p.add_argument('--terapkan',action='store_true')
    a=p.parse_args()
    print(json.dumps(siapkan(a.paket,terapkan=a.terapkan),ensure_ascii=False,indent=2))
